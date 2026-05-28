# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/fr.svg" width="30"> Qu'est-ce que [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) ?

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** est une solution professionnelle, **100% gratuite et open-source**, conçue pour transformer WhatsApp en un puissant outil d'automatisation. Construite en **Python** avec **[Neonize](https://github.com/krypton-byte/neonize)** comme moteur de connexion.

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

1. `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. `bash scripts/install/install.sh` (Linux/macOS) ou `scripts\install\install.bat` (Windows)
3. `bash scripts/generate-env/generate-env.sh` — génère `.env` automatiquement
4. `bash scripts/run/run.sh` ou `scripts\run\run.bat`

---

## ☁️ Hébergement : Alwaysdata (Gratuit 24/7)

| Ressource | Free         |
| :-------- | :----------- |
| Stockage  | **1 Go SSD** |
| RAM       | **256 Mo**   |
| Uptime    | **24/7**     |

### Étapes de déploiement :

1. Créer un compte sur [Alwaysdata.com](https://www.alwaysdata.com/) — plan **Free**.
2. Ouvrir le terminal SSH : **Remote access › SSH**.
3. Cloner et installer :
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. Générer `.env` :
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. Configurer le Service : **Advanced › Services › Add a service** :
   - **Name** : `ZapUnlocked-API`
   - **Command** : `python3 main.py`
   - **Working directory** : `ZapUnlocked-API`
   - **Environment variables** : `PORT=8300`
6. URL d'accès : `http://services-[utilisateur].alwaysdata.net:8300/`
   > Accédez directement depuis votre navigateur, sans configuration supplémentaire.

---

## 🔐 Authentification

```text
http://services-[utilisateur].alwaysdata.net:8300/qr?API_KEY=VOTRE_CLE
```

---

## 📖 Documentation

👉 **[Documentation Officielle](https://zapunlocked-api.kauafpss.com.br)**

---

## ❤️ Crédits

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
