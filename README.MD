# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

<p align="center">
  <img src="https://img.shields.io/github/stars/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Stars">
  <img src="https://img.shields.io/github/forks/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Forks">
  <img src="https://img.shields.io/github/repo-size/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Repo Size">
  <img src="https://img.shields.io/github/license/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="License">
</p>

### 🌐 Select Language / Selecione o Idioma:

|                                                                                   English                                                                                   |                                                                                   Español                                                                                   |                                                                                  Français                                                                                   |                                                                                   Deutsch                                                                                   |                                                                                    中文                                                                                     |                                                                                   日本語                                                                                    |                                                                                   Русский                                                                                   |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------: |
| [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/us.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/en.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/es.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/es.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/fr.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/fr.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/de.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/de.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/cn.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/zh.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/jp.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/ja.md) | [<img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/ru.svg" width="40">](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/readmes/ru.md) |

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/br.svg" width="30"> O que é o [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)?

O **[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** é uma solução profissional, **100% gratuita e de código aberto**, projetada para transformar o WhatsApp em uma poderosa ferramenta de automação. Construída em **Python** com **[Neonize](https://github.com/krypton-byte/neonize)** como motor de conexão, esta API oferece uma interface REST (FastAPI) simples para gerenciar sessões, enviar mídias complexas e criar interações inteligentes sem a necessidade de um banco de dados pesado.

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

- `GET /status` - Status da Conexão e Sessão
- `GET /qr` - Visualizar QR Code Interativo
- `GET /qr/image` - Obter Imagem do QR Code (Base64)
- `POST /qr/pair` - Gerar Código de Pareamento Numérico
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

---

# 🛠️ Instalação e Hospedagem

> Coloque sua API profissional de WhatsApp no ar em menos de 5 minutos com a **ZapUnlocked-API**.

## 💻 Instalação Local (Windows / Linux / macOS)

Ideal para desenvolvimento, testes ou rodar em servidor próprio.

1. **Clone o Repositório**

   ```bash
   git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git
   cd ZapUnlocked-API
   ```

2. **Instale as Dependências**
   Execute o instalador automático do seu sistema:
   - **Windows**: `scripts\install.bat`
   - **Linux/macOS**: `bash scripts/install.sh`

3. **Configure o Ambiente**
   Copie o `.env.example` e defina suas variáveis:

   ```bash
   cp .env.example .env
   ```

   | Variável          | Descrição                                     |
   | :---------------- | :-------------------------------------------- |
   | `API_KEY`         | Senha para autenticação em todos os endpoints |
   | `INTERNAL_SECRET` | Token para validar assinaturas de webhook     |

4. **Execute a API**
   - **Windows**: `scripts\run.bat`
   - **Linux/macOS**: `bash scripts/run.sh`

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

1. **Fork do Repositório**: Faça um fork do [Repositório Oficial](https://github.com/zKauaFerreira/ZapUnlocked-API) para sua conta do GitHub.
2. **Crie sua Conta**: Acesse [Alwaysdata.com](https://www.alwaysdata.com/) e escolha o plano **Free**.
3. **Acesse o Terminal Web**: No painel, vá em **Remote access › SSH** e acesse o host SSH fornecido.
4. **Instale a API**: No terminal SSH, rode:
   ```bash
   git clone https://github.com/seu-usuario/ZapUnlocked-API.git
   cd ZapUnlocked-API
   bash scripts/install.sh
   ```
5. **Configure o Serviço (24/7)**: No painel da Alwaysdata, vá em **Web › Services** e adicione um novo serviço:
   - **Command**: `python main.py`
   - **Working directory**: `/home/[usuario]/ZapUnlocked-API`

---

## 🔐 Autenticação (Login)

Após o deploy, conecte sua conta do WhatsApp acessando no navegador:

```text
https://seu-slug.alwaysdata.net/qr?API_KEY=SUA_SENHA_SECRETA
```

---

## 📖 Documentação Oficial

Para documentação técnica detalhada, exemplos de código e playground interativo, acesse nosso site oficial.

👉 **[Acesse a Documentação Oficial](https://zapdocs.kauafpss.qzz.io)**

> ### Documentation Index
>
> Fetch the complete documentation index at: https://zapdocs.kauafpss.qzz.io/llms.txt
> Use this file to discover all available pages before exploring further.

---

## ❤️ Créditos & Agradecimentos

- **[Neonize](https://github.com/krypton-byte/neonize)**: Biblioteca Python para conexão nativa com o WhatsApp Web.
- **[Alwaysdata](https://www.alwaysdata.com/)**: Infraestrutura gratuita de alta qualidade.

---

## 📄 Licença

Este projeto é licenciado sob a **Licença MIT**.

Feito com 💜 por [Kauã Ferreira](https://www.instagram.com/kauafpss_/).
