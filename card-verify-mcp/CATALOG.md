# Obot Catalog Entry（UVX + Git，发布时覆盖写入）

## Name
证照鉴伪

## Short Description
根据图片 URL 核验行驶证等证照，调用 id-vision cardVerify 接口。

## Description
根据证照图片 URL 做鉴伪/识别，适合行驶证等现场核验场景。

## Server Tenancy / Type
Single-tenant

## Runtime（UVX + Git）
- Runtime: UVX
- Package: `git+https://github.com/zxh258147/my-obot-skills.git#subdirectory=card-verify-mcp`
- Command: `obot-card-verify-mcp`

不要开 OAuth。Type 不要选 Multi-tenant。PyPI 备用包名：`obot-card-verify-mcp==0.1.3`

## Obot 环境变量
- CARD_VERIFY_APP_ID（必填）
- CARD_VERIFY_API_KEY（必填，敏感）
- CARD_VERIFY_BASE_URL（可选）
