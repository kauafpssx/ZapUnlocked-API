# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/jp.svg" width="30"> [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) とは？

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** は、**Python** と **[Neonize](https://github.com/krypton-byte/neonize)** を使用した WhatsApp 自動化ソリューションです。

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

1. `git clone`
2. `scripts\install.bat` (Win) または `bash scripts/install.sh` (Linux)
3. `.env` の設定
4. 実行

---

## ☁️ ホスティング: Alwaysdata (無料 24/7)

| リソース   | 無料版       |
| :--------- | :----------- |
| ストレージ | **1 GB SSD** |
| RAM        | **256 MB**   |
| 稼働時間   | **24/7**     |

👉 **[Alwaysdata セットアップガイド](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## ❤️ クレジット

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
