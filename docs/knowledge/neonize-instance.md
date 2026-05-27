# Neonize — Gerenciamento de Instância

> Como interagir com o cliente neonize para configurar e controlar a instância do WhatsApp.

---

## 📞 Chamadas (CallOfferEv)

O neonize expõe o evento `CallOfferEv` para interceptar chamadas de voz/vídeo recebidas.

### Importação
```python
from neonize.events import CallOfferEv
```

### Registrar handler de chamada
```python
from neonize.utils.jid import jid_is_lid, Jid2String

@client.event(CallOfferEv)
def on_call_offer(c: NewClient, event: CallOfferEv):
    meta = event.basicCallMeta
    caller_jid = getattr(meta, "from")  # "from" é DECIMAL (minúsculo!) e keyword Python
    call_id = meta.callID
    print(f"Chamada de {Jid2String(caller_jid)} | ID: {call_id}")
```

### Campos disponíveis em CallOfferEv

> ⚠️ **NÃO existe `event.Caller`, `event.CallID` nem `event.basicCallMeta.From` (maiúsculo)!**
> O campo protobuf chama-se `from` (minúsculo) e é acessado via `getattr(meta, "from")`.

| Campo | Acesso | Tipo | Description |
|---|---|---|---|
| `basicCallMeta` | `event.basicCallMeta` | objeto | Container de metadados da chamada |
| `from` (chamador) | `getattr(event.basicCallMeta, "from")` | JID | JID de quem está ligando |
| `callID` | `event.basicCallMeta.callID` | str | ID único da chamada |
| `callCreator` | `event.basicCallMeta.callCreator` | JID | Criador da chamada |
| `timestamp` | `event.basicCallMeta.timestamp` | int | Unix timestamp da chamada |

### LID JIDs em chamadas

Quando um chamador usa multi-dispositivo, o `from` pode ser um **LID** (`@lid`) em vez de `@s.whatsapp.net`.
O neonize fornece utilitários para detectar e resolver LID:

```python
from neonize.utils.jid import jid_is_lid, Jid2String

caller_jid = getattr(event.basicCallMeta, "from")

if jid_is_lid(caller_jid):
    # Resolver LID para JID real via get_user_info
    phone_jid = None
    try:
        user_info_list = c.get_user_info(caller_jid)
        for user_info in user_info_list:
            for device_jid in user_info.UserInfo.Devices:
                if device_jid.Server == "s.whatsapp.net" and device_jid.User:
                    phone_jid = f"{device_jid.User}@s.whatsapp.net"
                    break
            if phone_jid:
                break
    except Exception as e:
        print(f"Falha ao resolver LID: {e}")
else:
    phone_jid = f"{caller_jid.User}@s.whatsapp.net"

# Utilitários de JID:
# jid_is_lid(jid)   → bool  — verifica se jid.Server == "lid"
# Jid2String(jid)   → str   — serializa JID como string human-readable
```

### Não existe `reject_call` no neonize

> ⚠️ **`c.reject_call()` não existe no neonize!** A chamada cai por timeout naturalmente no chamador.


---

## 📱 Pareamento por Número (PairPhone)

Alternativa ao QR Code — gera um código de 8 dígitos para inserir no WhatsApp.

### Assinatura
```python
def PairPhone(
    phone: str,              # Número no formato internacional (554499999999)
    show_push_notification: bool,  # Exibir notificação no celular
    client_name: ClientName = ClientName.LINUX,
    client_type: Optional[ClientType] = None,
) -> str
```

### Uso correto (síncrono dentro de asyncio.to_thread)
```python
import asyncio
from neonize.client import NewClient

code = await asyncio.wait_for(
    asyncio.to_thread(client.PairPhone, "554499999999", True),
    timeout=15.0
)
print(f"Código: {code}")  # Ex: "ABCD-EFGH"
```

### Pré-requisito
- O cliente DEVE estar **aguardando conexão** (sem sessão autenticada ativa)
- O número DEVE ter WhatsApp instalado
- O código expira rapidamente (± 60 segundos)

### Como usar no WhatsApp
1. Abra o WhatsApp no celular
2. Vá em **Dispositivos** > **Conectar dispositivo**
3. No celular, toque em **Conectar com número de telefone**
4. Digite o código de 8 dígitos gerado pela API

---

## ✅ Marcar Mensagem como Lida (mark_read)

### Assinatura correta
```python
from neonize.utils.enum import ReceiptType

# mark_read usa *args (variadic) para IDs e keyword-only args para o resto
client.mark_read(
    message.Info.ID,          # ID da mensagem — passado como positional arg
    chat=source.Chat,         # JID do chat (source = message.Info.MessageSource)
    sender=source.Sender,     # JID do remetente
    receipt=ReceiptType.READ, # Tipo do recibo (READ, PLAYED, etc.)
)
```

> ⚠️ `chat` e `sender` devem ser **JID objects** (vindo do evento), não strings.
> Use `source.Chat` e `source.Sender` diretamente do `message.Info.MessageSource` em vez de `build_jid()`.

---

## 🔄 Eventos de Chamada Disponíveis

| Evento | Descrição |
|---|---|
| `CallOfferEv` | Chamada recebida (momento para rejeitar) |
| `CallAcceptEv` | Chamada aceita |
| `CallOfferNoticeEv` | Aviso de chamada chegando |
| `CallPreAcceptEv` | Pré-aceitação de chamada |
| `UnknownCallEventEV` | Evento de chamada desconhecido |

---

## ⚙️ Configurações de Instância (settings.json)

Configurações persistidas em `data/settings.json` que controlam comportamentos automáticos:

| Chave | Tipo | Padrão | Descrição |
|---|---|---|---|
| `call_reject_auto` | bool | `false` | Rejeitar chamadas automaticamente |
| `call_reject_message` | str | `"..."` | Mensagem enviada ao rejeitar |
| `auto_read_message` | bool | `false` | Marcar mensagens como lidas automaticamente |
