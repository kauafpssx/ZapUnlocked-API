# Correção: Erro ao enviar mensagem para Meta AI

> **Changelog desta correção:**
> - [`chat.py`] Removido `get_lid_from_pn()` e `is_on_whatsapp()` — Meta AI não é usuário comum, esses métodos retornavam JID vazio causando `"can't send message to unknown server"`
> - [`chat.py`] Removidos números falsos de 15 dígitos que não existiam (`867051314767696` e `718584497008509` estavam sendo usados como se fossem telefone, mas com servidor `@s.whatsapp.net` errado)
> - [`chat.py`] Descoberto via código fonte do whatsmeow que o servidor correto é `@bot` (constante `BotServer = "bot"` em `types/jid.go`)
> - [`chat.py`] Agora envia para `867051314767696@bot` (pessoal) ou `718584497008509@bot` (business)
> - [`event_handlers.py`] Adicionado tratamento para `chat.Server == "bot"` no `_resolve_jid()` — retorna só o identificador sem sufixo
> - [`event_handlers.py`] Atualizado `_META_AI_PHONES` com os identificadores corretos
> - [`response_tracker.py`] Comentários atualizados

## 1. Entendimento Simples

```
Você quer visitar a Casa do Meta AI no WhatsApp.

ANTIGAMENTE:
  O endereço era: 13135550002@s.whatsapp.net  (usuário normal)
  O porteiro achava e você entrava.

HOJE:
  O Meta AI mudou de endereço.
  Agora o endereço é: 867051314767696@bot  (bot, não usuário)
  
  O WhatsApp tem um sistema novo para robôs (Bots).
  Eles usam o servidor "bot", não "s.whatsapp.net".
  
  Se você insiste em mandar para @s.whatsapp.net:
    → O WhatsApp procura na lista de usuários normais
    → Não encontra (porque é um bot)
    → Erro: "no LID found"
```

---

## 2. A Descoberta — Código Fonte do whatsmeow

Olhando o código fonte **oficial do whatsmeow** (a biblioteca Go que o neonize usa):

```go
// whatsmeow/types/jid.go

// Servidores conhecidos no WhatsApp
const (
    BotServer = "bot"  // ← Robôs! É um tipo especial de servidor
)

// JIDs do Meta AI definidos oficialmente:
var (
    MetaAIJID    = NewJID("13135550002",     DefaultUserServer)  // 👴 ANTIGO
    NewMetaAIJID = NewJID("867051314767696", BotServer)          // 🆕 NOVO (@bot)
)
```

**Existem DOIS Meta AI:**

| Tipo | Identificador | Servidor | JID completo |
|------|--------------|----------|--------------|
| 👴 Antigo (legacy) | `13135550002` | `s.whatsapp.net` | `13135550002@s.whatsapp.net` |
| 🆕 Novo (pessoal) | `867051314767696` | `bot` | `867051314767696@bot` |
| 🆕 Novo (business) | `718584497008509` | `bot` | `718584497008509@bot` |

---

## 3. A Raiz de TODOS os Erros

### ❌ Erro 1: `"no LID found for 13135550002@s.whatsapp.net"`

```
Você enviou para: 13135550002@s.whatsapp.net  (endereço ANTIGO)
WhatsApp responde: "Esse número não tem LID aqui"

Motivo: O Meta AI não é mais acessível pelo endereço antigo.
Algumas regiões/contas ainda funcionam, outras não.
```

### ❌ Erro 2: `"can't send message to unknown server"`

```
Você enviou para um JID com Server vazio ("").
O whatsmeow rejeita porque não sabe o que fazer com server vazio.

Motivo: código tentou get_lid_from_pn() que retornou JID vazio.
```

### ❌ Erro 3: `"no LID found for 867051314767696@s.whatsapp.net"`

```
Você enviou para: 867051314767696@s.whatsapp.net  (identificador NOVO com servidor VELHO)

Motivo: O identificador 867051314767696 NÃO é um telefone.
É um ID de serviço. O servidor correto é @bot, não @s.whatsapp.net.
```

---

## 4. O que o `wa.me/ais/` significa?

Quando você vê:

```
https://wa.me/ais/867051314767696
https://wa.me/ais/718584497008509
```

O `/ais/` = **A**rtificial **I**ntelligence **S**ervice.

É um endpoint especial do WhatsApp para serviços de IA.
O número (ex: `867051314767696`) não é um telefone — é um **identificador de serviço**.
Ele usa o servidor `@bot` internamente.

---

## 5. Diagnóstico

### Passo 1 — Teste manual no celular

1. Abra o WhatsApp
2. Toque no ícone do **Meta AI** (círculo roxo/rosa)
3. Mande "oi"
4. Funcionou?

### Passo 2 — Veja o log da API

| Mensagem no log | Causa |
|-----------------|-------|
| `no LID found for 13135550002@s.whatsapp.net` | Usando número antigo com servidor errado |
| `no LID found for 867051314767696@s.whatsapp.net` | Usando @s.whatsapp.net em vez de @bot |
| `can't send message to unknown server` | JID vazio (get_lid_from_pn falhou) |
| `Sending to Meta AI (xxx@bot)` | ✅ Correto! Se falhar, é conta/região |

### Passo 3 — Webhook: veja o JID real do Meta AI

Quando uma mensagem CHEGA do Meta AI (resposta ao seu "oi"), o webhook mostra:

```json
{
  "event": "message",
  "data": {
    "remoteJid": "867051314767696@bot",
    "senderJid": "867051314767696@bot"
  }
}
```

Se o `remoteJid` terminar com `@bot`, você confirmou que o servidor correto é `bot`.

---

## 6. Soluções

### ✅ Solução 1 — Usar o servidor `@bot` (recomendado)

No `.env`, configure:

```ini
# Meta AI — identificadores @bot (padrão)
META_AI_PERSONAL=867051314767696
META_AI_BUSINESS=718584497008509
```

O código já usa `@bot` como servidor padrão.

### ✅ Solução 2 — Fallback para legacy (@s.whatsapp.net)

Se `@bot` não funcionar na sua região, tente o antigo:

```ini
META_AI_SERVER=s.whatsapp.net
META_AI_PHONE=13135550002
```

### ✅ Solução 3 — Primeiro contato manual

1. No WhatsApp do celular, toque no ícone do Meta AI
2. Mande "hello"
3. Aguarde resposta
4. Reinicie a API
5. Teste `POST /ai/ask`

### ✅ Solução 4 — Verificar tipo de conta

- **WhatsApp pessoal** → ✅ Ok
- **WhatsApp Business** → ❌ Pode não funcionar

---

## 7. Correções no Código (já aplicadas)

### `src/services/whatsapp/ai/chat.py`

```python
# Antes (ERRADO):
jid = neonize_build_jid("13135550002", "s.whatsapp.net")

# Depois (CORRETO):
# Usa o identificador e servidor adequados:
#   Pessoal:  867051314767696@bot
#   Business: 718584497008509@bot
identifier, server = _pick_meta_ai_id()
jid = neonize_build_jid(identifier, server)
```

### `src/services/whatsapp/event_handlers.py`

```python
# Antes: só tratava server "lid"
if chat.Server == "lid":
    ...

# Depois: também trata server "bot"
if chat.Server == "bot":
    return chat.User  # só o identificador, sem @s.whatsapp.net
```

---

## 8. Mapa Completo dos JIDs do WhatsApp

| Tipo | Servidor | Exemplo |
|------|----------|---------|
| 👤 Usuário normal | `s.whatsapp.net` | `5511999999999@s.whatsapp.net` |
| 🕵️ LID (privacidade) | `lid` | `123456789@lid` |
| 👥 Grupo | `g.us` | `abcd1234@g.us` |
| 📢 Broadcast | `broadcast` | `status@broadcast` |
| 📰 Newsletter | `newsletter` | `xyz@newsletter` |
| 🤖 **Bot (Meta AI)** | **`bot`** | **`867051314767696@bot`** |
| 📱 Messenger | `msgr` | — |
| 🔗 Interop | `interop` | — |

---

## 9. Checklist

- [ ] Identificar se usa Meta AI novo (`@bot`) ou velho (`@s.whatsapp.net`)
- [ ] Configurar `.env` com os identificadores corretos
- [ ] Verificar se `META_AI_SERVER` está como `bot` (padrão)
- [ ] Testar manualmente no celular primeiro
- [ ] Rodar `POST /ai/ask` com `"message": "What is the capital of Brazil?"`
- [ ] Ver log para confirmar que está enviando para `xxx@bot`
- [ ] Se falhar com "no LID found" mesmo com @bot, é região/conta

---

## Referências

- [whatsmeow Go source — types/jid.go (linha 34, `BotServer`)](https://github.com/tulir/whatsmeow/blob/main/types/jid.go#L34)
- [whatsmeow Go source — `NewMetaAIJID`](https://github.com/tulir/whatsmeow/blob/main/types/jid.go#L54)
- [WhatsApp FAQ: About Meta AI](https://faq.whatsapp.com/2257017191175152)
- [Código atual: `src/services/whatsapp/ai/chat.py`](../src/services/whatsapp/ai/chat.py)
- [Código atual: `src/services/whatsapp/event_handlers.py`](../src/services/whatsapp/event_handlers.py)
