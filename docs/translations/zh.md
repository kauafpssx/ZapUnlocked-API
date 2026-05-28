# 🚀 [ZapUnlocked-API](https://zapunlocked-api.kauafpss.com.br) 📲✨

![ZapUnlocked-API Banner](https://github.com/kauafpssx/ZapUnlocked-API/blob/documentation/images/banner/dark.png?raw=true)

<p align="center">
  <img src="https://img.shields.io/badge/Free%20%26%20Open%20Source-A855F7?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="Free & Open Source">
  <img src="https://img.shields.io/badge/Self%20Hosted-A855F7?style=for-the-badge&logo=docker&logoColor=white" alt="Self Hosted">
  <img src="https://img.shields.io/badge/REST%20API-A855F7?style=for-the-badge&logo=fastapi&logoColor=white" alt="REST API">
  <img src="https://img.shields.io/badge/MIT%20License-A855F7?style=for-the-badge&logo=opensourceinitiative&logoColor=white" alt="MIT License">
  <img src="https://img.shields.io/badge/Python%203.10%2B-A855F7?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.10+">
</p>

<table width="100%">
  <tr>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/en.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/us.svg" width="40" title="English"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/es.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/es.svg" width="40" title="Español"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/fr.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/fr.svg" width="40" title="Français"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/de.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/de.svg" width="40" title="Deutsch"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/ja.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/jp.svg" width="40" title="日本語"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/ru.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/ru.svg" width="40" title="Русский"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/it.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/it.svg" width="40" title="Italiano"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/ar.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/sa.svg" width="40" title="العربية"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/tr.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/tr.svg" width="40" title="Türkçe"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/kr.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/kr.svg" width="40" title="한국어"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/in.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/in.svg" width="40" title="हिन्दी"></a></td>
    <td align="center" valign="middle"><a href="https://github.com/kauafpssx/ZapUnlocked-API/blob/main/docs/translations/nl.md"><img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/nl.svg" width="40" title="Nederlands"></a></td>
  </tr>
</table>

---

## <img src="https://github.com/lipis/flag-icons/raw/refs/heads/main/flags/4x3/cn.svg" width="30"> 什么是 ZapUnlocked-API？

WhatsApp API 市场收取的月费极其高昂：每月数十到数百雷亚尔，并且还有使用限制、按对话收费以及数据经过第三方服务器等问题。**ZapUnlocked-API 就是为了改变这一现状而存在的。**

基于 **Python** 构建，使用 **[Neonize](https://github.com/krypton-byte/neonize)** 作为连接引擎，此 API 提供简单的 REST 接口（FastAPI），用于管理会话、发送复杂媒体和创建智能交互。**无需重型数据库、无需月费、不依赖任何第三方。**

我们的主张建立在**技术卓越**和**开发者独立性**之上。我们相信，强大的工具应该对那些构建自己解决方案的人触手可及。

> [!TIP]
> 非常适合寻求快速集成机器人、通知和自动化服务系统的开发者。**完全免费。**

---

## 🗺️ API 概览

```mermaid
mindmap
  root((📲 ZapUnlocked-API))
    📨 消息
      文本 / 回复
      媒体 📸🎥🎵
      反应 / 位置
      联系人 / 链接
      编辑 / 删除 / 已读
    🔘 交互式
      Stateless 按钮
      选项列表
      投票
    🔍 查询
      联系人信息
      历史记录
      最近聊天
      内存 / 磁盘
      数据库
    🔗 连接
      状态 / SSE
      二维码
      配对码
      登出
    📡 Webhooks
      创建 / 列表
      编辑 / 删除
      启用 / 测试
      20 种事件
    ⚙️ 个人资料与隐私
      名称 / 头像
      最后上线时间
      屏蔽
    🤖 机器人
      AI 标签
      IP 控制
      拒绝来电
      自动已读
    📱 实例
      账户数据
      设备信息
      重命名
    🖥️ 系统
      环境变量
      媒体清理
      自动清理
```

---

## ✨ 特色功能

| 功能 | 描述 |
| :--- | :--- |
| 🧩 **Stateless 按钮** | 使用加密 webhook 创建无需数据库的交互流程 |
| 🔢 **无二维码配对** | 通过数字代码连接 · 适合无 GUI 的服务器 |
| 🎵 **自动音频转换** | 发送显示为本地录制（PTT）的音频 |
| 📦 **智能媒体队列** | 自动管理以防止过度内存消耗 |
| 🏷️ **动态占位符** | 使用 `{{name}}`、`{{day}}、`{{phone}}` 自定义消息和 webhook |

> [!NOTE]
> 所有功能**100% 免费**，并由开源社区维护。

---

## 📋 API 路由

<details>
<summary><b>📨 发送消息</b> · 13 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `POST` | `/send` | 发送文本消息 / 回复 |
| `POST` | `/send_image` | 发送图片 |
| `POST` | `/send_video` | 发送视频（支持 GIF 和 PTV） |
| `POST` | `/send_audio` | 发送音频（自动转换为 PTT） |
| `POST` | `/send_document` | 发送文档 |
| `POST` | `/send_sticker` | 发送贴纸 |
| `POST` | `/send_reaction` | 发送表情反应 |
| `POST` | `/send_location` | 发送位置 |
| `POST` | `/send_contact` | 发送联系人 |
| `POST` | `/send_contacts` | 发送多个联系人 |
| `POST` | `/send_link` | 发送带预览的链接 |
| `POST` | `/messages/delete` | 删除消息 |
| `POST` | `/messages/read` | 标记为已读 |
| `POST` | `/messages/edit` | 编辑已发送消息 |
</details>

<details>
<summary><b>🔘 交互式消息</b> · 4 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `POST` | `/send_wbuttons` | 发送按钮（列表、操作、OTP、PIX） |
| `POST` | `/messages/send-option-list` | 发送选项列表 |
| `POST` | `/messages/send-poll` | 发送投票 |
| `POST` | `/messages/send-poll-vote` | 参与投票 |
</details>

<details>
<summary><b>🔍 查询与管理</b> · 7 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `POST` | `/contacts/info` | 联系人详细信息 |
| `POST` | `/management/fetch_messages` | 获取消息历史 |
| `POST` | `/management/recent_contacts` | 列出最近聊天 |
| `GET` | `/management/memory` | 内存使用状态 |
| `GET` | `/management/volume_stats` | 检查磁盘使用情况 |
| `GET` | `/management/database/status` | 数据库状态与统计 |
| `POST` | `/management/database/cleanup` | 手动清理数据库 |
</details>

<details>
<summary><b>🔗 连接与会话</b> · 8 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `GET` | `/` | 欢迎页面（HTML） |
| `GET` | `/status` | 连接和会话状态 |
| `GET` | `/status/stream` | 实时状态（SSE） |
| `GET` | `/qr` | 查看交互式二维码 |
| `GET` | `/qr/image` | 获取二维码图像（Base64） |
| `POST` | `/qr/pair` | 生成数字配对码 |
| `GET` | `/settings/phone-code/{phone}` | 按号码生成配对码 |
| `POST` | `/qr/logout` | 断开并重置会话 |
</details>

<details>
<summary><b>📡 Webhooks（CRUD）</b> · 7 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `POST` | `/webhooks` | 创建命名的 webhook |
| `GET` | `/webhooks` | 列出所有 webhook |
| `PUT` | `/webhooks/{name}` | 编辑 webhook |
| `DELETE` | `/webhooks/{name}` | 删除 webhook |
| `POST` | `/webhooks/{name}/toggle` | 启用 / 禁用 |
| `POST` | `/webhooks/{name}/test` | 测试 webhook |
| `GET` | `/webhooks/events` | 列出事件类型（20 种） |
</details>

<details>
<summary><b>⚙️ 个人资料与隐私</b> · 3 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `POST` | `/settings/profile` | 更改机器人名称和头像 |
| `POST` | `/settings/privacy` | 调整隐私设置（最后上线时间等） |
| `POST` | `/settings/block` | 屏蔽 / 取消屏蔽联系人 |
</details>

<details>
<summary><b>🤖 机器人设置</b> · 5 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `GET` | `/settings/bot` | 查看机器人设置 |
| `POST` | `/settings/bot` | 更新设置（AI 标签、IP 控制） |
| `PUT` | `/settings/instance/call-reject-auto` | 自动拒绝来电 |
| `PUT` | `/settings/instance/call-reject-message` | 拒绝来电的回复消息 |
| `PUT` | `/settings/instance/auto-read-message` | 自动已读消息 |
</details>

<details>
<summary><b>📱 实例</b> · 3 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `GET` | `/instance/me` | 已连接账户数据 |
| `GET` | `/instance/device` | 设备技术数据 |
| `PUT` | `/instance/update-name` | 重命名实例 |
</details>

<details>
<summary><b>🖥️ 系统</b> · 5 个端点</summary>

| 方法 | 路由 | 描述 |
| :----- | :--- | :-------- |
| `GET` | `/system/env` | 查看环境变量 |
| `PUT` | `/system/env` | 更新环境变量 |
| `POST` | `/system/cleanup/force` | 强制清理临时媒体 |
| `GET` | `/system/cleanup/settings` | 查看自动清理设置 |
| `PUT` | `/system/cleanup/settings` | 更新自动清理间隔 |
</details>

> **共计: 56 个端点** · 用于 WhatsApp 自动化的完整 REST API。

---

## 🛠️ 安装与托管

> 使用 **ZapUnlocked-API** 在 **5 分钟**内启动您的专业 WhatsApp API。

### 💻 本地安装

适合开发、测试或在自有服务器上运行。

```mermaid
flowchart LR
  A[Clone] --> B[Install]
  B --> C[Config .env]
  C --> D[Run 🚀]
  D --> E[Config Account 🔗]
  E --> F[Production! ⚡]
```

**1. 克隆仓库**

```bash
git clone https://github.com/kauafpssx/ZapUnlocked-API.git
cd ZapUnlocked-API
```

**2. 安装依赖**

| 系统 | 命令 |
| :------ | :------ |
| 🪟 Windows | `scripts\install\install.bat` |
| 🐧 Linux / macOS | `bash scripts/install/install.sh` |

**3. 配置环境**

| 系统 | 命令 |
| :------ | :------ |
| 🪟 Windows | `scripts\generate-env\generate-env.bat` |
| 🐧 Linux / macOS | `bash scripts/generate-env/generate-env.sh` |

| 变量 | 描述 |
| :------- | :-------- |
| `API_KEY` | 所有端点的认证密码 |
| `INTERNAL_SECRET` | 用于验证 webhook 签名的令牌 |
| `PORT` | API 端口（默认：`8300`） |

**4. 运行 API**

| 系统 | 命令 |
| :------ | :------ |
| 🪟 Windows | `scripts\run\run.bat` |
| 🐧 Linux / macOS | `bash scripts/run/run.sh` |

---

### ☁️ 托管: Alwaysdata（免费 24/7）

**Alwaysdata** 是推荐的托管选项，可稳定免费地运行 API，无需维护自有服务器。

#### 📊 免费计划资源

| 资源 | 免费版可用 |
| :------ | :----------------- |
| 💾 存储 | **1 GB SSD** |
| 🧠 内存 | **256 MB** |
| ⚡ CPU | **1/4 vCPU** |
| 🔄 备份 | **3 天**自动备份 |
| 📡 在线时间 | **24/7** 通过 Services |

#### 👣 部署步骤

**1.** 在 [Alwaysdata.com](https://www.alwaysdata.com/) 注册账号 · **Free** 计划。

**2.** 通过 SSH 访问: `https://ssh-[usuario].alwaysdata.net`。

**3.** 克隆并安装:

```bash
git clone https://github.com/kauafpssx/ZapUnlocked-API.git ~/ZapUnlocked-API
cd ~/ZapUnlocked-API
bash scripts/install/install.sh
```

**4.** 生成 `.env`:

```bash
bash scripts/generate-env/generate-env.sh
```

**5.** 配置服务（24/7）: **Advanced › Services › Add a service**:

| 字段 | 值 |
| :---- | :---- |
| **Name** | `ZapUnlocked-API` |
| **Command** | `python3 main.py` |
| **Working directory** | `ZapUnlocked-API` |
| **Environment variables** | `PORT=8300` |

**6.** 访问地址:

```
http://services-[usuario].alwaysdata.net:8300/
```

> [!TIP]
> 该 URL 外部可直接访问。*（可选）* 如需使用自定义域名，在 **Web › Sites › Add a site** 中配置 **Reverse Proxy**，指向 `http://[usuario].alwaysdata.net`。

---

## 🔐 认证（登录）

部署后，在浏览器中访问以下地址以连接您的 WhatsApp 账户:

```text
http://services-[usuario].alwaysdata.net:8300/qr?API_KEY=SUA_SENHA_SECRETA
```

---

## 📖 官方文档

<p align="center">
  👉 <a href="https://zapunlocked-api.kauafpss.com.br"><strong>zapunlocked-api.kauafpss.com.br</strong></a>
</p>

有关详细技术文档、代码示例和交互式游乐场，请访问我们的官方网站。

> [!TIP]
> 使用 **LLMs.txt** 作为 AI 索引: [`zapunlocked-api.kauafpss.com.br/llms.txt`](https://zapunlocked-api.kauafpss.com.br/llms.txt)。在浏览前发现所有页面。

---

## ❤️ 致谢

| 项目 | 描述 |
| :------ | :-------- |
| [![Neonize](https://img.shields.io/badge/Neonize-A855F7?style=for-the-badge&logo=python&logoColor=white)](https://github.com/krypton-byte/neonize) | 用于原生连接 WhatsApp Web 的 Python 库 |
| [![whatsmeow](https://img.shields.io/badge/whatsmeow-A855F7?style=for-the-badge&logo=go&logoColor=white)](https://github.com/tulir/whatsmeow) | Neonize 的基础 Go 库 · 连接的核心 |
| [![Alwaysdata](https://img.shields.io/badge/Alwaysdata-A855F7?style=for-the-badge&logo=alwaysdata&logoColor=white)](https://www.alwaysdata.com/) | 高质量的免费基础设施 |

---

## 📄 许可证

本项目基于 **MIT 许可证** 授权。

<p align="center">
  由 <a href="https://www.instagram.com/kauafpss_/">Kauã Ferreira</a> 用 💜 制作
</p>

