# Webhook Events — ZapUnlocked API

Todos os webhooks recebem um envelope padrão:

```json
{
  "event": "message.text",
  "timestamp": "2025-01-01T12:00:00Z",
  "data": { ... }
}
```

Se o webhook tiver um `body` customizado com `{{placeholders}}`, esse body é enviado em vez do envelope padrão.

---

## Gerenciamento

| Rota | Descrição |
|------|-----------|
| `GET /webhooks` | Listar todos os webhooks |
| `POST /webhooks` | Criar webhook |
| `GET /webhooks/{name}` | Detalhes |
| `PUT /webhooks/{name}` | Editar |
| `DELETE /webhooks/{name}` | Apagar |
| `POST /webhooks/{name}/toggle` | Ativar/desativar |
| `POST /webhooks/{name}/test` | Enviar payload de teste |
| `GET /webhooks/events` | Listar todos os tipos de evento |

### Criar webhook — Exemplo

```json
POST /webhooks
{
  "name": "meu-crm",
  "url": "https://meucrm.com/hook",
  "events": ["message.text", "message.button_reply"],
  "active": true
}
```

Use `"events": ["*"]` para receber todos.

---

## Eventos de Mensagem Recebida

Todos os eventos de mensagem incluem estes campos base em `data`:

```json
{
  "messageId": "3EB0ABCDEF123456",
  "from": "5511999999999",
  "fromName": "João Silva",
  "fromJid": "5511999999999@s.whatsapp.net",
  "isGroup": false
}
```

---

### `message.text`

Mensagem de texto simples ou formatada.

```json
{
  "event": "message.text",
  "data": {
    "messageId": "...",
    "from": "5511999999999",
    "fromName": "João",
    "fromJid": "5511999999999@s.whatsapp.net",
    "isGroup": false,
    "text": "Olá! Como posso ajudar?",
    "quoted": {
      "id": "3EB0...",
      "fromMe": true
    }
  }
}
```

`quoted` é `null` se não for uma resposta.

---

### `message.image`

```json
{
  "event": "message.image",
  "data": {
    ...base,
    "caption": "Foto do produto",
    "mimetype": "image/jpeg",
    "fileLength": 204800
  }
}
```

---

### `message.video`

```json
{
  "event": "message.video",
  "data": {
    ...base,
    "caption": "Veja esse vídeo!",
    "mimetype": "video/mp4",
    "fileLength": 5242880,
    "isPTT": false,
    "isGif": false
  }
}
```

---

### `message.audio`

```json
{
  "event": "message.audio",
  "data": {
    ...base,
    "mimetype": "audio/ogg; codecs=opus",
    "fileLength": 30720,
    "isPTT": true,
    "durationSeconds": 8
  }
}
```

`isPTT: true` = nota de voz gravada no WhatsApp.

---

### `message.document`

```json
{
  "event": "message.document",
  "data": {
    ...base,
    "fileName": "contrato.pdf",
    "caption": "Segue o contrato",
    "mimetype": "application/pdf",
    "fileLength": 102400
  }
}
```

---

### `message.sticker`

```json
{
  "event": "message.sticker",
  "data": {
    ...base,
    "mimetype": "image/webp",
    "isAnimated": false
  }
}
```

---

### `message.contact`

```json
{
  "event": "message.contact",
  "data": {
    ...base,
    "displayName": "Maria Souza",
    "vcard": "BEGIN:VCARD\nVERSION:3.0\n..."
  }
}
```

---

### `message.location`

```json
{
  "event": "message.location",
  "data": {
    ...base,
    "lat": -23.5505,
    "lng": -46.6333,
    "name": "Av. Paulista",
    "address": "Av. Paulista, 1000 - São Paulo"
  }
}
```

---

### `message.reaction`

Reação (emoji) a uma mensagem.

```json
{
  "event": "message.reaction",
  "data": {
    ...base,
    "emoji": "❤️",
    "targetMessageId": "3EB0ABCDEF123456",
    "isRemoved": false
  }
}
```

`isRemoved: true` quando o usuário **remove** a reação (emoji vazio).

---

### `message.poll_created`

Enquete recebida.

```json
{
  "event": "message.poll_created",
  "data": {
    ...base,
    "pollName": "Qual o melhor sabor?",
    "options": ["Chocolate", "Morango", "Baunilha"]
  }
}
```

---

### `message.poll_vote`

Voto em enquete.

```json
{
  "event": "message.poll_vote",
  "data": {
    ...base,
    "pollId": "3EB0ABCDEF123456",
    "selectedOptions": ["Chocolate"]
  }
}
```

---

### `message.button_reply`

Clique em botão (quick_reply, cta_url, cta_copy, etc.).

```json
{
  "event": "message.button_reply",
  "data": {
    ...base,
    "buttonId": "opcao_sim",
    "displayText": "Sim",
    "type": "quick_reply"
  }
}
```

`type` pode ser `quick_reply` (botão moderno) ou `legacy_button` (formato antigo).

---

### `message.list_reply`

Seleção de item em lista interativa.

```json
{
  "event": "message.list_reply",
  "data": {
    ...base,
    "rowId": "1",
    "title": "X-Burguer",
    "description": "R$ 18,90"
  }
}
```

---

### `message.deleted`

Mensagem deletada pelo remetente.

```json
{
  "event": "message.deleted",
  "data": {
    ...base
  }
}
```

---

### `message.unknown`

Tipo de mensagem não mapeado.

```json
{
  "event": "message.unknown",
  "data": {
    ...base,
    "rawType": "senderKeyDistributionMessage"
  }
}
```

---

## Eventos de Mensagem Enviada

### `message.sent`

> **Nota:** Disparado manualmente via rota `/send` quando configurado. Não é automático para todas as rotas ainda — pode ser implementado por demanda.

```json
{
  "event": "message.sent",
  "data": {
    "to": "5511999999999",
    "type": "text",
    "messageId": "3EB0ABCDEF123456"
  }
}
```

---

## Eventos de Conexão

### `connection.connected`

WhatsApp conectado com sucesso.

```json
{
  "event": "connection.connected",
  "data": {
    "phone": "5511999999999"
  }
}
```

---

### `connection.disconnected`

WhatsApp desconectado (logout ou erro).

```json
{
  "event": "connection.disconnected",
  "data": {}
}
```

---

### `connection.qr_ready`

QR Code gerado para escaneamento.

```json
{
  "event": "connection.qr_ready",
  "data": {
    "qr": "2@abc123..."
  }
}
```

---

## Eventos de Chamada

### `call.received`

Chamada recebida (aceita ou rejeitada).

```json
{
  "event": "call.received",
  "data": {
    "from": "5511999999999",
    "fromJid": "5511999999999@s.whatsapp.net",
    "callId": "ABC123DEF456"
  }
}
```

---

## Placeholders (body customizado)

Se o webhook tiver `body` configurado, esses placeholders são substituídos:

| Placeholder | Valor |
|-------------|-------|
| `{{from}}` | Número do remetente |
| `{{text}}` | Texto da mensagem |
| `{{phone}}` | Mesmo que `{{from}}` |
| `{{id}}` | ID da mensagem |
| `{{timestamp}}` | Timestamp UTC atual |
| `{{requested}}` | (fetchMessages) qtd solicitada |
| `{{found}}` | (fetchMessages) qtd encontrada |
