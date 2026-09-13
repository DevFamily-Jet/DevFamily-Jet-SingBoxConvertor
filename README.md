# Sing-box 订阅转换托管中心 (Cloudflare Worker + KV)

本项目将 Python 版 Sing-box 订阅转换器升级移植到了 **Cloudflare Worker 边缘无服务器架构**，通过 **Cloudflare KV** 实现了「原机场订阅地址」与「客户端固定新订阅地址」的持久化绑定与自动联动更新。

---

## ✨ 核心特性

1. **原地址与新地址永久联动**：
   - 客户端只需填写一次 Worker 生成的永久专属地址（如 `https://your-worker.workers.dev/sub/my-sub`）。
   - 每次客户端更新配置时，Worker 实时从 KV 读取原订阅地址并向机场请求最新节点，动态转换为最新的 Sing-box 1.14/1.15 配置。
   - 机场换域名或更换订阅链接时，**只需在管理界面修改一次原地址，所有终端设备（手机、电脑、软路由）自动同步更新，无需重新导入配置**！
2. **边缘无服务器 & 全球加速**：
   - 依托 Cloudflare 全球 CDN，拉取订阅极速，零服务器维护成本（每天免费 100,000 次请求）。
3. **针对 Sing-box 1.14/1.15 深度优化**：
   - **默认 FakeIP DNS（0ms 本地虚拟解析）**：彻底解决 Cloudflare CDN 优选节点或 WebSocket 节点原生不支持 UDP 转发导致的无网/断网问题。
   - **Windows TUN 优化**：预设 `strict_route: false` 与 `ip_is_private: true` 直连分流，防止 Windows 网卡死锁。
   - **最新规范**：遵循 1.14+ `route.rules` 中的 `action: "sniff"`、`action: "hijack-dns"` 及扁平化 `http_clients` 规范。
4. **多协议与多格式支持**：
   - 协议：VLESS (Reality/Vision)、VMess、Trojan、Shadowsocks、Hysteria 2、TUIC。
   - 格式：Base64 订阅链接流、纯文本 URI 列表、Clash/Mihomo Proxies YAML 格式。
5. **开箱即用可视化后台**：
   - 访问 Worker 根目录（`/`）即可打开现代深色 Web 管理界面，支持在线创建、短链别名绑定、一键复制、修改原地址、删除等操作。

---

## 🚀 部署指南（两种方式，任选其一）

### 方式一：Web 网页端 1 分钟零代码部署（推荐）

1. **登录 Cloudflare**：进入 [Cloudflare Dashboard](https://dash.cloudflare.com/)。
2. **创建 KV 命名空间**：
   - 依次点击左侧菜单：`存储和数据库 (Storage & Databases)` -> `KV`。
   - 点击 **创建命名空间 (Create a Namespace)**，名称填入：`SUB_KV`，点击添加。
3. **创建 Worker**：
   - 依次点击左侧菜单：`计算 (Workers & Pages)` -> `创建应用程序 (Create application)` -> `创建 Worker`。
   - 取一个名字（例如 `singbox-sub`），点击 **部署 (Deploy)**。
4. **绑定 KV 命名空间**：
   - 进入刚创建的 Worker 详情页，点击 **设置 (Settings)** -> **变量 (Variables)** -> 找到 **KV 命名空间绑定 (KV Namespace Bindings)**。
   - 点击 **添加绑定 (Add binding)**：
     - **变量名称 (Variable name)** 严格填入：`SUB_KV`
     - **KV 命名空间** 选择刚才创建的 `SUB_KV`。
   - 点击保存并部署。
5. **粘贴代码**：
   - 点击右上角 **编辑代码 (Edit code)**。
   - 将本项目 `cf-worker/src/index.js` 的**全部代码**复制粘贴进去，覆盖原有的所有内容。
   - 点击右上角 **部署 (Deploy)**。
6. **搞定！** 访问分配的 `https://<你的Worker>.workers.dev` 即可打开管理后台！

---

### 方式二：使用 Wrangler 命令行部署

如果你本地有 Node.js / Wrangler 环境：

```bash
cd cf-worker

# 1. 登录 Cloudflare
npx wrangler login

# 2. 创建 KV 命名空间
npx wrangler kv:namespace create "SUB_KV"
# 将输出的 id 替换填入 wrangler.toml 中的 id = "..."

# 3. 部署到 Cloudflare
npx wrangler deploy
```

---

## 📖 使用接口说明

- **Web 管理界面**：`GET /`
- **客户端订阅地址**：`GET /sub/<你的ID>`
  - 例如：`https://<你的Worker>.workers.dev/sub/mysub`
  - 可选参数：`?version=1.14`（默认 1.14，可选 1.14 或 1.15）、`?tun=false`（关闭 TUN）
- **动态一次性转换链接（不存 KV）**：`GET /convert?url=<原订阅URL>`
