# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

<p align="center">
  <img src="https://img.shields.io/github/stars/kauafpssx/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Stars">
  <img src="https://img.shields.io/github/forks/kauafpssx/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Forks">
  <img src="https://img.shields.io/github/repo-size/kauafpssx/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Repo Size">
  <img src="https://img.shields.io/github/license/kauafpssx/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="License">
</p>

### 🌐 Select Language / Selecione o Idioma:

|                                                                                   English                                                                                   |                                                                                   Español                                                                                   |                                                                                  Français                                                                                   |                                                                                   Deutsch                                                                                   |                                                                                    中文                                                                                     |                                                                                   日本語                                                                                    |                                                                                   Русский                                                                                   |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/us.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/en.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/es.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/es.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/fr.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/fr.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/de.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/de.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/cn.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/zh.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/jp.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/ja.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/ru.svg" width="40">](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/ru.md) |

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/br.svg" width="30"> O que é o [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)?

O **[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** é uma solução profissional, **100% gratuita e de código aberto**, projetada para transformar o WhatsApp em uma poderosa ferramenta de automação. Construída em **Python** com **[Neonize](https://github.com/krypton-byte/neonize)** como motor de conexão, esta API oferece uma interface REST (FastAPI) simples para gerenciar sessões, enviar mídias complexas e criar interações inteligentes sem a necessidade de um banco de dados pesado.

> [!TIP]
> Perfeito para desenvolvedores que buscam agilidade na integração de bots, notificações e sistemas de atendimento automatizados.

---

## 🚀 Funcionalidades em Destaque

- **Botões Stateless**: Crie fluxos interativos sem precisar de banco de dados, com webhooks criptografados.
- **Pareamento sem QR Code**: Conecte via código numérico, ideal para servidores sem interface gráfica ou câmeras.
- **Conversão Automática de Áudio**: Envie áudios que aparecem como gravados na hora (PTT) nativamente no iOS e Android.
- **Fila de Mídias Inteligente**: Gerenciamento automático para evitar o consumo excessivo de memória.
- **Placeholders Dinâmicos**: Personalize mensagens e webhooks com variáveis como `{{name}}`, `{{day}}` e `{{phone}}`.

---

## 🛤️ Principais Rotas

### 📨 Envio de Mensagens

- `POST /send` - Enviar Mensagem de Texto / Responder
- `POST /send_image` - Enviar Imagem
- `POST /send_video` - Enviar Vídeo (suporta GIF e PTV)
- `POST /send_audio` - Enviar Áudio (com conversão automática para PTT)
- `POST /send_document` - Enviar Documento
- `POST /send_sticker` - Enviar Figurinha
- `POST /send_reaction` - Enviar Reação com Emoji
- `POST /send_location` - Enviar Localização
- `POST /send_contact` / `POST /send_contacts` - Enviar Contato(s)
- `POST /send_link` - Enviar Link com Preview
- `POST /messages/delete` - Deletar Mensagem
- `POST /messages/read` - Marcar como Lida
- `POST /messages/edit` - Editar Mensagem Enviada

### 🔘 Mensagens Interativas

- `POST /send_wbuttons` - Enviar Botões (Lista, Ação, OTP, PIX)
- `POST /messages/send-option-list` - Enviar Lista de Opções
- `POST /messages/send-poll` - Enviar Enquete
- `POST /messages/send-poll-vote` - Votar em Enquete

### 🔍 Consultas e Gestão

- `POST /contacts/info` - Informações Detalhadas do Contato
- `POST /management/fetch_messages` - Buscar Histórico de Mensagens
- `POST /management/recent_contacts` - Listar Chats Recentes
- `GET /management/memory` - Status do Uso de Memória
- `GET /management/volume_stats` - Verificar Uso de Disco
- `GET /management/database/status` - Status e Estatísticas do Banco
- `POST /management/database/cleanup` - Limpeza Manual do Banco

### 🔗 Conexão e Sessão

- `GET /` - Página de Boas-vindas (HTML)
- `GET /status` - Status da Conexão e Sessão
- `GET /status/stream` - Status em Tempo Real (SSE)
- `GET /qr` - Visualizar QR Code Interativo
- `GET /qr/image` - Obter Imagem do QR Code (Base64)
- `POST /qr/pair` - Gerar Código de Pareamento Numérico
- `GET /settings/phone-code/{phone}` - Gerar Código de Pareamento por Número
- `POST /qr/logout` - Desconectar e Resetar Sessão

### 📡 Webhooks (CRUD)

- `POST /webhooks` - Criar Webhook Nomeado
- `GET /webhooks` - Listar Todos os Webhooks
- `PUT /webhooks/{name}` - Editar Webhook
- `DELETE /webhooks/{name}` - Remover Webhook
- `POST /webhooks/{name}/toggle` - Ativar/Desativar
- `POST /webhooks/{name}/test` - Testar Webhook
- `GET /webhooks/events` - Listar Tipos de Eventos (20 tipos)

### ⚙️ Perfil e Privacidade

- `POST /settings/profile` - Alterar Nome e Foto do Bot
- `POST /settings/privacy` - Ajustar Privacidade (Visto por último, etc)
- `POST /settings/block` - Bloquear/Desbloquear Contato

### 🤖 Configurações do Bot

- `GET /settings/bot` - Ver Configurações do Bot
- `POST /settings/bot` - Atualizar Configurações do Bot (tag IA, IP control)
- `PUT /settings/instance/call-reject-auto` - Rejeitar Chamadas Automaticamente
- `PUT /settings/instance/call-reject-message` - Mensagem de Chamada Rejeitada
- `PUT /settings/instance/auto-read-message` - Leitura Automática de Mensagens

### 📱 Instância

- `GET /instance/me` - Dados da Conta Conectada
- `GET /instance/device` - Dados Técnicos do Dispositivo
- `PUT /instance/update-name` - Renomear Instância

### 🖥️ Sistema

- `GET /system/env` - Ver Variáveis de Ambiente
- `PUT /system/env` - Atualizar Variáveis de Ambiente
- `POST /system/cleanup/force` - Limpeza Forçada de Mídia Temporária
- `GET /system/cleanup/settings` - Ver Configurações de Limpeza Automática
- `PUT /system/cleanup/settings` - Atualizar Intervalo de Limpeza Automática

---

# 🛠️ Instalação e Hospedagem

> Coloque sua API profissional de WhatsApp no ar em menos de 5 minutos com a **ZapUnlocked-API**.

## 💻 Instalação Local (Windows / Linux / macOS)

Ideal para desenvolvimento, testes ou rodar em servidor próprio.

1. **Clone o Repositório**

   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git
   cd ZapUnlocked-API
   ```

2. **Instale as Dependências**
   Execute o instalador automático do seu sistema:
   - **Windows**: `scripts\install\install.bat`
   - **Linux/macOS**: `bash scripts/install/install.sh`

3. **Configure o Ambiente**
   Gere o `.env` automaticamente com o script oficial:
   - **Windows**: `scripts\generate-env\generate-env.bat`
   - **Linux/macOS**: `bash scripts/generate-env/generate-env.sh`

   | Variável          | Descrição                                     |
   | :---------------- | :-------------------------------------------- |
   | `API_KEY`         | Senha para autenticação em todos os endpoints |
   | `INTERNAL_SECRET` | Token para validar assinaturas de webhook     |
   | `PORT`            | Porta da API (padrão: `8300`)                 |

4. **Execute a API**
   - **Windows**: `scripts\run\run.bat`
   - **Linux/macOS**: `bash scripts/run/run.sh`

---

## ☁️ Hospedagem: Alwaysdata (Grátis 24/7)

A **Alwaysdata** é a opção recomendada para hospedar a API de forma estável e gratuita sem precisar manter um servidor ligado.

### Recursos do Plano Free

| Recurso       | Disponível no Free    |
| :------------ | :-------------------- |
| Armazenamento | **1 GB SSD**          |
| RAM           | **256 MB**            |
| CPU           | **1/4 vCPU**          |
| Backup        | **3 dias** automático |
| Uptime        | **24/7** via Services |

### Passo a Passo para Deploy:

1. **Crie sua Conta**: Acesse [Alwaysdata.com](https://www.alwaysdata.com/) e escolha o plano **Free**.
2. **Acesse o Terminal SSH**: No painel, vá em **Remote access › SSH**.
3. **Clone e Instale**:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. **Gere o arquivo `.env`**:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
   O script gera as chaves automaticamente e salva o `.env` na raiz do projeto.
5. **Configure o Serviço (24/7)**: No painel, vá em **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. **URL de Acesso Interno**:
   ```
   http://services-[usuario].alwaysdata.net:8300/
   ```
   > O AlwaysData restringe acesso externo direto às portas 8300–8499. Para expor publicamente, configure um **Reverse Proxy** em **Web › Sites › Add a site** apontando para essa URL interna.

---

## 🔐 Autenticação (Login)

Após o deploy, conecte sua conta do WhatsApp acessando no navegador:

```text
http://services-[usuario].alwaysdata.net:8300/qr?API_KEY=SUA_SENHA_SECRETA
```

---

## 📖 Documentação Oficial

Para documentação técnica detalhada, exemplos de código e playground interativo, acesse nosso site oficial.

👉 **[Acesse a Documentação Oficial](https://zapunlocked-api.kauafpss.com.br)**

> ### Documentation Index
>
> Fetch the complete documentation index at: https://zapunlocked-api.kauafpss.com.br/llms.txt
> Use this file to discover all available pages before exploring further.

---

## ❤️ Créditos & Agradecimentos

- **[Neonize](https://github.com/krypton-byte/neonize)**: Biblioteca Python para conexão nativa com o WhatsApp Web.
- **[Alwaysdata](https://www.alwaysdata.com/)**: Infraestrutura gratuita de alta qualidade.

---

## 📄 Licença

Este projeto é licenciado sob a **Licença MIT**.

Feito com 💜 por [Kauã Ferreira](https://www.instagram.com/kauafpss_/).
