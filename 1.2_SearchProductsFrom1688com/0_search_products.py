import requests
import hashlib
import time
import urllib.parse
import base64
# 配置信息（替换为你的实际参数）
APP_KEY = "你的appkey"
APP_SECRET = "你的secret"
API_URL = "https://gw.open.1688.com/openapi/param2/1/com.alibaba.ai.vision/alibaba.ai.vision.product.search"
IMAGE_PATH = "sample.jpg"  # 本地商品图片路径
# 1. 图片预处理：转换为Base64编码
with open(IMAGE_PATH, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")
# 2. 组装参数
params = {
    "app_key": APP_KEY,
    "method": "alibaba.ai.vision.product.search",
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "v": "1.0",
    "format": "json",
    "image": image_base64,  # Base64编码图片
    "imageType": "base64",  # 图片类型为base64
    "matchType": "exact",  # 精准匹配（similar为相似匹配）
    "page": 1,  # 页码
    "pageSize": 20  # 每页返回20条结果
}
# 3. 生成签名
sorted_params = sorted(params.items(), key=lambda x: x[0])  # 按参数名排序
# URL编码参数值，拼接为字符串
sign_str = "&".join([f"{k}={urllib.parse.quote_plus(v)}" for k, v in sorted_params])
# 加密生成签名
sign = hashlib.md5((sign_str + "&secret=" + APP_SECRET).encode()).hexdigest().upper()
params["sign"] = sign
# 4. 发送请求并解析数据
response = requests.get(API_URL, params=params)
result = response.json()
# 5. 处理响应
if result.get("success"):
    products = result["result"]["products"]
    print(f"共匹配到{len(products)}款商品：")
    for idx, product in enumerate(products, 1):
        print(f"\n=== 第{idx}款商品 ===")
        print(f"商品标题：{product['title']}")
        print(f"价格范围：{product['priceRange']['minPrice']}-{product['priceRange']['maxPrice']}元")
        print(f"起订量：{product['moq']}件")
        print(f"供应商：{product['seller']['sellerName']}（诚信通{product['seller']['memberLevel']}年）")
        print(f"匹配得分：{product['matchScore']}分（满分100）")
        print(f"商品链接：{product['detailUrl']}")
else:
    print(f"调用失败：{result['errorMessage']}（错误码：{result['errorCode']}）")