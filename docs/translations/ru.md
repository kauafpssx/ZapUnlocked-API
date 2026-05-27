# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/ru.svg" width="30"> Что такое [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)?

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** — это решение для автоматизации WhatsApp на **Python** и **[Neonize](https://github.com/krypton-byte/neonize)**.

---

## 🛤️ Основные Маршруты

### 📨 Отправка

- `POST /send`, `/send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 Интерактив

- `POST /send_wbuttons`, `/messages/send-option-list`, `/messages/send-poll`

### 🔍 Управление

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

---

# 🛠️ Установка и Хостинг

## 💻 Локально

1. `git clone`
2. `scripts\install.bat` (Win) или `bash scripts/install.sh` (Linux)
3. Настройка `.env`
4. `scripts\run.bat` (Win) или `bash scripts/run.sh` (Linux)

---

## ☁️ Хостинг: Alwaysdata (Бесплатно 24/7)

| Ресурс   | Бесплатно    |
| :------- | :----------- |
| Хранение | **1 GB SSD** |
| RAM      | **256 MB**   |
| Аптайм   | **24/7**     |

👉 **[Руководство Alwaysdata](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## ❤️ Благодарности

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
