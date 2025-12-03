import requests
import time
import hmac
import hashlib
import base64
from typing import Optional, List, Dict

class AmazonDesignPatentChecker:
    def __init__(self, patsnap_api_key: str, patsnap_secret_key: str):
        self.api_key = patsnap_api_key
        self.secret_key = patsnap_secret_key
        self.base_url = "https://api.patsnap.com/v3"
        self.token_expires_at = 0
        self.access_token = None

    def get_patsnap_token(self) -> Optional[str]:
        """获取PatSnap API访问Token（有效期2小时）"""
        current_time = time.time()
        if self.access_token and current_time < self.token_expires_at:
            return self.access_token
        
        # 生成PatSnap签名（按官方规范：timestamp + api_key + secret_key 加密）
        timestamp = str(int(current_time * 1000))
        sign_str = f"{self.api_key}{timestamp}{self.secret_key}".encode("utf-8")
        sign = hmac.new(
            self.secret_key.encode("utf-8"),
            sign_str,
            hashlib.sha256
        ).hexdigest().upper()
        
        headers = {"Content-Type": "application/json"}
        payload = {
            "apiKey": self.api_key,
            "timestamp": timestamp,
            "sign": sign
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/token",
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            token_data = response.json()
            self.access_token = token_data.get("accessToken")
            self.token_expires_at = current_time + 7200  # 2小时过期
            print(f"✅ PatSnap Token获取成功，有效期至：{time.ctime(self.token_expires_at)}")
            return self.access_token
        except Exception as e:
            print(f"❌ PatSnap Token获取失败：{str(e)}，响应：{response.text if 'response' in locals() else '无'}")
            return None

    def _get_amazon_product_info(self, asin: str) -> Optional[Dict]:
        """
        辅助函数：通过ASIN获取亚马逊商品核心信息（标题、主图URL）
        （依赖亚马逊Product Advertising API，需提前申请权限）
        """
        # 替换为你的亚马逊PA API凭证（client_id、client_secret、associate_tag）
        pa_api_client_id = "你的亚马逊PA API Client ID"
        pa_api_client_secret = "你的亚马逊PA API Client Secret"
        associate_tag = "你的亚马逊联盟Tag"
        
        # 生成PA API Token（简化版，完整逻辑需参考亚马逊PA API文档）
        pa_auth_str = f"{pa_api_client_id}:{pa_api_client_secret}".encode("utf-8")
        pa_basic_auth = base64.b64encode(pa_auth_str).decode("utf-8")
        pa_token_response = requests.post(
            "https://api.amazon.com/auth/o2/token",
            headers={"Authorization": f"Basic {pa_basic_auth}"},
            data={"grant_type": "client_credentials", "scope": "product AdvertisingAPI"}
        )
        pa_token = pa_token_response.json().get("access_token")
        
        # 调用PA API获取商品信息
        pa_headers = {
            "Authorization": f"Bearer {pa_token}",
            "x-amz-target": "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"
        }
        pa_payload = {
            "ItemIds": [asin],
            "Resources": ["Images.Primary.Large", "ItemInfo.Title"],
            "PartnerTag": associate_tag,
            "PartnerType": "Associate"
        }
        
        try:
            pa_response = requests.post(
                "https://paapi5.us-east-1.amazonaws.com/",
                headers=pa_headers,
                json=pa_payload,
                timeout=15
            )
            pa_response.raise_for_status()
            item_data = pa_response.json().get("ItemsResult", {}).get("Items", [])[0]
            return {
                "title": item_data.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", ""),
                "image_url": item_data.get("Images", {}).get("Primary", {}).get("Large", {}).get("URL", "")
            }
        except Exception as e:
            print(f"❌ 亚马逊商品信息获取失败（ASIN：{asin}）：{str(e)}")
            return None

    def search_design_patent_by_asin(self, asin: str, country_codes: List[str] = ["US", "CN", "EU"]) -> Dict:
        """
        方式1：通过ASIN查询商品是否注册外观专利（推荐优先使用）
        :param asin: 亚马逊商品ASIN码（如B07VGRYQMR）
        :param country_codes: 目标专利国家/地区（US=美国，CN=中国，EU=欧盟，JP=日本）
        :return: 专利检索结果（含是否注册、专利号、状态、有效期等）
        """
        # 1. 通过ASIN获取商品标题和图片（用于专利检索关键词）
        product_info = self._get_amazon_product_info(asin)
        if not product_info:
            return {"error": "获取商品信息失败", "result": None}
        
        product_title = product_info["title"]
        product_image_url = product_info["image_url"]
        print(f"📦 商品信息：ASIN={asin}，标题={product_title}，图片URL={product_image_url}")
        
        # 2. 调用PatSnap API检索外观专利（关键词+图片双重匹配）
        return self.search_design_patent_by_keyword_and_image(
            keywords=[product_title],
            image_url=product_image_url,
            country_codes=country_codes
        )

    def search_design_patent_by_keyword(self, keywords: List[str], country_codes: List[str] = ["US", "CN", "EU"]) -> Dict:
        """
        方式2：通过关键词查询相关外观专利
        :param keywords: 商品关键词（如["wireless earbud case", "蓝牙耳塞盒"]）
        :param country_codes: 目标专利国家/地区
        :return: 专利检索结果
        """
        access_token = self.get_patsnap_token()
        if not access_token:
            return {"error": "PatSnap Token获取失败", "result": None}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": " OR ".join(keywords),
            "patentType": "DESIGN",  # 仅检索外观专利
            "countryCodes": country_codes,
            "pageSize": 20,  # 每页返回20条结果
            "pageNum": 1
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/patent/search",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return self._parse_patent_result(response.json())
        except Exception as e:
            error_msg = f"❌ 关键词专利检索失败：{str(e)}"
            if "response" in locals():
                error_msg += f"，响应：{response.text}"
            return {"error": error_msg, "result": None}

    def search_design_patent_by_image(self, image_url: str, country_codes: List[str] = ["US", "CN", "EU"]) -> Dict:
        """
        方式3：通过商品图片查询相似外观专利（图像识别匹配）
        :param image_url: 商品主图URL（清晰展示外观细节）
        :param country_codes: 目标专利国家/地区
        :return: 专利检索结果
        """
        access_token = self.get_patsnap_token()
        if not access_token:
            return {"error": "PatSnap Token获取失败", "result": None}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "imageUrl": image_url,
            "patentType": "DESIGN",
            "countryCodes": country_codes,
            "similarityThreshold": 0.7  # 相似度阈值（≥70%视为匹配）
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/patent/search-by-image",
                headers=headers,
                json=payload,
                timeout=60  # 图片比对耗时较长，超时设为60秒
            )
            response.raise_for_status()
            return self._parse_patent_result(response.json())
        except Exception as e:
            error_msg = f"❌ 图片专利检索失败：{str(e)}"
            if "response" in locals():
                error_msg += f"，响应：{response.text}"
            return {"error": error_msg, "result": None}

    def search_design_patent_by_keyword_and_image(self, keywords: List[str], image_url: str, country_codes: List[str] = ["US", "CN", "EU"]) -> Dict:
        """
        方式4：关键词+图片双重检索（准确率最高，推荐跨境场景）
        """
        access_token = self.get_patsnap_token()
        if not access_token:
            return {"error": "PatSnap Token获取失败", "result": None}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": " OR ".join(keywords),
            "imageUrl": image_url,
            "patentType": "DESIGN",
            "countryCodes": country_codes,
            "similarityThreshold": 0.7,
            "pageSize": 20
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/patent/search-combined",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            return self._parse_patent_result(response.json())
        except Exception as e:
            error_msg = f"❌ 双重检索失败：{str(e)}"
            if "response" in locals():
                error_msg += f"，响应：{response.text}"
            return {"error": error_msg, "result": None}

    def _parse_patent_result(self, patent_data: Dict) -> Dict:
        """解析专利检索结果，提取核心信息"""
        parsed_result = {
            "is_registered": False,
            "registered_patents": [],
            "total_count": 0,
            "summary": ""
        }
        
        patents = patent_data.get("result", {}).get("patents", [])
        total_count = patent_data.get("result", {}).get("totalCount", 0)
        parsed_result["total_count"] = total_count
        
        if not patents:
            parsed_result["summary"] = "未检索到相关外观专利"
            return parsed_result
        
        # 筛选有效且高相似度的专利（相似度≥70% + 专利状态为有效）
        valid_patents = []
        for patent in patents:
            patent_info = {
                "patent_number": patent.get("publicationNumber", ""),  # 专利号
                "country": patent.get("countryCode", ""),  # 国家/地区
                "title": patent.get("title", ""),  # 专利名称
                "applicant": patent.get("applicant", [{}])[0].get("name", ""),  # 申请人（品牌方）
                "filing_date": patent.get("filingDate", ""),  # 申请日
                "publication_date": patent.get("publicationDate", ""),  # 公开日
                "expiry_date": patent.get("expiryDate", ""),  # 到期日（判断是否有效）
                "status": patent.get("legalStatus", ""),  # 法律状态（如"ACTIVE"=有效）
                "similarity_score": patent.get("similarityScore", 0.0),  # 与商品的相似度
                "patent_url": patent.get("patentUrl", "")  # 专利详情页URL（可查看设计图）
            }
            
            # 过滤条件：相似度≥70% + 状态有效（ACTIVE/GRANTED） + 未过期
            if (patent_info["similarity_score"] >= 0.7 and
                patent_info["status"] in ["ACTIVE", "GRANTED"] and
                patent_info["expiry_date"] and time.strptime(patent_info["expiry_date"], "%Y-%m-%d") > time.localtime()):
                valid_patents.append(patent_info)
        
        parsed_result["is_registered"] = len(valid_patents) > 0
        parsed_result["registered_patents"] = valid_patents
        
        if valid_patents:
            parsed_result["summary"] = f"检索到{total_count}条相关外观专利，其中{len(valid_patents)}条为有效注册专利（相似度≥70%）"
        else:
            parsed_result["summary"] = f"检索到{total_count}条相关外观专利，但无有效注册专利（已过期/相似度不足）"
        
        return parsed_result


# -------------------------- 调用示例（三种方式任选） --------------------------
if __name__ == "__main__":
    # 替换为你的PatSnap API凭证（从PatSnap开发者中心获取）
    PATSNAP_API_KEY = "你的PatSnap API Key"
    PATSNAP_SECRET_KEY = "你的PatSnap Secret Key"

    # 初始化专利查询客户端
    patent_checker = AmazonDesignPatentChecker(PATSNAP_API_KEY, PATSNAP_SECRET_KEY)

    # -------------------------- 方式1：通过ASIN查询（推荐） --------------------------
    ASIN = "B07VGRYQMR"  # 待查询商品ASIN
    result = patent_checker.search_design_patent_by_asin(
        asin=ASIN,
        country_codes=["US", "CN"]  # 查询美国和中国的外观专利
    )

    # -------------------------- 方式2：通过关键词查询 --------------------------
    # KEYWORDS = ["wireless earbud case", "蓝牙耳塞收纳盒"]
    # result = patent_checker.search_design_patent_by_keyword(
    #     keywords=KEYWORDS,
    #     country_codes=["US", "EU"]
    # )

    # -------------------------- 方式3：通过图片查询 --------------------------
    # IMAGE_URL = "https://m.media-amazon.com/images/I/71XgZ4L3SOL._AC_UF1000,1000_QL80_.jpg"
    # result = patent_checker.search_design_patent_by_image(
    #     image_url=IMAGE_URL,
    #     country_codes=["US", "JP"]
    # )

    # -------------------------- 输出结果 --------------------------
    print("\n🎉 外观专利查询结果汇总：")
    print(f"错误信息：{result.get('error', '无')}")
    print(f"查询摘要：{result.get('result', {}).get('summary', '')}")
    print(f"是否已注册有效外观专利：{'✅ 是' if result.get('result', {}).get('is_registered') else '❌ 否'}")

    # 打印有效专利详情
    valid_patents = result.get("result", {}).get("registered_patents", [])
    if valid_patents:
        print("\n📋 有效注册外观专利详情：")
        for idx, patent in enumerate(valid_patents, 1):
            print(f"\n{idx}. 专利信息：")
            print(f"   - 专利号：{patent['patent_number']}")
            print(f"   - 国家/地区：{patent['country']}")
            print(f"   - 申请人（品牌）：{patent['applicant']}")
            print(f"   - 状态：{patent['status']}")
            print(f"   - 到期日：{patent['expiry_date']}")
            print(f"   - 与商品相似度：{patent['similarity_score']:.2f}")
            print(f"   - 专利详情页：{patent['patent_url']}")