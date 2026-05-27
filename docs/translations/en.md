# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

<p align="center">
  <img src="https://img.shields.io/github/stars/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Stars">
  <img src="https://img.shields.io/github/forks/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Forks">
  <img src="https://img.shields.io/github/repo-size/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="Repo Size">
  <img src="https://img.shields.io/github/license/zKauaFerreira/ZapUnlocked-API?style=for-the-badge&logo=github&color=30A3E6" alt="License">
</p>

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/us.svg" width="30"> What is [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)?

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** is a professional, **100% free and open-source** solution designed to transform WhatsApp into a powerful automation tool. Built in **Python** with **[Neonize](https://github.com/krypton-byte/neonize)** as the connection engine, this API provides a simple REST interface (FastAPI) for managing sessions, sending complex media, and creating intelligent interactions without requiring a heavy database.

> [!TIP]
> Perfect for developers seeking agility in integrating bots, notifications, and automated customer service systems.

---

## 🚀 Key Features

- **Stateless Buttons**: Create interactive flows without a database, using encrypted webhooks.
- **QR-less Pairing**: Connect via numeric code, ideal for headless servers or environments without cameras.
- **Automatic Audio Conversion**: Send audio that appears as "recorded just now" (PTT) natively on iOS and Android.
- **Smart Media Queue**: Automatic management to prevent excessive memory consumption.
- **Dynamic Placeholders**: Personalize messages and webhooks with variables like `{{name}}`, `{{day}}`, and `{{phone}}`.

---

## 🛤️ Main Routes

### 📨 Sending Messages

- `POST /send` - Send Text Message / Reply
- `POST /send_image` - Send Image
- `POST /send_video` - Send Video (supports GIF and PTV)
- `POST /send_audio` - Send Audio (with automatic PTT conversion)
- `POST /send_document` - Send Document
- `POST /send_sticker` - Send Sticker
- `POST /send_reaction` - Send Reaction with Emoji
- `POST /send_location` - Send Location
- `POST /send_contact` / `POST /send_contacts` - Send Contact(s)
- `POST /send_link` - Send Link with Preview
- `POST /messages/delete` - Delete Message
- `POST /messages/read` - Mark as Read
- `POST /messages/edit` - Edit Sent Message

### 🔘 Interactive Messages

- `POST /send_wbuttons` - Send Buttons (List, Action, OTP, PIX)
- `POST /messages/send-option-list` - Send Option List
- `POST /messages/send-poll` - Send Poll
- `POST /messages/send-poll-vote` - Vote on Poll

### 🔍 Queries and Management

- `POST /contacts/info` - Detailed Contact Information
- `POST /management/fetch_messages` - Fetch Message History
- `POST /management/recent_contacts` - List Recent Chats
- `GET /management/memory` - Memory Usage Status
- `GET /management/volume_stats` - Check Disk Usage
- `GET /management/database/status` - DB Status and Stats
- `POST /management/database/cleanup` - Manual DB Cleanup

### 🔗 Connection and Session

- `GET /status` - Connection and Session Status
- `GET /qr` - View Interactive QR Code
- `GET /qr/image` - Get QR Code Image (Base64)
- `POST /qr/pair` - Generate Numeric Pairing Code
- `POST /qr/logout` - Disconnect and Reset Session

### 📡 Webhooks (CRUD)

- `POST /webhooks` - Create Named Webhook
- `GET /webhooks` - List All Webhooks
- `PUT /webhooks/{name}` - Edit Webhook
- `DELETE /webhooks/{name}` - Remove Webhook
- `POST /webhooks/{name}/toggle` - Enable/Disable
- `POST /webhooks/{name}/test` - Test Webhook
- `GET /webhooks/events` - List Event Types (20 types)

### ⚙️ Profile and Privacy

- `POST /settings/profile` - Change Bot Name and Photo
- `POST /settings/privacy` - Adjust Privacy (Last seen, etc.)
- `POST /settings/block` - Block/Unblock Contact

---

# 🛠️ Installation and Hosting

> Get your professional WhatsApp API up and running in less than 5 minutes with **ZapUnlocked-API**.

## 💻 Local Installation (Windows / Linux / macOS)

Ideal for development, testing, or running on your own server.

1. **Clone the Repository**

   ```bash
   git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git
   cd ZapUnlocked-API
   ```

2. **Install Dependencies**
   Run the automatic installer for your system:
   - **Windows**: `scripts\install.bat`
   - **Linux/macOS**: `bash scripts/install.sh`

3. **Configure the Environment**
   Copy `.env.example` and set your variables:

   ```bash
   cp .env.example .env
   ```

   | Variable          | Description                                  |
   | :---------------- | :------------------------------------------- |
   | `API_KEY`         | Password for authentication on all endpoints |
   | `INTERNAL_SECRET` | Token to validate webhook signatures         |

4. **Run the API**
   - **Windows**: `scripts\run.bat`
   - **Linux/macOS**: `bash scripts/run.sh`

---

## ☁️ Hosting: Alwaysdata (Free 24/7)

**Alwaysdata** is the recommended option for hosting the API stably and for free without needing to keep a computer on.

### Free Plan Features

| Resource | Available on Free     |
| :------- | :-------------------- |
| Storage  | **1 GB SSD**          |
| RAM      | **256 MB**            |
| CPU      | **1/4 vCPU**          |
| Backup   | **3 days** automatic  |
| Uptime   | **24/7** via Services |

### Deployment Steps:

1. **Fork the Repository**: Fork the [Official Repository](https://github.com/zKauaFerreira/ZapUnlocked-API) to your GitHub account.
2. **Create your Account**: Access [Alwaysdata.com](https://www.alwaysdata.com/) and choose the **Free** plan.
3. **Access the Web Terminal**: In the panel, go to **Remote access › SSH** and access the provided SSH host.
4. **Install the API**: In the SSH terminal, run:
   ```bash
   git clone https://github.com/your-user/ZapUnlocked-API.git
   cd ZapUnlocked-API
   bash install.sh
   ```
5. **Configure the Service (24/7)**: In the Alwaysdata panel, go to **Web › Services** and add a new service:
   - **Command**: `python main.py`
   - **Working directory**: `/home/[user]/ZapUnlocked-API`

---

## 🔐 Authentication (Login)

After deployment, connect your WhatsApp account by accessing in your browser:

```text
https://your-slug.alwaysdata.net/qr?API_KEY=YOUR_SECRET_PASSWORD
```

---

## 📖 Official Documentation

For detailed technical documentation, code examples, and an interactive playground, visit our official website.

👉 **[Access the Official Documentation](https://zapdocs.kauafpss.qzz.io)**

> ### Documentation Index
>
> Fetch the complete documentation index at: https://zapdocs.kauafpss.qzz.io/llms.txt
> Use this file to discover all available pages before exploring further.

---

## ❤️ Credits & Acknowledgments

- **[Neonize](https://github.com/krypton-byte/neonize)**: Python library for native WhatsApp Web connection.
- **[Alwaysdata](https://www.alwaysdata.com/)**: High-quality free infrastructure.

---

## 📄 License

This project is licensed under the **MIT License**.

Made with 💜 by [Kauã Ferreira](https://www.instagram.com/kauafpss_/).
