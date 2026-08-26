# Obot Catalog Entry（发布时覆盖写入，直接复制到创建表单）

## Name
天气查询

## Short Description
查询北京、上海、广州、深圳、纽约的演示天气和三日预报。

## Description
提供演示天气数据，无需 API Key，适合联调和现场作业流程演示。

## 功能
- `list_cities`：列出支持的城市
- `get_weather`：当前天气
- `get_forecast`：三日预报
- 支持中文城市名：北京 / 上海 / 广州 / 深圳 / 纽约

UVX 包名：`obot-weather-mcp==0.1.1`

## Server Tenancy / Type
Multi-tenant

## Runtime
- Runtime: UVX
- Package: `obot-weather-mcp==0.1.1`

## Obot 环境变量
无需配置。

## 说明
- Type 选 Multi-tenant：所有用户共用同一份 MCP 实例和同一组环境变量。
- 此项保存后不能改，要改必须删除后重建。
