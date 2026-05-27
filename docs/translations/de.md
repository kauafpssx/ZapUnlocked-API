# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/de.svg" width="30"> Was ist [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)?

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** ist eine professionelle, **100% kostenlose** Automatisierungslösung für WhatsApp. Gebaut in **Python** mit **[Neonize](https://github.com/krypton-byte/neonize)**.

---

## 🛤️ Routen

### 📨 Senden

- `POST /send`, `/send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 Interaktiv

- `POST /send_wbuttons`, `/messages/send-option-list`, `/messages/send-poll`

### 🔍 Verwaltung

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

---

# 🛠️ Installation & Hosting

## 💻 Lokal

1. `git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git`
2. `scripts\install.bat` (Win) oder `bash scripts/install.sh` (Linux)
3. `cp .env.example .env`
4. `scripts\run.bat` oder `bash scripts/run.sh`

---

## ☁️ Hosting: Alwaysdata (Kostenlos 24/7)

| Ressource | Free         |
| :-------- | :----------- |
| Speicher  | **1 GB SSD** |
| RAM       | **256 MB**   |
| Online    | **24/7**     |

👉 **[Alwaysdata Guide](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## 🔐 Login

```text
https://dein-slug.alwaysdata.net/qr?API_KEY=DEIN_KEY
```

---

## ❤️ Credits

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
