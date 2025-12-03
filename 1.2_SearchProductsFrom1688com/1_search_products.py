import requests
import time
import hmac
import hashlib
import urllib.parse
from typing import Optional, Dict

class AliCrossImageSearch:
    def __init__(self, app_key: str, app_secret: str):
        self.app_key = app_key
        self.app_secret = app_secret
        # 完整接口URL（含域名）
        self.full_api_url = f"https://gw.open.1688.com/openapi/param2/1/com.alibaba.linkplus/alibaba.cross.similar.offer.search/{self.app_key}"
        # 提取官方要求的urlPath（关键！从完整URL中拆分）
        self.url_path = "param2/1/com.alibaba.linkplus/alibaba.cross.similar.offer.search"
        self.token_url = "https://gw.open.1688.com/auth/requestToken"

    def get_access_token(self) -> Optional[str]:
        """获取Access Token（逻辑不变）"""
        params = {
            "client_id": self.app_key,
            "client_secret": self.app_secret,
            "grant_type": "client_credentials",
            "scope": "com.alibaba.linkplus"
        }
        try:
            response = requests.get(self.token_url, params=params, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            return token_data.get("access_token")
        except Exception as e:
            print(f"获取Token失败：{str(e)}，响应：{response.text if 'response' in locals() else '无'}")
            return None

    def generate_official_sign(self, params: Dict) -> str:
        """【官方标准签名方法+urlPath】完全对齐1688文档"""
        # 步骤1：参数去重+过滤空值
        unique_params = {}
        for key, value in params.items():
            if value is not None and str(value).strip() != "":
                unique_params[key] = str(value).strip()

        # 步骤2：按参数名ASCII升序排序
        sorted_items = sorted(unique_params.items(), key=lambda x: x[0])

        # 步骤3：拼接参数为"key=value"字符串（无分隔符）
        params_str = "".join([f"{key}{value}" for key, value in sorted_items])

        # 步骤4：拼接「urlPath + 参数字符串」（核心补充！官方强制要求）
        sign_base_str = self.url_path + params_str

        # 步骤5：HMAC-SHA1签名（密钥为app_secret，UTF-8编码）
        hmac_obj = hmac.new(
            self.app_secret.encode("utf-8"),
            sign_base_str.encode("utf-8"),
            hashlib.sha1
        )

        # 步骤6：转十六进制+大写，得到sign
        sign = hmac_obj.hexdigest().upper()
        return sign

    def search_similar_offer(self, access_token: str, image_param: Dict, 
                             filter_params: Optional[Dict] = None) -> Optional[Dict]:
        """调用接口（签名含urlPath，完全合规）"""
        # 1. 基础必选参数（官方要求的所有固定参数）
        base_params = {
            "app_key": self.app_key,
            "timestamp": str(int(time.time() * 1000)),  # 毫秒级时间戳
            "format": "json",
            "v": "2.0",
            "sign_method": "hmac",
            "scene": "cross_border",
            "access_token": access_token
        }

        # 2. 合并所有参数（基础+筛选+图片参数）
        if filter_params:
            base_params.update(filter_params)
        base_params.update(image_param)

        # 3. 生成合规签名（含urlPath）
        base_params["_aop_signature"] = self.generate_official_sign(base_params)

        # 4. 构造请求头
        headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json" if "image_url" in image_param else "multipart/form-data"
        }

        # 5. 发送请求
        try:
            if "image_file" in image_param:
                files = {"image_file": image_param["image_file"]}
                response = requests.post(
                    self.full_api_url,
                    data=base_params,
                    files=files,
                    headers=headers,
                    timeout=30
                )
            else:
                response = requests.post(
                    self.full_api_url,
                    json=base_params,
                    headers=headers,
                    timeout=30
                )

            response.raise_for_status()
            result = response.json()
            print(f"接口响应：{result}")
            return result
        except Exception as e:
            error_msg = f"调用失败：{str(e)}"
            if "response" in locals():
                error_msg += f"，响应：{response.text}"
            print(error_msg)
            return None


# -------------------------- 调用示例 --------------------------
if __name__ == "__main__":
    APP_KEY = "3969349"
    APP_SECRET = "gJ59S3lPaClY"

    cross_image_search = AliCrossImageSearch(APP_KEY, APP_SECRET)
    access_token = cross_image_search.get_access_token()
    if not access_token:
        exit()

    # 图片参数（二选一）
    image_param = {"image_url": "https://m.media-amazon.com/images/I/71CZ9WJJviL._AC_SL1500_.jpg"}  # 公网可访问URL
    # with open("test.jpg", "rb") as f:
    #     image_param = {"image_file": f}

    # 筛选参数
    filter_params = {"category_id": "60020000", "min_price": 10, "max_price": 100}

    # 调用接口
    result = cross_image_search.search_similar_offer(access_token, image_param, filter_params)

    # 解析结果
    if result and result.get("code") == 200:
        similar_offers = result.get("data", {}).get("similar_offers", [])
        print(f"\n共找到{len(similar_offers)}个相似商品")
    else:
        print(f"错误：{result.get('msg', '未知')}")