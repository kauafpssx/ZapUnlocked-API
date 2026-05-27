# Neonize — Base de Conhecimento

> Tudo que aprendemos sobre a biblioteca `neonize` durante o desenvolvimento do ZapUnlocked-API.  
> Atualizar sempre que descobrir novos padrões, bugs, ou comportamentos inesperados.

---

## 📚 Índice

1. [Visão Geral](#visão-geral)  
2. [Estrutura do Cliente](#estrutura-do-cliente)  
3. [Métodos Disponíveis](#métodos-disponíveis)  
4. [Contatos (ContactStore)](#contatos-contactstore)  
5. [Envio de Mensagens](#envio-de-mensagens)  
6. [Mensagens Interativas (Botões)](#mensagens-interativas-botões)  
7. [Enquetes (Polls)](#enquetes-polls)  
8. [Funções Variadic — Armadilhas](#funções-variadic--armadilhas)  
9. [Métodos Ausentes ou Quebrados](#métodos-ausentes-ou-quebrados)  
10. [Execução Assíncrona](#execução-assíncrona)  
11. [Respostas Protobuf — Campos Corretos](#respostas-protobuf--campos-corretos)  

---

## Visão Geral

- **Repo:** https://github.com/krypton-byte/neonize
- **Baseado em:** Whatsmeow (Go) com bindings Python via gRPC
- **Instalação:** `pip install neonize`
- **Autenticação:** SQLite local (ex: `auth_info/myapp.db`)

```python
from neonize.client import NewClient

client = NewClient("auth_info/session.db")
client.connect()
```

---

## Estrutura do Cliente

O cliente principal é `NewClient`. Ele possui um sub-objeto `contact` do tipo `ContactStore`:

```python
sock = NewClient("session.db")
sock.contact  # -> ContactStore instance
```

**Propriedades e sub-objetos importantes:**
| Atributo | Tipo | Descrição |
|---|---|---|
| `sock.contact` | `ContactStore` | Acesso ao banco local de contatos |

---

## Métodos Disponíveis

### NewClient (principais)

| Método | Descrição | Notas |
|---|---|---|
| `is_on_whatsapp(*phones)` | Verifica se números estão no WA | **VARIADIC** — ver seção de armadilhas |
| `get_user_info(*jids)` | Retorna info do usuário (status, VerifiedName) | **VARIADIC**, retorna lista |
| `get_profile_picture(jid)` | URL da foto de perfil | Pode lançar exceção se não encontrar |
| `send_message(jid, message)` | Envia mensagem protobuf genérica | Aceita qualquer `Message` |
| `send_image(jid, image, caption)` | Atalho para enviar imagem | Aceita URL, bytes, ou caminho |
| `send_audio(jid, audio)` | Atalho para enviar áudio | |
| `send_video(jid, video, caption)` | Atalho para enviar vídeo | |
| `send_sticker(jid, sticker)` | Atalho para enviar sticker (WebP) | |
| `send_document(jid, document, ...)` | Atalho para enviar documento | |
| `build_poll_vote_creation(name, options, selectable_count)` | Cria poll | Retorna `Message` |
| `build_poll_vote(msg_info, options)` | Cria voto numa poll | Requer `MessageInfo` correto |
| `build_image_message(url_or_bytes)` | Processa imagem e retorna `Message` | `.imageMessage` contém o sub-objeto |
| `upload(bytes, MediaType)` | Faz upload de mídia | Retorna `UploadResponse` |
| `revoke_message(jid, msg_key)` | Deleta mensagem | |
| `mark_read(ids, timestamp, jid, sender)` | Marca como lida | |

### ContactStore (acessado via `sock.contact`)

| Método | Descrição |
|---|---|
| `get_all_contacts()` | Lista todos os contatos do banco local |
| `get_contact(jid)` | Pega dados de um contato pelo JID |
| `put_pushname(jid, name)` | Salva push name no banco local |
| `put_contact_name(jid, fullname, firstname)` | Salva nome completo no banco local |
| `put_all_contact_name(entries)` | Bulk update de nomes |

---

## Contatos (ContactStore)

### Como obter informações de um contato

```python
from neonize.utils.jid import build_jid

jid = build_jid("5511999999999@s.whatsapp.net")
contact = sock.contact.get_contact(jid)

print(contact.FullName)      # Nome completo (do banco local)
print(contact.FirstName)     # Primeiro nome
print(contact.PushName)      # Push name atual do WhatsApp
print(contact.BusinessName)  # Nome de conta Business
```

> ⚠️ **Os nomes só estarão preenchidos se o contato já interagiu com o número conectado ou se o nome foi salvo manualmente via `put_contact_name`.**

### Listar todos os contatos

```python
contacts = sock.contact.get_all_contacts()
for c in contacts:
    print(c.ContactID.User, c.PushName)
```

---

## Envio de Mensagens

### Texto Simples
```python
from neonize.utils.jid import build_jid

jid = build_jid("554499999999@s.whatsapp.net")
sock.send_message(jid, "Hello World!")
```

### Responder Mensagem (Quote)
```python
sock.send_message(jid, "Resposta!", quoted=message_event)
```

### Imagem
```python
sock.send_image(jid, "https://example.com/img.jpg", caption="Legenda")
sock.send_image(jid, open("file.jpg","rb").read(), caption="Local")
```

### Sticker (WebP)
```python
sock.send_sticker(jid, "https://example.com/sticker.webp")
```

### Vídeo
```python
sock.send_video(jid, "https://example.com/video.mp4", caption="Legenda")
```

---

## Mensagens Interativas (Botões)

> ⚠️ **Estrutura confirmada pelos arquivos `.pyi` do `neonize-master`.**

### Estrutura correta (rootContextV1 — compatível com iOS/Android/Web)

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import (
    Message, MessageContextInfo, InteractiveMessage, DeviceListMetadata
)

interactive_msg = InteractiveMessage()
interactive_msg.body.text = "Texto principal"
interactive_msg.footer.text = "Rodapé"
interactive_msg.header.title = "Título"          # texto no header
# OU:
# interactive_msg.header.hasMediaAttachment = True
# interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)

btn = interactive_msg.nativeFlowMessage.buttons.add()
btn.name = "cta_url"   # ou cta_call, cta_copy, quick_reply, single_select, payment_info
btn.buttonParamsJSON = json.dumps({...})

interactive_msg.nativeFlowMessage.messageVersion = 1

msg = Message(
    interactiveMessage=interactive_msg,
    messageContextInfo=MessageContextInfo(
        deviceListMetadata=DeviceListMetadata(),
        deviceListMetadataVersion=2
    )
)
sock.send_message(jid, msg)
```

### Tipos de botão e seus `buttonParamsJSON`

| `btn.name` | Tipo | `buttonParamsJSON` |
|---|---|---|
| `cta_url` | Link externo | `{"display_text": "...", "url": "https://...", "merchant_url": "https://..."}` |
| `cta_call` | Ligar | `{"display_text": "...", "phoneNumber": "+55..."}` |
| `cta_copy` | Copiar código (OTP) | `{"display_text": "...", "copy_code": "123456"}` |
| `quick_reply` | Botão de resposta rápida | `{"display_text": "...", "id": "btn_id"}` |
| `single_select` | Lista de seleção | veja abaixo |
| `payment_info` | PIX (Business only) | `{"payment_settings": [{"type": "pix_static_code", "pix_static_code": {"merchant_name": "...", "key": "...", "key_type": "EMAIL"}}]}` |

### `single_select` — formato correto das seções

```python
# ⚠️ IMPORTANTE: usar "id" (não "rowID") nas rows!
btn.name = "single_select"
btn.buttonParamsJSON = json.dumps({
    "title": "Ver opções",
    "sections": [
        {
            "title": "Seção 1",
            "rows": [
                {"id": "row_1", "title": "Opção 1", "description": "Descrição"},
                {"id": "row_2", "title": "Opção 2", "description": "Outra desc"}
            ]
        }
    ]
})
```

### Imagem no Header

```python
# build_image_message retorna um Message completo
# .imageMessage é o sub-objeto ImageMessage que vai no header
img_full = client.build_image_message(image_url_or_bytes)
interactive_msg.header.hasMediaAttachment = True
interactive_msg.header.imageMessage.CopyFrom(img_full.imageMessage)
```

### Reply/Quote dentro de InteractiveMessage

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import ContextInfo

ctx = ContextInfo()
ctx.stanzaId = quoted_message.Info.ID
ctx.participant = quoted_message.Info.MessageSource.Sender.User + "@s.whatsapp.net"
ctx.quotedMessage.CopyFrom(quoted_message.Message)

# O contextInfo fica DENTRO do InteractiveMessage, não na raiz
interactive_msg.contextInfo.CopyFrom(ctx)
```

---

## Enquetes (Polls)

### Criar enquete

```python
from neonize.utils.enum import VoteType

vote_type = VoteType.SINGLE  # ou VoteType.MULTIPLE (selectable_count=0)
msg = client.build_poll_vote_creation(
    name="Qual cor?",
    options=["Vermelho", "Azul", "Verde"],
    selectable_count=vote_type
)
client.send_message(jid, msg)
```

### Votar em enquete

> ⚠️ **MessageSource NÃO TEM `remoteJID`/`fromMe`/`ID`!**  
> Os campos corretos são `Chat` (JID object), `IsFromMe` (bool), `IsGroup` (bool).  
> O `ID` da mensagem fica em `MessageInfo.ID`, não dentro de `MessageSource`.

```python
from neonize.proto.waE2E.WAWebProtobufsE2E_pb2 import Message, PollCreationMessage
from neonize.proto.Neonize_pb2 import MessageInfo, MessageSource, JID as NeonizeJID

target_jid = build_jid(phone)

msg_info = MessageInfo(
    ID=poll_message_id,          # ID da mensagem original da enquete
    MessageSource=MessageSource(
        Chat=NeonizeJID(
            User=target_jid.User,
            Server=target_jid.Server
        ),
        IsFromMe=False,
        IsGroup=False
    ),
    Message=Message(
        pollCreationMessage=PollCreationMessage(name="Nome da enquete")
    )
)

vote_msg = client.build_poll_vote(msg_info, ["Azul"])
client.send_message(target_jid, vote_msg)
```

---

## Funções Variadic — Armadilhas

Algumas funções do neonize são **variadic** (aceitam múltiplos argumentos), não listas:

### ❌ ERRADO
```python
results = sock.is_on_whatsapp(["5511999999999", "5522888888888"])  # ERRO!
user_infos = sock.get_user_info([jid1, jid2])  # ERRO!
```

### ✅ CORRETO
```python
results = sock.is_on_whatsapp("5511999999999", "5522888888888")
user_infos = sock.get_user_info(jid1, jid2)

# Para um único argumento:
results = sock.is_on_whatsapp(phone)  # sem lista!
user_infos = sock.get_user_info(jid)
```

### Campo de retorno `is_on_whatsapp`
```python
results = sock.is_on_whatsapp("5511999999999")
result = results[0]
print(result.IsIn)           # bool — SE está no WhatsApp (campo correto!)
print(result.JID.User)       # número
print(result.VerifiedName)   # nome verificado (se business)
# ⚠️ NÃO EXISTE result.IsOnWhatsApp! O campo correto é IsIn
```

---

## Métodos Ausentes ou Quebrados

| Método | Status | Alternativa |
|---|---|---|
| `get_status_message(jid)` | ❌ Não existe na versão atual | `get_user_info` (campo `Status`) |
| `get_business_profile(jid)` | ❌ Não existe na versão atual | Sem alternativa por enquanto |
| `get_contact(jid)` via `NewClient` | ❌ Não exposto diretamente | Usar `sock.contact.get_contact(jid)` |
| PIX via `payment_info` | ⚠️ Só funciona em contas Business | Para pessoal: usar `cta_copy` com a chave |

---

## Execução Assíncrona

O neonize é **síncrono** internamente. Para usar em FastAPI (async), sempre usar `asyncio.to_thread`:

```python
import asyncio

# Execução com timeout para evitar hangs
try:
    result = await asyncio.wait_for(
        asyncio.to_thread(sock.is_on_whatsapp, phone),
        timeout=4.0
    )
except asyncio.TimeoutError:
    logger.error("Timeout ao chamar is_on_whatsapp")
```

> ⚠️ **NUNCA** chamar métodos do neonize diretamente em funções async sem `asyncio.to_thread`! Isso bloqueia o event loop inteiro.

### Timeouts recomendados
| Método | Timeout |
|---|---|
| `is_on_whatsapp` | 4s |
| `get_user_info` | 4s |
| `get_profile_picture` | 4s |
| `sock.contact.*` | 3s |
| `send_message` | 10s |
| `send_image/video/audio` | 30s |

---

## Respostas Protobuf — Campos Corretos

### JID (Neonize_pb2)
```python
# Campos: User, RawAgent, Device, Integrator, Server, IsEmpty
jid.User    # "5511999999999"
jid.Server  # "s.whatsapp.net" ou "g.us"
```

### MessageInfo (Neonize_pb2)
```python
# Campos: MessageSource, ID, ServerID, Type, Pushname, Timestamp, Category, Multicast, MediaType, Edit
info.ID              # Message ID (string)
info.MessageSource   # MessageSource object
info.Pushname        # nome do remetente
info.Timestamp       # unix timestamp
```

### MessageSource (Neonize_pb2)
> ⚠️ NÃO tem `remoteJID`, `fromMe`, nem campo `ID`!
```python
# Campos: Chat (JID), Sender (JID), IsFromMe (bool), IsGroup (bool), AddressingMode, SenderAlt, RecipientAlt
source.Chat.User     # número do chat
source.Chat.Server   # "s.whatsapp.net" ou "g.us"
source.Sender.User   # número do remetente
source.IsFromMe      # bool
source.IsGroup       # bool
```

### IsOnWhatsAppResponse
```python
result.IsIn          # bool
result.JID.User      # string com número
result.VerifiedName  # nome da conta Business, se houver
```

### ContactInfo (retornado por `contact.get_contact`)
```python
contact.Found         # bool
contact.FirstName     # str
contact.FullName      # str  
contact.PushName      # str
contact.BusinessName  # str
contact.RedactedPhone # str
```

### UserInfo (retornado por `get_user_info`)
```python
user_info.Status           # str (bio/status)
user_info.VerifiedName.Details.VerifiedName  # nome verificado
user_info.VerifiedName.Details.PublicName    # nome público
```

### JID Helper
```python
from neonize.utils.jid import build_jid

# Formato correto:
jid = build_jid("5511999999999@s.whatsapp.net")  # indivíduo
jid = build_jid("120363xxxxxxx-xxxxxx@g.us")     # grupo

# Acessar partes:
jid.User   # número sem domínio
jid.Server # "s.whatsapp.net" ou "g.us"
```
