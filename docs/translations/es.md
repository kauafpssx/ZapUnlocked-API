# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/kauafpssx/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/es.svg" width="30"> ¿Qué es [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)?

**[ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br)** es una solución profesional, **100% gratuita y de código abierto**, diseñada para transformar WhatsApp en una poderosa herramienta de automatización. Construida en **Python** con **[Neonize](https://github.com/krypton-byte/neonize)** como motor de conexión, esta API ofrece una interfaz REST sencilla (FastAPI) para gestionar sesiones, enviar medios complejos y crear interacciones inteligentes sin necesidad de una base de datos pesada.

> [!TIP]
> Perfecto para desarrolladores que buscan agilidad en la integración de bots, notificaciones y sistemas de atención automatizada.

---

## 🚀 Funcionalidades Destacadas

- **Botones Stateless**: Crea flujos interactivos sin base de datos, con webhooks encriptados.
- **Emparejamiento sin QR**: Conecta mediante código numérico, ideal para servidores sin interfaz gráfica.
- **Conversão Automática de Áudio**: Envía audios que aparecen como grabados al momento (PTT) nativamente en iOS y Android.
- **Cola de Medios Inteligente**: Gestión automática para evitar consumo excesivo de memoria.
- **Placeholders Dinâmicos**: Personaliza mensajes y webhooks con variables como `{{name}}`, `{{day}}` y `{{phone}}`.

---

## 🛤️ Principales Rutas

### 📨 Envío de Mensajes

- `POST /send` - Texto / Responder
- `POST /send_image`, `/send_video`, `/send_audio`, `/send_document`, `/send_sticker`
- `POST /send_reaction`, `/send_location`, `/send_contact`, `/send_link`
- `POST /messages/delete`, `/messages/read`, `/messages/edit`

### 🔘 Mensajes Interactivos

- `POST /send_wbuttons` - Botones (Lista, Acción, OTP, PIX)
- `POST /messages/send-option-list`, `/messages/send-poll`, `/messages/send-poll-vote`

### 🔍 Consultas y Gestión

- `POST /contacts/info`, `/management/fetch_messages`, `/management/recent_contacts`
- `GET /management/memory`, `/management/volume_stats`, `/management/database/status`

### 📡 Webhooks (CRUD)

- `POST /webhooks`, `GET /webhooks`, `PUT /webhooks/{name}`, `DELETE /webhooks/{name}`
- `POST /webhooks/{name}/toggle`, `/webhooks/{name}/test`, `GET /webhooks/events`

### 🔗 Conexión y Sesión

- `GET /status`, `/qr`, `/qr/image` · `POST /qr/pair`, `/qr/logout`

---

# 🛠️ Instalación y Hospedaje

## 💻 Instalación Local

1. **Clonar**: `git clone https://github.com/kauafpssx/ZapUnlocked-API.git`
2. **Dependencias**:
   - Windows: `scripts\install\install.bat`
   - Linux: `bash scripts/install/install.sh`
3. **Configurar**: `bash scripts/generate-env/generate-env.sh` — genera `.env` automáticamente
4. **Ejecutar**: `scripts\run\run.bat` o `bash scripts/run/run.sh`

---

## ☁️ Hospedaje: Alwaysdata (Gratis 24/7)

### Recursos del Plan Free

| Recurso        | Disponible   |
| :------------- | :----------- |
| Almacenamiento | **1 GB SSD** |
| RAM            | **256 MB**   |
| Uptime         | **24/7**     |

### Pasos de Deploy:

1. Crear cuenta en [Alwaysdata.com](https://www.alwaysdata.com/) — plan **Free**.
2. Abrir terminal SSH: **Remote access › SSH**.
3. Clonar e instalar:
   ```bash
   git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
   cd ~/ZapUnlocked-API
   bash scripts/install/install.sh
   ```
4. Generar `.env`:
   ```bash
   bash scripts/generate-env/generate-env.sh
   ```
5. Configurar Service: **Advanced › Services › Add a service**:
   - **Name**: `ZapUnlocked-API`
   - **Command**: `python3 main.py`
   - **Working directory**: `ZapUnlocked-API`
   - **Environment variables**: `PORT=8300`
6. URL de Acceso: `http://services-[usuario].alwaysdata.net:8300/`
   > Accede directamente desde tu navegador, sin configuración adicional.

---

## 🔐 Autenticación (Login)

Conecta tu WhatsApp:

```text
http://services-[usuario].alwaysdata.net:8300/qr?API_KEY=TU_CLAVE
```

---

## 📖 Documentación Oficial

👉 **[Accede a la Documentación Oficial](https://zapunlocked-api.kauafpss.com.br)**

---

## ❤️ Créditos

- **[Neonize](https://github.com/krypton-byte/neonize)** - **[Alwaysdata](https://www.alwaysdata.com/)**.

---

## 📄 Licencia

MIT License.

Hecho con 💜 por [Kauã Ferreira](https://www.instagram.com/kauafpss_/).
