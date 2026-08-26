---
name: doc-verify-weather
description: >
  Use when the user needs a combined field workflow for document image
  verification (证照鉴伪 / cardVerify / vehicle license) and local weather
  lookup. Follow the ordered process: collect inputs, check weather, verify
  the image, then produce a combined work report. Do not skip steps or swap
  the order unless the user explicitly asks to skip weather or skip verify.
compatibility: Requires Obot MCP servers obot-card-verify-mcp and obot-weather-mcp.
license: MIT
---

# 现场证照核验 + 天气作业流程

把 **图片鉴伪** 和 **天气查询** 串成一次现场作业。先看天气是否适合拍照/外勤，再核验证照，最后给出综合结论。

## When to use

- 用户提供行驶证/证照图片 URL，同时问当地天气或能否外勤。
- 用户说「核验证件并看天气」「现场作业」「拍照鉴伪」。
- 需要一份同时包含鉴伪结果和天气建议的报告。

## Required MCP tools

This skill does not call HTTP APIs itself. Use the connected MCP servers:

| Server | Tools |
| --- | --- |
| `obot-card-verify-mcp` | `check_card_verify_config`, `card_verify` |
| `obot-weather-mcp` | `list_cities`, `get_weather`, `get_forecast` |

If a required tool is missing, stop and tell the user to connect those two MCP servers on this agent. Do not invent verification or weather data.

## Inputs

Collect these before starting. Ask for anything missing.

| Field | Required | Default | Notes |
| --- | --- | --- | --- |
| `image_url` | Yes | — | Publicly reachable image URL |
| `city` | Yes | — | Beijing / Shanghai / Guangzhou / Shenzhen / New York, or 北京 / 上海 / 广州 / 深圳 / 纽约 |
| `category` | No | `VEHICLE_LICENSE` | Document type |
| `sub_category` | No | `FRONT` | `FRONT` or `BACK` |

If `city` is unsupported, call `list_cities`, show the list, and ask the user to pick one.

## Workflow (do in this order)

```
1. 收集入参
2. 检查 MCP 是否可用
3. 查询当前天气 + 三日预报
4. 给出是否适合拍照/外勤的天气结论
5. 调用证照鉴伪
6. 输出综合报告（鉴伪 + 天气 + 下一步）
```

### Step 1 — Collect inputs

Confirm `image_url` and `city`. Fill defaults for `category` and `sub_category` if omitted.

### Step 2 — Check MCP availability

1. Call `check_card_verify_config`.
2. If `ok` is false, stop. Tell the user to set `CARD_VERIFY_BASE_URL`, `CARD_VERIFY_APP_ID`, and `CARD_VERIFY_API_KEY` on the card-verify MCP. Do not print secrets.
3. Call `list_cities` only if the city may be unsupported.

### Step 3 — Weather first

1. Call `get_weather` with `city`.
2. Call `get_forecast` with the same `city`.
3. Classify conditions:
   - **适合拍照**: Sunny / Cloudy / Partly cloudy, and not Thunderstorm / Rainy / Showers.
   - **谨慎拍照**: Rainy / Light rain / Humid / Overcast. Warn that glare, blur, or water spots may hurt verification.
   - **不建议外勤**: Thunderstorm. Recommend delay or indoor reshoot.
4. Tell the user the weather conclusion, then continue to verification unless they ask to stop.

Do not skip verification only because weather is poor. Still run Step 4, and put the weather risk into the report.

### Step 4 — Verify the document image

Call `card_verify` with:

- `image_url`
- `category` (default `VEHICLE_LICENSE`)
- `sub_category` (default `FRONT`)

Interpret the tool result:

- `ok` is false, or `error` is set: verification **failed to run**. Report the error type (`missing_config`, `timeout`, `request_failed`, HTTP status). Do not claim the document is fake.
- `ok` is true: summarize `data` from the API. If the payload is unclear, quote the important fields instead of guessing pass/fail.

Never invent plate numbers, owner names, or authenticity scores that were not in the tool response.

### Step 5 — Combined report

Return a single report in the user's language (Chinese if they wrote Chinese):

```markdown
# 现场作业报告

## 1. 入参
- 城市：
- 证照类型：
- 图片：只写已确认的 URL，不要展开签名查询参数以外的密钥

## 2. 天气
- 当前：天气 / 气温 / 湿度 / 风力
- 预报：今天 / 明天 / 后天
- 外勤建议：适合拍照 | 谨慎拍照 | 不建议外勤
- 原因：

## 3. 证照鉴伪
- 调用状态：成功 | 失败
- 结论：根据 API 原文归纳
- 关键字段：

## 4. 下一步
- 鉴伪成功且天气适合：可继续现场作业
- 鉴伪成功但天气差：建议补拍或改期
- 鉴伪失败：先排除图片清晰度/拍摄环境，必要时换图重试
```

## Guardrails

- Keep this order: weather then verify, unless the user says to skip one step.
- Do not hardcode API keys, app ids, or weather numbers.
- Do not call the cardVerify HTTP API directly; only use the MCP tool.
- If only weather is requested, still prefer this skill only when verification is also in scope. For weather-only questions, just use `obot-weather-mcp`.
- If only verification is requested, you may skip weather after saying so, then run Step 4 and a shorter report.

## Example

User: 帮我核验这张行驶证，顺便看下北京今天能不能外勤拍照  
Image URL: `https://example.com/license-front.jpg`

Agent:

1. `get_weather(city="北京")` then `get_forecast(city="北京")`
2. State whether outdoor photography is advisable
3. `card_verify(image_url=..., category="VEHICLE_LICENSE", sub_category="FRONT")`
4. Output the combined report
