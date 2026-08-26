# Obot Catalog Entry（发布时覆盖写入，直接复制到创建表单）

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

UVX 包名：`obot-card-verify-mcp==0.1.1`

## Server Tenancy / Type
Multi-tenant

## Runtime
- Runtime: UVX
- Package: `obot-card-verify-mcp==0.1.1`

## Obot 环境变量
- CARD_VERIFY_APP_ID（必填）
- CARD_VERIFY_API_KEY（必填，敏感）
- CARD_VERIFY_BASE_URL（可选）

## 说明
- Type 选 Multi-tenant：所有用户共用同一份 MCP 实例和同一组环境变量。
- 此项保存后不能改，要改必须删除后重建。
