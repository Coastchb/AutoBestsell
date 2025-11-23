import requests
import time
import json
import os
import base64

# -------------------------- 配置参数（需替换为你的信息）--------------------------
CLIENT_ID = "a810c17f-f864-4928-9065-19b234cb36c6"  # 开发者平台获取
CLIENT_SECRET = "APaXehSpu-YkOfHP-7Kp4r3If9_bECmbb6OgoqXgfxLpwg1I0lPzqHjrHkosMLQtS2rkqF6XLVMbv7NTCZz5rFo"  # 开发者平台获取
ENVIRONMENT = "sandbox"  # 测试环境填 "sandbox"，正式环境填 "production"
# 接口端点（根据环境自动切换，无需修改）
TOKEN_URL = "https://marketplace.walmartapis.com/v3/token" if ENVIRONMENT == "production" else "https://sandbox.walmartapis.com/v3/token"
BATCH_UPLOAD_URL = "https://marketplace.walmartapis.com/v3/feeds?feedType=MP_ITEM" #if ENVIRONMENT == "production" else "https://sandbox.walmartapis.com/v3/feeds?feedType=MP_ITEM"


# -------------------------- 核心功能函数 --------------------------
def get_access_token():
    """获取OAuth 2.0 Access Token（有效期3600秒，官方要求）"""
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "Authorization": f"Basic {base64.b64encode(auth_str.encode('utf-8')).decode('utf-8')}",
        "WM_QOS.CORRELATION_ID": "b3261d2d-028a-4ef7-8602-633c23200af6",  # 唯一请求ID（用于排查问题）
        "WM_SVC.NAME": "Walmart Marketplace"  # 固定值
    }
    data = {
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=10)
        response.raise_for_status()  # 触发HTTP错误（如401、403）
        token_data = response.json()
        print(f"Token获取成功，有效期：{token_data['expires_in']}秒")
        return token_data["access_token"]
    except requests.exceptions.RequestException as e:
        print(f"Token获取失败：{str(e)}")
        if response.status_code == 401:
            print("错误原因：Client ID/Secret错误，或账号未激活")
        exit(1)

def batch_upload_products(access_token):
    """批量上传商品到沃尔玛平台"""
    # 请求头（完全对应 curl 中的 --header）
    headers = {
        "WM_QOS.CORRELATION_ID": "b3261d2d-028a-4ef7-8602-633c23200af6",
        "WM_SEC.ACCESS_TOKEN": f"{access_token}",
        "WM_SVC.NAME": "Walmart Marketplace",
        "accept": "application/json"
        # 注意：multipart/form-data 不需要手动指定，requests 会自动处理
    }

    # 上传的文件配置（对应 curl 中的 --form file='@V4.8_MP_ITEM.json'）
    file_path = "items-feed/V4.8_MP_ITEM.json"  # 确保该文件在 Python 脚本执行目录下
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在：{file_path}")

    # files 格式：{字段名: (文件名, 文件对象, MIME类型)}
    files = {
        "file": (
            os.path.basename(file_path),  # 上传后的文件名（与原文件一致）
            open(file_path, "rb"),        # 以二进制模式打开文件
            "application/json"            # 文件的 MIME 类型（JSON 对应此值）
        )
    }

    try:
        # 发送 POST 请求
        response = requests.post(
            url=BATCH_UPLOAD_URL,
            #params=params,
            headers=headers,
            files=files,
            timeout=30  # 超时时间（秒），可根据需求调整
        )

        response.raise_for_status()
        upload_result = response.json()
        print("\n上传响应结果：")
        print(json.dumps(upload_result, indent=2))

        # 解析成功/失败商品
        success_skus = [item["sku"] for item in upload_result.get("successes", [])]
        failed_skus = [item["sku"] for item in upload_result.get("failures", [])]
        print(f"\n✅ 上传成功的商品SKU：{success_skus}")
        if failed_skus:
            print(f"❌ 上传失败的商品SKU：{failed_skus}")
            # 打印失败原因
            for failure in upload_result.get("failures", []):
                print(f"  - SKU {failure['sku']}：{failure['errors'][0]['message']}")

    except requests.exceptions.RequestException as e:
        print(f"\n上传失败：{str(e)}")
        if response.status_code in [400, 403, 422]:
            print(f"错误详情：{response.text}")
            if "INSUFFICIENT_PERMISSIONS" in response.text:
                print("原因：未开通Product Management权限，请返回开发者平台申请")
            elif "INVALID_IMAGE_URL" in response.text:
                print("原因：图片URL无效（需HTTPS公网链接，无水印）")
    finally:
        # 确保文件流关闭（with 语句更优雅，也可替换为 with 写法）
        files["file"][1].close()


# -------------------------- 主函数执行 --------------------------
if __name__ == "__main__":
    # 1. 获取Access Token
    access_token = get_access_token()
    print(f"access_token:{access_token}")
    # 2. 批量上传商品
    batch_upload_products(access_token)
