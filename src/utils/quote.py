"""
Utility compartilhada para resolução de reply/quote em mensagens.

Elimina a duplicação do bloco de quote que existia em 8 controllers de send.
Uso único: controllers de envio chamam esta função em vez de reimplementar a lógica.
"""

from src.services.whatsapp.sender import find_message


async def resolve_quote(
    jid: str,
    reply_identifier: str | None = None,
    reply_type: str | None = "id",
) -> dict:
    """
    Resolve uma mensagem citada (reply/quote) no histórico local.

    Args:
        jid: JID completo do destinatário (ex: "5511999999999@s.whatsapp.net")
        reply_identifier: ID da mensagem ou texto para busca
        reply_type: "id" (padrão) para buscar por ID, "text" para buscar por texto

    Returns:
        Dict com chave "quoted" se encontrado, dict vazio caso contrário.

    Raises:
        Exception: Se reply_type=="text" e mensagem não for encontrada.
    """
    if not reply_identifier:
        return {}

    quoted_msg = await find_message(jid, reply_identifier, reply_type)
    if quoted_msg:
        return {"quoted": quoted_msg}

    if reply_type == "id":
        # Stub para que o WA ainda renderize o quote mesmo sem a msg no histórico local
        return {
            "quoted": {
                "key": {
                    "remoteJid": jid,
                    "fromMe": False,
                    "id": reply_identifier,
                },
                "message": {"conversation": "..."},
            }
        }

    raise Exception(
        f"Não foi possível encontrar a mensagem para responder com o texto: "
        f"'{reply_identifier}'"
    )
