# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/jp.svg" width="30"> [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) とは？

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** は、**Python** と **[Neonize](https://github.com/krypton-byte/neonize)** を使用した WhatsApp 自動化ソリューションです。

---

## 🛤️ 主なルート

### 📨 メッセージ送信

- `POST /send`, `/send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 インタラクティブ

- `POST /send_wbuttons`, `/messages/send-option-list`, `/messages/send-poll`

### 🔍 管理

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

---

# 🛠️ インストールとホスティング

## 💻 ローカル

1. `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. `scripts\install\install.bat` (Win) または `bash scripts/install/install.sh` (Linux)
3. `bash scripts/generate-env/generate-env.sh` — `.env` を自動生成
4. `scripts\run\run.bat` または `bash scripts/run/run.sh`

---

## ☁️ ホスティング: Alwaysdata (無料 24/7)

| リソース   | 無料版       |
| :--------- | :----------- |
| ストレージ | **1 GB SSD** |
| RAM        | **256 MB**   |
| 稼働時間   | **24/7**     |

### デプロイ手順:

1. [Alwaysdata.com](https://www.alwaysdata.com/) でアカウント作成 — **Free** プラン。
2. SSH ターミナルを開く: **Remote access › SSH**。
3. クローンとインストール:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. `.env` を生成:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. Service を設定: **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. アクセス URL: `http://services-[ユーザー].alwaysdata.net:8300/`
   > ブラウザから直接アクセスできます。追加設定は不要です。

---

## 🔐 ログイン

```text
http://services-[ユーザー].alwaysdata.net:8300/qr?API_KEY=YOUR_SECRET_KEY
```

---

## ❤️ クレジット

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
