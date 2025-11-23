#from amazon_paapi5_python_sdk.configuration import Configuration
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.models.search_items_request import SearchItemsRequest
from paapi5_python_sdk.models.search_items_resource import SearchItemsResource
from paapi5_python_sdk.rest import ApiException
import inspect
print(f"requests 模块路径: {inspect.getfile(DefaultApi)}")

from datetime import datetime, timedelta
import time

class AmazonOfficialPAApi:
    def __init__(self, access_key, secret_key, associate_id, region="us-east-1"):
        # 配置官方SDK
        self.config = Configuration()
        self.config.access_key = access_key
        self.config.secret_key = secret_key
        self.config.region = region  # 与端点自动绑定
        self.associate_id = associate_id
        self.api = DefaultApi(configuration=self.config)

    # 筛选辅助方法（不变）
    @staticmethod
    def is_recent_new_product(launch_date_str):
        if not launch_date_str:
            return False
        try:
            launch_date = datetime.strptime(launch_date_str, "%Y-%m-%d")
            return datetime.now().date() - launch_date.date() <= timedelta(days=30)
        except ValueError:
            return False

    @staticmethod
    def has_new_release_tag(features):
        if not features:
            return False
        if isinstance(features, list):
            return any('new release' in feat.lower() for feat in features if feat)
        return 'new release' in features.lower() if features else False

    def search_new_products(self, category_ids, max_pages=10):
        all_products = []
        resources = [
            SearchItemsResource.ITEMS_TITLE,
            SearchItemsResource.ITEMS_IMAGES_PRIMARY_MEDIUM_URL,
            SearchItemsResource.ITEMS_DELIVERYINFO_INCLUDED_SHIPPING_TYPE,
            SearchItemsResource.ITEMS_DELIVERYINFO_ESTIMATED_DELIVERY_MIN_DATE,
            SearchItemsResource.ITEMS_DELIVERYINFO_ESTIMATED_DELIVERY_MAX_DATE,
            SearchItemsResource.ITEMS_ASIN,
            SearchItemsResource.ITEMS_DETAILPAGEURL,
            SearchItemsResource.ITEMS_ITEMINFO_LAUNCHDATE_RELEASEDATE,
            SearchItemsResource.ITEMS_CUSTOMERREVIEWS_TOTALREVIEWS,
            SearchItemsResource.ITEMS_ITEMINFO_FEATURES_FEATURE
        ]

        for category_id in category_ids:
            print(f"\n===== 类目ID {category_id} =====")
            next_token = None
            page = 1
            while page <= max_pages:
                # 构造官方SDK的请求对象
                request = SearchItemsRequest(
                    partner_tag=self.associate_id,
                    partner_type=PartnerType.ASSOCIATES,
                    category_id=category_id,
                    sort_by="NewestArrivals",
                    item_count=10,
                    resources=resources,
                    next_token=next_token
                )

                try:
                    # 调用官方SDK的search_items方法（无boto3依赖）
                    time.sleep(1.5)  # 限流延迟
                    response = self.api.search_items(request)
                    items_result = response.items_result if response.items_result else None
                    items = items_result.items if items_result and items_result.items else []

                    for item in items:
                        # 筛选逻辑
                        launch_date = item.item_info.launch_date.release_date if (item.item_info and item.item_info.launch_date) else ""
                        if not self.is_recent_new_product(launch_date):
                            continue
                        total_reviews = item.customer_reviews.total_reviews if (item.customer_reviews) else 0
                        features = item.item_info.features.feature if (item.item_info and item.item_info.features) else []
                        if not self.has_new_release_tag(features):
                            continue

                        # 整理数据
                        product = {
                            'ASIN': item.asin or '',
                            '标题': item.title or '无标题',
                            '主图URL': item.images.primary.medium.url if (item.images and item.images.primary and item.images.primary.medium) else '无图片',
                            '配送类型': item.delivery_info.included_shipping_type if item.delivery_info else '无配送信息',
                            '预计送达时间': self._format_delivery_date(item),
                            '详情页链接': item.detail_page_url or '无链接',
                            '上市日期': launch_date,
                            '总评价数': total_reviews,
                            '是否New Release': '是'
                        }
                        all_products.append(product)

                    print(f"第{page}页：原始{len(items)}条 → 筛选后{len([p for p in all_products if p['ASIN'] == item.asin for item in items])}条")
                    next_token = response.next_token if response.next_token else None
                    if not next_token:
                        break
                    page += 1

                except Exception as e:
                    print(f"请求失败（第{page}页）：{str(e)}")
                    break
        return all_products

    @staticmethod
    def _format_delivery_date(item):
        if not item.delivery_info or not item.delivery_info.estimated_delivery:
            return "无预计送达时间"
        ed = item.delivery_info.estimated_delivery
        min_date = ed.min_date or ""
        max_date = ed.max_date or ""
        return f"{min_date} 至 {max_date}" if min_date and max_date else min_date or max_date or "无预计送达时间"

# -------------------------- 运行代码 --------------------------
if __name__ == "__main__":
    # 替换为你的实际信息！
    ACCESS_KEY = "你的Access Key ID"
    SECRET_KEY = "你的Secret Access Key"
    ASSOCIATE_ID = "你的亚马逊联盟Associate ID"
    REGION = "us-east-1"  # 美站
    TARGET_CATEGORY_IDS = ["1063498", "1000"]  # Home&Kitchen + Books

    # 初始化官方SDK客户端
    pa_api = AmazonOfficialPAApi(
        access_key=ACCESS_KEY,
        secret_key=SECRET_KEY,
        associate_id=ASSOCIATE_ID,
        region=REGION
    )

    # 获取数据
    new_products = pa_api.search_new_products(category_ids=TARGET_CATEGORY_IDS, max_pages=5)

    # 输出结果
    print(f"\n共获取{len(new_products)}条新品数据")
    for idx, p in enumerate(new_products, 1):
        print(f"\n{idx}. {p['标题']}（ASIN：{p['ASIN']}）")
        print(f"   主图：{p['主图URL']}")
        print(f"   上市日期：{p['上市日期']}")
        print(f"   评价数：{p['总评价数']}")