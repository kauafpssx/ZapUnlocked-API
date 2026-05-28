# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/blob/documentation/images/banner/dark.png?raw=true)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/ru.svg" width="30"> Что такое [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)?

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** — это решение для автоматизации WhatsApp на **Python** и **[Neonize](https://github.com/krypton-byte/neonize)**.

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

1. `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. `scripts\install\install.bat` (Win) или `bash scripts/install/install.sh` (Linux)
3. `bash scripts/generate-env/generate-env.sh` — автоматически создаёт `.env`
4. `scripts\run\run.bat` (Win) или `bash scripts/run/run.sh` (Linux)

---

## ☁️ Хостинг: Alwaysdata (Бесплатно 24/7)

| Ресурс   | Бесплатно    |
| :------- | :----------- |
| Хранение | **1 GB SSD** |
| RAM      | **256 MB**   |
| Аптайм   | **24/7**     |

### Шаги деплоя:

1. Создать аккаунт на [Alwaysdata.com](https://www.alwaysdata.com/) — план **Free**.
2. Открыть SSH-терминал: **Remote access › SSH**.
3. Клонировать и установить:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. Сгенерировать `.env`:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. Настроить Service: **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. **URL доступа**: `http://services-[пользователь].alwaysdata.net:8300/`
   > Открывайте прямо в браузере. *(Необязательно)* Для использования собственного домена настройте **Reverse Proxy** в **Web › Sites › Add a site**, указав `http://[пользователь].alwaysdata.net`.

---

## 🔐 Аутентификация

```text
http://services-[пользователь].alwaysdata.net:8300/qr?API_KEY=YOUR_SECRET_KEY
```

---

## ❤️ Благодарности

**[Neonize](https://github.com/krypton-byte/neonize)** & **[Alwaysdata](https://www.alwaysdata.com/)**.
