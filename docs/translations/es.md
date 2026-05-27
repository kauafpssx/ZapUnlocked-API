# 🚀 [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io) 📲✨

![ZapUnlocked-API Banner](https://github.com/zKauaFerreira/ZapUnlocked-API/raw/refs/heads/documentation/images/hero-dark.svg)

🌐 [Leia em Português (BR)](https://github.com/zKauaFerreira/ZapUnlocked-API/blob/main/README.md)

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/es.svg" width="30"> ¿Qué es [ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)?

**[ZapUnlocked-API](https://zapdocs.kauafpss.qzz.io)** es una solución profesional, **100% gratuita y de código abierto**, diseñada para transformar WhatsApp en una poderosa herramienta de automatización. Construida en **Python** con **[Neonize](https://github.com/krypton-byte/neonize)** como motor de conexión, esta API ofrece una interfaz REST sencilla (FastAPI) para gestionar sesiones, enviar medios complejos y crear interacciones inteligentes sin necesidad de una base de datos pesada.

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

1. **Clonar**: `git clone https://github.com/zKauaFerreira/ZapUnlocked-API.git`
2. **Dependencias**:
   - Windows: `scripts\install.bat`
   - Linux: `bash scripts/install.sh`
3. **Configurar**: `cp .env.example .env`
4. **Ejecutar**: `scripts\run.bat` o `bash scripts/run.sh`

---

## ☁️ Hospedaje: Alwaysdata (Gratis 24/7)

### Recursos del Plan Free

| Recurso        | Disponible   |
| :------------- | :----------- |
| Almacenamiento | **1 GB SSD** |
| RAM            | **256 MB**   |
| Uptime         | **24/7**     |

👉 **[Guía de configuración en Alwaysdata](https://zapdocs.kauafpss.qzz.io/essentials/quickstart)**

---

## 🔐 Autenticación (Login)

Conecta tu WhatsApp:

```text
https://tu-slug.alwaysdata.net/qr?API_KEY=TU_CLAVE
```

---

## 📖 Documentación Oficial

👉 **[Accede a la Documentación Oficial](https://zapdocs.kauafpss.qzz.io)**

---

## ❤️ Créditos

- **[Neonize](https://github.com/krypton-byte/neonize)** - **[Alwaysdata](https://www.alwaysdata.com/)**.

---

## 📄 Licencia

MIT License.

Hecho con 💜 por [Kauã Ferreira](https://www.instagram.com/kauafpss_/).
