"""
Cliente WhatsApp via Neonize.
Gerencia conexão, eventos, reconexão e ciclo de vida do bot.
"""

import asyncio
import gc
from pathlib import Path

from neonize.client import NewClient
from neonize.events import ConnectedEv, MessageEv, HistorySyncEv, CallOfferEv
import sqlite3
import json
import time
import logging
from neonize.utils import log as neonize_logger
import sys
import re
import threading
import os
import socket

from src.utils.logger import logger
from src.config.constants import AUTH_DIR, DATA_DIR, RECONNECT_DELAY, PORT, API_KEY
from src.services.whatsapp import storage

# ── Estado global ──────────────────────────────────────
client: NewClient | None = None
is_ready = False
current_qr: str | None = None
current_pair_code: str | None = None
reaction_cache: dict = {}
START_TIME = time.time()
main_loop: asyncio.AbstractEventLoop | None = None

DB_CONFIG_FILE = Path(DATA_DIR) / "db_config.json"
DEFAULT_INTERVAL = 1440
last_cleanup_time = 0
current_interval = DEFAULT_INTERVAL

MAX_REACTIONS_IN_CACHE = 1000
cleanup_lock = threading.Lock()


# ══════════════════════════════════════════════════════════
# GETTERS / SETTERS
# ══════════════════════════════════════════════════════════

def get_sock():
    return client


def get_is_ready():
    return is_ready


def get_qr():
    return current_qr


def get_pair_code():
    return current_pair_code


def reset_pair_code():
    global current_pair_code
    current_pair_code = None


def get_store():
    return None  # Depreciado para economizar RAM


def get_reaction_cache():
    return reaction_cache


def set_cleanup_interval(interval_minutes: int):
    """Define o intervalo de limpeza do banco SQLite (em minutos)."""
    global current_interval
    current_interval = interval_minutes
    save_db_config()
    logger.info(f"⚙️ Intervalo de limpeza atualizado para {interval_minutes} minutos via setter")


def get_cleanup_state():
    """Retorna estado atual do cleanup (para diagnóstico)."""
    return {
        "last_cleanup_time": last_cleanup_time,
        "current_interval": current_interval,
    }


# ══════════════════════════════════════════════════════════
# GERENCIAMENTO DO BANCO SQLITE
# ══════════════════════════════════════════════════════════

def load_db_config():
    global current_interval, last_cleanup_time
    try:
        if DB_CONFIG_FILE.exists():
            with open(DB_CONFIG_FILE, "r") as f:
                config = json.load(f)
                current_interval = config.get("interval", DEFAULT_INTERVAL)
                last_cleanup_time = config.get("last_run", 0)
    except Exception as e:
        logger.error(f"Error loading db config: {e}")


def save_db_config():
    try:
        with open(DB_CONFIG_FILE, "w") as f:
            json.dump(
                {"interval": current_interval, "last_run": last_cleanup_time}, f
            )
    except Exception as e:
        logger.error(f"Error saving db config: {e}")


def cleanup_db():
    """Limpa tabelas temporárias do SQLite e executa VACUUM (thread-safe)."""
    global last_cleanup_time
    if not cleanup_lock.acquire(blocking=False):
        logger.warning("⚠️ Uma limpeza já está em curso. Pulando...")
        return

    try:
        auth_file = Path(AUTH_DIR) / "auth.sqlite"
        if not auth_file.exists():
            return

        logger.info("🧹 Iniciando limpeza automática do banco SQLite...")

        conn = sqlite3.connect(str(auth_file), isolation_level=None)
        cursor = conn.cursor()

        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.Error as e:
            logger.warning(f"⚠️ Não foi possível ativar modo WAL: {e}")

        cursor.execute("BEGIN TRANSACTION")
        for table in ["whatsmeow_event_buffer"]:
            try:
                cursor.execute(f"DELETE FROM {table}")
                logger.debug(f"Removidos registros da tabela {table}")
            except sqlite3.OperationalError:
                pass
        cursor.execute("COMMIT")

        try:
            cursor.execute("VACUUM")
        except sqlite3.Error as e:
            logger.error(f"❌ Erro ao executar VACUUM: {e}")

        conn.close()
        gc.collect()

        last_cleanup_time = int(time.time())
        save_db_config()
        logger.info("✅ Limpeza do banco concluída com sucesso.")
    except Exception as e:
        logger.error(f"❌ Erro na limpeza do banco: {e}")
    finally:
        cleanup_lock.release()


async def db_cleanup_scheduler():
    """Loop infinito que executa cleanup periodicamente conforme intervalo configurado."""
    while True:
        now = int(time.time())
        elapsed = (now - last_cleanup_time) / 60
        if elapsed >= current_interval:
            cleanup_db()
        await asyncio.sleep(60)


# ══════════════════════════════════════════════════════════
# HANDLER DE MENSAGENS RECEBIDAS
# ══════════════════════════════════════════════════════════

async def handle_message_async(c: NewClient, message: "MessageEv"):
    """Processa mensagem recebida: filtra, persiste, webhook, auto-read, handlers."""
    ts = message.Info.Timestamp
    if ts < START_TIME - 10 or message.Info.MessageSource.Chat.User == "status":
        return

    from src.utils.messageParser import parse_message, should_ignore_message

    if should_ignore_message(message):
        return

    source = message.Info.MessageSource
    chat = source.Chat

    jid = f"{chat.User}@s.whatsapp.net"
    if source.IsGroup:
        jid = f"{chat.User}@g.us"
    elif chat.Server == "lid":
        if source.SenderAlt and source.SenderAlt.Server == "s.whatsapp.net":
            jid = f"{source.SenderAlt.User}@s.whatsapp.net"
        elif source.RecipientAlt and source.RecipientAlt.Server == "s.whatsapp.net":
            jid = f"{source.RecipientAlt.User}@s.whatsapp.net"
        elif source.Sender and source.Sender.Server == "s.whatsapp.net":
            jid = f"{source.Sender.User}@s.whatsapp.net"

    phone = jid.split("@")[0]

    parsed = parse_message(message)
    if not parsed:
        _cache_reaction_if_present(message)
        return

    _cache_reaction_if_present(message)

    text_content = parsed.get("text", "")
    resolved_name = message.Info.Pushname or phone

    msg_dict = {
        "key": {
            "remoteJid": jid,
            "fromMe": source.IsFromMe,
            "id": message.Info.ID,
        },
        "messageTimestamp": int(ts),
        "pushName": resolved_name,
        "message": {"conversation": text_content} if text_content else {},
    }

    await storage.add_message_to_history(phone, msg_dict)
    await storage.save_chat_index(
        {
            "id": jid,
            "phone": phone,
            "name": resolved_name,
            "lastMessageTimestamp": int(ts),
        }
    )

    _auto_read_message(c, message, source)
    _forward_to_handler(c, message)

    del msg_dict
    if ts % 10 == 0:
        gc.collect()


def _cache_reaction_if_present(message):
    """Extrai e cacheia reação se presente na mensagem."""
    try:
        reaction = message.Message.reactionMessage
        if reaction and reaction.key.ID:
            reaction_cache[reaction.key.ID] = reaction.text
    except Exception:
        pass


async def _fire(event_type: str, data: dict):
    """Despacha evento para o sistema de webhooks nomeados."""
    try:
        from src.services.webhookDispatcher import dispatch_event
        await dispatch_event(event_type, data)
    except Exception as e:
        logger.error(f"Erro ao disparar evento '{event_type}': {e}")


def _auto_read_message(c, message, source):
    """Marca mensagem como lida automaticamente se configurado."""
    try:
        from src.services.whatsapp.settingsService import get_settings

        settings = get_settings()
        if settings.get("auto_read_message", False) and not source.IsFromMe:
            from neonize.utils.enum import ReceiptType
            c.mark_read(
                message.Info.ID,
                chat=source.Chat,
                sender=source.Sender,
                receipt=ReceiptType.READ,
            )
    except Exception as e:
        logger.debug(f"Auto-read falhou: {e}")


def _forward_to_handler(c, message):
    """Encaminha mensagem para o handler de callbacks."""
    try:
        from src.handlers.messageHandler import handleMessage
        asyncio.create_task(handleMessage(c, message))
    except Exception:
        pass


# ══════════════════════════════════════════════════════════
# CONTACT NAME RESOLVER
# ══════════════════════════════════════════════════════════

def get_contact_name(client, jid: str, push_name: str = None) -> str:
    """
    Resolve nome do contato com fallback de 4 níveis:
    FullName > FirstName > BusinessName > PushName.
    """
    try:
        from neonize.utils import build_jid
        contact = client.contact_get(build_jid(jid))
        if contact:
            name = (
                contact.FullName
                or contact.FirstName
                or contact.BusinessName
                or contact.PushName
            )
            if name and name.strip():
                return name.strip()
    except Exception:
        pass
    return (push_name or "Anônimo").strip()


# ══════════════════════════════════════════════════════════
# EVENT HANDLERS (registrados no start_bot)
# ══════════════════════════════════════════════════════════

def _on_qr(c: NewClient, qr_bytes: bytes):
    global current_qr
    current_qr = qr_bytes.decode("utf-8")

    # ── Monta URL pública dinâmica ──────────────────────────────────
    public_url = os.getenv("PUBLIC_URL")                        # 1. env var explicita (ex: http://meudominio.com:8080)
    if not public_url:
        user = os.getenv("USER", "")
        if user:
            public_url = f"http://services-{user}.alwaysdata.net:{PORT}"
        else:
            hostname = socket.gethostname()
            public_url = f"http://{hostname}:{PORT}"
    else:
        # Se a env var nao veio com :porta, adiciona
        if ":" not in public_url.split("/")[-1]:
            public_url = f"{public_url}:{PORT}"
    qr_url = f"{public_url}/qr"
    if API_KEY:
        qr_url += f"?API_KEY={API_KEY}"
    logger.info(f"📲 QR Code gerado! Acesse: {qr_url}")
    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.qr_ready", {"qr": current_qr}))
        )


def _on_connected(c: NewClient, event: "ConnectedEv"):
    global is_ready, current_qr, current_pair_code
    is_ready = True
    current_qr = None
    current_pair_code = None
    logger.info("✅ WhatsApp conectado e pronto")
    if main_loop and main_loop.is_running():
        phone = ""
        try:
            me = c.get_me()
            phone = me.JID.User
        except Exception:
            pass
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.connected", {"phone": phone}))
        )


def _on_pair_code(c: NewClient, code: str, connected: bool):
    global current_pair_code
    if not connected:
        current_pair_code = code
        logger.info(f"🔑 Código de pareamento recebido: {code}")


def _on_history_sync(c: NewClient, event: "HistorySyncEv"):
    pass  # Ignoramos sincronização de histórico para economizar RAM


def _on_call_offer(c: NewClient, event: "CallOfferEv"):
    """Rejeita chamadas automaticamente se configurado."""
    try:
        from src.services.whatsapp.settingsService import get_settings
        settings = get_settings()

        meta = event.basicCallMeta
        caller_jid = getattr(meta, "from")
        call_id = meta.callID

        from neonize.utils.jid import Jid2String
        caller_str = Jid2String(caller_jid)
        caller_phone = caller_str.split("@")[0]

        if main_loop and main_loop.is_running():
            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(_fire("call.received", {
                    "from": caller_phone,
                    "fromJid": caller_str,
                    "callId": call_id,
                }))
            )

        if not settings.get("call_reject_auto", False):
            return

        logger.info(f"📞 Chamada de {caller_str} (ID: {call_id}) — rejeitando automaticamente")

        msg = settings.get(
            "call_reject_message",
            "No momento não posso atender. Por favor, envie uma mensagem.",
        )
        if msg and main_loop and main_loop.is_running():
            async def _send_call_reply():
                try:
                    c.send_message(caller_jid, msg)
                    logger.info(f"📞 Mensagem de rejeição enviada para {caller_str}")
                except Exception as send_err:
                    logger.warning(f"⚠️ Não foi possível enviar mensagem de rejeição: {send_err}")

            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(_send_call_reply())
            )
    except Exception as e:
        logger.error(f"Erro no handler de chamada: {e}")


def _on_message(c: NewClient, message: "MessageEv"):
    """Agenda processamento de mensagem recebida no event loop principal."""
    if message.Info.Timestamp < START_TIME - 10:
        return
    try:
        if main_loop and main_loop.is_running():
            main_loop.call_soon_threadsafe(
                lambda: asyncio.create_task(handle_message_async(c, message))
            )
        else:
            logger.warning("🕒 Loop principal não disponível para processar mensagem")
    except Exception as e:
        logger.error(f"Erro ao agendar mensagem: {e}")


# ══════════════════════════════════════════════════════════
# MONKEY-PATCHES para captura de Pair Code (fallback)
# ══════════════════════════════════════════════════════════

def _patch_neonize_logging():
    """
    Aplica monkey-patches para capturar código de pareamento que pode vir
    via logs do CGo ou Python, como fallback para o callback oficial paircode.
    """
    try:
        import neonize.utils as neonize_utils
        import neonize.client as neonize_client

        if hasattr(neonize_utils, "log_whatsmeow"):
            original_log_whatsmeow = neonize_utils.log_whatsmeow

            def patched_log_whatsmeow(binary, size):
                try:
                    from neonize.proto.Neonize_pb2 import LogEntry
                    import ctypes

                    log_msg = LogEntry.FromString(ctypes.string_at(binary, size))
                    _intercept_pair_code(log_msg.Message)
                except Exception:
                    pass
                return original_log_whatsmeow(binary, size)

            neonize_utils.log_whatsmeow = patched_log_whatsmeow
            neonize_client.log_whatsmeow = patched_log_whatsmeow
    except Exception as e:
        logger.warning(f"⚠️ Erro ao patchear log_whatsmeow: {e}")

    try:
        import neonize.events as neonize_events

        if not hasattr(neonize_events.log, "_patched"):
            original_events_info = neonize_events.log.info

            def patched_events_info(msg, *args, **kwargs):
                try:
                    full_msg = str(msg) % args if args else str(msg)
                    _intercept_pair_code(full_msg)
                except Exception:
                    pass
                return original_events_info(msg, *args, **kwargs)

            neonize_events.log.info = patched_events_info
            neonize_events.log._patched = True
    except Exception as e:
        logger.warning(f"⚠️ Erro ao patchear neonize.events: {e}")

    try:
        import builtins

        if not hasattr(builtins.print, "_patched"):
            original_print = builtins.print

            def patched_print(*args, **kwargs):
                try:
                    full_msg = " ".join(str(a) for a in args)
                    _intercept_pair_code(full_msg)
                except Exception:
                    pass
                return original_print(*args, **kwargs)

            builtins.print = patched_print
            builtins.print._patched = True
    except Exception as e:
        logger.warning(f"⚠️ Erro ao patchear builtins.print: {e}")


def _intercept_pair_code(text: str):
    """Tenta extrair código de pareamento de uma string de log."""
    global current_pair_code
    if "Pair" in text or "code" in text.lower():
        match = re.search(r"([A-Z0-9]{4}[- ]?[A-Z0-9]{4})", text)
        if match:
            code = match.group(1).replace(" ", "-")
            current_pair_code = code
            logger.info(f"🎯 Código capturado via interceptor: {code}")


# ══════════════════════════════════════════════════════════
# BOOTSTRAP: start_bot
# ══════════════════════════════════════════════════════════

async def start_bot():
    """Inicializa o cliente Neonize: configura logging, registra handlers e conecta."""
    global client, is_ready, current_qr, main_loop
    main_loop = asyncio.get_running_loop()

    try:
        _reset_state()
        auth_file = str(Path(AUTH_DIR) / "auth.sqlite")
        _disconnect_existing()
        _configure_logging()
        _patch_neonize_logging()

        cleanup_db()
        client = NewClient(auth_file)
        _register_event_handlers()
        _load_db_config_and_start_scheduler()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, client.connect)

    except Exception as e:
        logger.error(f"❌ Erro ao iniciar bot: {str(e)}")
        await asyncio.sleep(RECONNECT_DELAY / 1000)
        asyncio.create_task(start_bot())


def _reset_state():
    """Reseta variáveis de estado globais para uma nova conexão."""
    reset_pair_code()


def _disconnect_existing():
    """Desconecta cliente existente se houver."""
    global client
    if client:
        try:
            client.disconnect()
        except Exception:
            pass


def _configure_logging():
    """Configura níveis de log do Neonize para reduzir verbosidade."""
    neonize_logger.setLevel(logging.ERROR)
    logging.getLogger("whatsmeow").setLevel(logging.INFO)


def _register_event_handlers():
    """Registra todos os callbacks de eventos no cliente Neonize."""
    client.qr(_on_qr)
    client.event(ConnectedEv)(_on_connected)
    client.event.paircode(_on_pair_code)
    client.event(HistorySyncEv)(_on_history_sync)
    client.event(CallOfferEv)(_on_call_offer)
    client.event(MessageEv)(_on_message)


def _load_db_config_and_start_scheduler():
    """Carrega configuração de cleanup e inicia o scheduler."""
    load_db_config()
    asyncio.create_task(db_cleanup_scheduler())


# ══════════════════════════════════════════════════════════
# LOGOUT
# ══════════════════════════════════════════════════════════

async def logout(keep_data=False):
    """Desconecta, limpa sessão e reinicia bot."""
    global client, is_ready, current_qr
    logger.info(f"🗑️ Iniciando logout... (Manter dados: {keep_data})")

    if client:
        try:
            client.logout()
            client.disconnect()
        except Exception:
            pass
        client = None

    is_ready = False
    current_qr = None

    if main_loop and main_loop.is_running():
        main_loop.call_soon_threadsafe(
            lambda: asyncio.create_task(_fire("connection.disconnected", {}))
        )

    auth_file = Path(AUTH_DIR) / "auth.sqlite"
    if auth_file.exists():
        try:
            auth_file.unlink()
        except Exception:
            pass

    if not keep_data:
        await storage.clear_all_data()
        logger.info("🧹 Dados de histórico apagados.")

    logger.info("🔄 Reiniciando bot para novo escaneamento...")
    await asyncio.sleep(2)
    asyncio.create_task(start_bot())
