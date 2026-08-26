# Obot Catalog Entry（UVX + Git，直接复制到创建表单）

## Name
证照鉴伪

## Short Description
根据图片 URL 核验行驶证等证照，调用 id-vision cardVerify 接口。

## Description
根据证照图片 URL 做鉴伪/识别，适合行驶证等现场核验场景。

## 功能
- 提交图片 URL，调用 `card_verify`
- 支持证照类型（默认 `VEHICLE_LICENSE`）和正反面（`FRONT` / `BACK`）
- 凭证通过环境变量注入，不写进代码

## 使用前需要
- **App Id**：`CARD_VERIFY_APP_ID`（请求头 `X-App-Id`）
- **API Key**：`CARD_VERIFY_API_KEY`（请求头 `X-Api-Key`）
- **Base URL**（可选）：`CARD_VERIFY_BASE_URL`

## Server Tenancy / Type
Single-tenant

不要选 Multi-tenant。Multi-tenant 会走网关 OAuth，Agent 容易报「需要 OAuth 认证」。本 MCP 不使用 OAuth，鉴伪凭据是环境变量。

## Runtime（UVX + Git）
- Runtime: `UVX`
- Package:

```
git+https://github.com/zxh258147/my-obot-skills.git#subdirectory=card-verify-mcp
```

- Command（若表单有此项）:

```
obot-card-verify-mcp
```

Obot 实际执行：

```
uvx --from git+https://github.com/zxh258147/my-obot-skills.git#subdirectory=card-verify-mcp obot-card-verify-mcp
```

## Obot 环境变量
- CARD_VERIFY_APP_ID（必填，敏感：否）
- CARD_VERIFY_API_KEY（必填，敏感：是）
- CARD_VERIFY_BASE_URL（可选，敏感：否）

## OAuth
不要开 Static OAuth / MCP OAuth。

- 鉴伪接口：`X-App-Id` + `X-Api-Key`，不是 OAuth
- 仓库若是公开 GitHub：UVX 可直接拉代码
- 仓库若是私有：在 Obot **Manage Credentials** 配 GitHub PAT（`repo` 读权限），或服务端设 `GITHUB_AUTH_TOKEN`。这是 Git 克隆凭证，不是给 Agent 的 OAuth
