# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/fr.svg" width="30"> Qu'est-ce que [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) ?

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** est une solution professionnelle, **100% gratuite et open-source**, conçue pour transformer WhatsApp en un puissant outil d'automatisation. Construite en **Python** avec **[Neonize](https://github.com/krypton-byte/neonize)** comme moteur de connexion.

---

## 🛤️ Principales Routes

### 📨 Envoi

- `POST /send`, `/send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 Interactif

- `POST /send_wbuttons`, `/messages/send-option-list`, `/messages/send-poll`

### 🔍 Gestion

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

---

# 🛠️ Installation et Hébergement

## 💻 Installation Locale

1. `git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git`
2. `bash scripts/install.sh` (Linux/macOS) ou `scripts\install.bat` (Windows)
3. `cp .env.example .env`
4. `bash scripts/run.sh` ou `scripts\run.bat`

---

## ☁️ Hébergement : Alwaysdata (Gratuit 24/7)

| Ressource | Free         |
| :-------- | :----------- |
| Stockage  | **1 Go SSD** |
| RAM       | **256 Mo**   |
| Uptime    | **24/7**     |

👉 **[Guide Alwaysdata](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## 🔐 Authentification

```text
https://votre-slug.alwaysdata.net/qr?API_KEY=VOTRE_CLE
```

---

## 📖 Documentation

👉 **[Documentation Officielle](https://zapdocs.kauafpss.qzz.io)**

---

## ❤️ Crédits

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
