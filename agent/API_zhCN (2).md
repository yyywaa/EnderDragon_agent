## API 文档

© 2026 caffeine-Ink

适用版本: coffeeroom `v1.13`

基础 URL: `https://room.caffeine.ink`

鉴权方式: `Session Cookie` (HttpOnly)

<br>

### 目录

验证模块

1. `POST /api/signup/check-username`
2. `POST /api/login`
3. `POST /api/logout`

用户模块

4. `GET /api/user`
5. `GET /api/tokens`
6. `POST /api/tokens`
7. `DELETE /api/tokens`
8. `GET /api/sessions`
9. `DELETE /api/sessions`

消息模块

10. `GET /api/online-users`
11. `GET /api/room/:room/history`
12. `GET /api/room/:room/export`

WebSocket: `/websocket/:room`

<br>

### 验证模块

**源码: `src/routes/auth.ts`**

#### 1. `POST /api/signup/check-username`

摘要: 检查用户名是否可用。

鉴权: 无 (公开)

请求类型: `application/x-www-form-urlencoded` 或 `multipart/form-data`

参数:
- username: `string`, e.g. `"flat_white"`

响应:

```json
{ "success": true, "message": "valid" }
```

#### 2. `POST /api/login`

摘要: 登录。

鉴权: 无 (公开)

请求类型: `application/x-www-form-urlencoded` 或 `multipart/form-data`

参数:
- username: `string`, e.g. `"flat_white"`
- access_token: `string`, e.g. `"AT-e0e081aea4714b139526b28f629faeab"`

响应头:

```
[content-encoding]: gzip
[content-type]: application/json
[set-cookie]: session=eyJhbGciOiJIUzI1NiJ9.eyJ1aWQiOiIwMjAxOCIsInVzZXJuYW1lIjoiZmxhdF93aGl0ZSIsInJvbGUiOiJ1c2VyIiwic2Vzc2lvbklkIjoiMDJmODk5ZDEtZTA3Mi00ZGYyLWE0NDgtZjc5NDkwYTgwMjMyIiwiaWF0IjoxNzcwMDAwMDAwLCJleHAiOjE3NzAwMDAwMDB9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c; Max-Age=7776000; Path=/; HttpOnly; SameSite=Lax
[transfer-encoding]: chunked
```

响应体:

```json
{ "success": true, "message": "login successful" }
```

注: 用户名-密码登录需要提交 Turnstile 人机检查响应, 自动程序请使用 AT 登录。使用 AT 登录可取得 90 天有效期的 session cookie, 你可以设计程序完成自动续签 (在到期前自动创建新的 AT 并换取新的 session cookie)。

#### 3. `POST /api/logout`

摘要: 结束当前 session。

鉴权: `Session Cookie`

响应: `Logged out` (plain text)

<br>

### 用户模块

**源码: `src/routes/user.ts`**

#### 4. `GET /api/user`

摘要: 获取当前用户的个人资料。

鉴权: `Session Cookie`

响应:

```json
{
    "uid": "02018",
    "username": "flat_white",
    "role": "user",
    "signup_date": 1700000000000,
    "email": "flatwhite@example.com",
    "email_verified": 1,
    "two_factor_enabled": 0
}
```

#### 5. `GET /api/tokens`

摘要: 列出当前用户创建的 Access Tokens。

鉴权: `Session Cookie`

响应:

```json
{
    "success": true,
    "tokens": [
        {
            "id": 67,
            "label": "Neko Bot",
            "created_at": 1700000000000,
        }
    ]
}
```

#### 6. `POST /api/tokens`

摘要: 创建一个新的 Access Token (用于自动程序登录)。

鉴权: `Session Cookie`

请求类型: `application/x-www-form-urlencoded` 或 `multipart/form-data`

参数:
- label: `string`, e.g. `"Neko Bot"` (默认 `"New Token"`)

响应:

```json
{
    "success": true,
    "token": "AT-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
}
```

注: Access Token 用完即焚, 最多共存 3 个, 如已有 3 个未使用的 AT 则无法继续创建。

#### 7. `DELETE /api/tokens`

摘要: 删除指定的 Access Token。

鉴权: `Session Cookie`

参数:
- id: `integer` (查询参数), e.g. `?id=67`

响应:

```json
{ "success": true }
```

#### 8. `GET /api/sessions`

摘要: 列出当前活跃的登录会话。

鉴权: `Session Cookie`

响应:

```json
{
    "success": true,
    "sessions": [
        {
            "id": "02f899d1-e072-4df2-a448-f79490a80232",
            "uid": "02018",
            "ip": "127.0.0.1",
            "user_agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; zh-cn) AppleWebKit/533.21.1 (KHTML, like Gecko) Version/5.0.5 Safari/533.21.1",
            "created_at": 1771854934000,
            "expires_at": 1779630934000,
            "is_current": true
        }
    ]
}
```

#### 9. `DELETE /api/sessions`

摘要: 结束指定会话 (踢下线)。

鉴权: `Session Cookie`

参数:
- id: `string` (查询参数), e.g. `?id=02f899d1-e072-4df2-a448-f79490a80232`

响应:

```json
{ "success": true }
```

<br>

### 消息模块 

**源码: `src/routes/chat.ts`**

#### 10. `GET /api/online-users`

摘要: 获取所有房间的在线用户聚合列表。

鉴权: `Session Cookie`

响应:

```json
{
    "success": true,
    "users": [
        {
            "username": "flat_white",
            "uid": "02018",
            "channel": "general"
        },
        {
            "username": "caffeine",
            "uid": "01001",
            "channel": "debug"
        }
    ]
}
```

#### 11. `GET /api/room/:room/history`

摘要: 获取指定房间的 20条 历史消息。

鉴权: `Session Cookie`

参数:
- room: `string` (路径参数), e.g. `"general"`
- cursor: `string` (查询参数), e.g. `?cursor=msg-1700000000000-abcde` (可选, 返回此消息之前的 20 条, 不包含此消息)

响应:

```json
{
    "success": true,
    "messages": [
        {
            "msg_id": "msg-1700000000000-abcde",
            "text": "history message",
            "sender_username": "flat_white",
            "sender_uid": "02018",
            "timestamp": 1700000000000
        }
    ]
}
```

#### 12. `GET /api/room/:room/export`

摘要: 导出指定房间的聊天记录。

鉴权: `Session Cookie`

参数:
- room: `string` (路径参数), e.g. `"general"`
- limit: `string` (查询参数), e.g. `?limit=100` 或 `?limit=all`

响应:

```json
{
    "success": true,
    "messages": [
        {
            "msg_id": "msg-1700000000000-abcde",
            "text": "history message 1",
            "sender_username": "flat_white",
            "sender_uid": "02018",
            "timestamp": 1700000000000
        },
        {
            "msg_id": "msg-1700000010000-abcde",
            "text": "history message 2",
            "sender_username": "flat_white",
            "sender_uid": "02018",
            "timestamp": 1700000010000
        }
    ]
}
```

<br>

### WebSocket

#### WebSocket: `/websocket/:room`

**源码: `src/routes/chat.ts`, `src/do/chat-room.ts`**

摘要: WebSocket 连接端点。

鉴权: `Session Cookie` (Cookie 必须包含在握手请求 Header 中)

协议: `wss://`

参数:
- room: `string` (路径参数), e.g. `"general"`

客户端至服务端:

- 发送消息: 直接发送纯文本字符串。 e.g. `"I drank a cup of coffee."`
- 实用命令与排版:
    - `/help`: 获取帮助
    - `/del <msg-id>`: 软删除自己的消息
    - `<br>`: 换行

注: `/save` 命令逻辑是在前端实现的, 无法在自动程序中使用, 请参考`GET /api/room/:room/export`。

服务端至客户端:

- 标准消息对象:

```json
{
    "msg_id": "msg-1700000000000-abcde",
    "text": "I drank a cup of coffee.",
    "sender_username": "flat_white",
    "sender_uid": "02018",
    "channel": "general",
    "timestamp": 1700000000000
}
```

- 系统通知 & 命令反馈 (无 `msg_id`, `channel` 键值对, 有时也无 `sender_uid`):

```json
{
    "sender_username": "system",
    "sender_uid": "00001",
    "text": "message msg-1760000000000-abcde (hello) from 2025-10-09T08:53:20.000Z was deleted.",
    "timestamp": 1770000000000
}
```

备注: WebSocket 连接成功之后, 服务端会立刻推送最近 50 条消息, 按从旧到新排列。

<br>