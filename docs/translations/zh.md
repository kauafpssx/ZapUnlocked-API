# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/cn.svg" width="30"> 什么是 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)？

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** 是基于 **Python** 和 **[Neonize](https://github.com/krypton-byte/neonize)** 构建的专业 WhatsApp 自动化解决方案。

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

1. `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. 运行 `scripts\install\install.bat` (Win) 或 `bash scripts/install/install.sh` (Linux)
3. `bash scripts/generate-env/generate-env.sh` — 自动生成 `.env`
4. 运行 `scripts\run\run.bat` 或 `bash scripts/run/run.sh`

---

## ☁️ 托管: Alwaysdata (免费 24/7)

| 资源 | 免费版       |
| :--- | :----------- |
| 存储 | **1 GB SSD** |
| 内存 | **256 MB**   |
| 在线 | **24/7**     |

### 部署步骤:

1. 在 [Alwaysdata.com](https://www.alwaysdata.com/) 注册账号 — **Free** 计划。
2. 打开 SSH 终端: **Remote access › SSH**。
3. 克隆并安装:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. 生成 `.env`:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. 配置 Service: **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. 内部访问地址: `http://services-[用户名].alwaysdata.net:8300/`

---

## 🔐 登录认证

```text
http://services-[用户名].alwaysdata.net:8300/qr?API_KEY=YOUR_SECRET_KEY
```

---

## ❤️ 致谢

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
