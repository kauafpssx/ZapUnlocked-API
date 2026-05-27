# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/cn.svg" width="30"> 什么是 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)？

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** 是基于 **Python** 和 **[Neonize](https://github.com/krypton-byte/neonize)** 构建的专业 WhatsApp 自动化解决方案。

---

## 🛤️ 主要路由

### 📨 发送消息

- `POST /send`, `/send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 互动消息

- `POST /send_wbuttons`, `/messages/send-option-list`, `/messages/send-poll`

### 🔍 管理与查询

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

---

# 🛠️ 安装与托管

## 💻 本地安装

1. `git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git`
2. 运行 `scripts\install.bat` (Win) 或 `bash scripts/install.sh` (Linux)
3. `cp .env.example .env`
4. 运行 `scripts\run.bat` 或 `bash scripts/run.sh`

---

## ☁️ 托管: Alwaysdata (免费 24/7)

| 资源 | 免费版       |
| :--- | :----------- |
| 存储 | **1 GB SSD** |
| 内存 | **256 MB**   |
| 在线 | **24/7**     |

👉 **[Alwaysdata 配置指南](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## ❤️ 致谢

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
