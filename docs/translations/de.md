# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/de.svg" width="30"> Was ist [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)?

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** ist eine professionelle, **100% kostenlose** Automatisierungslösung für WhatsApp. Gebaut in **Python** mit **[Neonize](https://github.com/krypton-byte/neonize)**.

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

1. `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. `scripts\install\install.bat` (Win) oder `bash scripts/install/install.sh` (Linux)
3. `bash scripts/generate-env/generate-env.sh` — `.env` automatisch generieren
4. `scripts\run\run.bat` oder `bash scripts/run/run.sh`

---

## ☁️ Hosting: Alwaysdata (Kostenlos 24/7)

| Ressource | Free         |
| :-------- | :----------- |
| Speicher  | **1 GB SSD** |
| RAM       | **256 MB**   |
| Online    | **24/7**     |

### Deploy-Schritte:

1. Konto erstellen auf [Alwaysdata.com](https://www.alwaysdata.com/) — **Free** Plan.
2. SSH-Terminal öffnen: **Remote access › SSH**.
3. Klonen und installieren:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. `.env` generieren:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. Service konfigurieren: **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. Zugriffs-URL: `http://services-[user].alwaysdata.net:8300/`
   > Direkt im Browser aufrufbar, keine zusätzliche Konfiguration nötig.

---

## 🔐 Login

```text
http://services-[user].alwaysdata.net:8300/qr?API_KEY=DEIN_KEY
```

---

## ❤️ Credits

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
