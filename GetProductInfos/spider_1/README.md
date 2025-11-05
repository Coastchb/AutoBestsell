## 说明

该脚本使用亚马逊官方 API：
- PA-API (Product Advertising API v5)：用于按类目获取“最新上架/新品”商品列表（标题、图片、描述等）
- SP-API (Selling Partner API)：用于查询每个 ASIN 的报价，以判断是否为 FBA (AFN)

输出两种格式：CSV 和 JSON，包含 `asin`、`title`、`image`、`description`、`is_fba`。

### 目录
- `fetch_new_products.py` 主程序
- `requirements.txt` 依赖

### 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 必要环境变量

PA-API（必需，用于新品检索）：
- `PAAPI_ACCESS_KEY`
- `PAAPI_SECRET_KEY`
- `PAAPI_PARTNER_TAG`（联盟跟踪ID）
- `PAAPI_HOST`（可选，默认 `webservices.amazon.com`）

SP-API（可选，用于判断 FBA，如果不配置将跳过该字段）：
- `LWA_APP_ID`
- `LWA_CLIENT_SECRET`
- `SP_API_REFRESH_TOKEN`
- `AWS_ACCESS_KEY`
- `AWS_SECRET_KEY`
- `ROLE_ARN`

可在项目根目录创建 `.env`（自行加载）或使用 shell 导出，例如：

```bash
export PAAPI_ACCESS_KEY=...
export PAAPI_SECRET_KEY=...
export PAAPI_PARTNER_TAG=yourtag-20
export PAAPI_HOST=webservices.amazon.com

export LWA_APP_ID=...
export LWA_CLIENT_SECRET=...
export SP_API_REFRESH_TOKEN=...
export AWS_ACCESS_KEY=...
export AWS_SECRET_KEY=...
export ROLE_ARN=arn:aws:iam::123456789012:role/YourSpApiRole
```

### 支持的类目名称

当前内置映射（US）：
- `Arts,Crafts&Sewing` -> `ArtsAndCrafts`
- `Clothing,Shoes&Jewelry` -> `FashionAndAccessories`

如需扩展，请在 `fetch_new_products.py` 中的 `PAAPI_CATEGORY_MAP` 增加条目。

### 运行示例

以美国站点 US 为例：

```bash
cd GetProductInfos/spider_1
python fetch_new_products.py 'Arts,Crafts&Sewing' 2 US
```

参数：
- 第1个参数：类目名称（如 `'Arts,Crafts&Sewing'`）
- 第2个参数：抓取页数（每页10条，默认 1）
- 第3个参数：站点（默认 `US`，支持 `US/UK/DE/JP/CA/FR/IT/ES/IN/AU/MX`）

运行完成后会在当前目录生成：
- `new_products_<类目>_<站点>.csv`
- `new_products_<类目>_<站点>.json`

### 注意事项
- PA-API 负责“新品/最新上架”的检索，SP-API 仅用于判断是否 AFN(FBA)。
- 并非所有 ASIN 都能从 SP-API 获取到报价信息，无法确定时 `is_fba` 为 `null`。
- 若你的账号权限或资质不足，SP-API 调用可能失败，脚本会跳过 FBA 字段。

