import requests
import os

# 配置请求参数
url = "https://marketplace.walmartapis.com/v3/feeds?feedType=MP_ITEM"
#params = {"feedType": "MP_ITEM"}  # URL 查询参数（对应 curl 中的 ?feedType=MP_ITEM）

# 请求头（完全对应 curl 中的 --header）
headers = {
    "WM_QOS.CORRELATION_ID": "b3261d2d-028a-4ef7-8602-633c23200af6",
    "WM_SEC.ACCESS_TOKEN": "eyJraWQiOiIzMzZkODkyNi0zOWVmLTQ0OTctOWFlNy0wZTVlNDVhODNiOWMiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiZGlyIn0..pXd2ZjzUpbnkc5_f.77TSDSN9Oj5cqvBhEOdZj557RbSBcFxEKhI8mv6r1ekCO9CzU1KrfxwHhrlMA71gngK7qtfGn5TrNMad0KSqwtTAc6ItPTb03k7OoDDOfhIMfIxBiKlX2gSIgZ_59TP2YQ22iewwGlXGfzPtJGyNOe5OM8B0byUL8k6IxoVoAeapGtyMNhbEbzuMDB7o2V5_UTKAl3ZP7kDEQGUVEdJEuQtrArw5gz5-dy5kAtAEq1Yzc0yuI1a6cb1n-lA2xLr2SujNUjB_NtCRtEvY5YKOTYms_dcWn6cu0LsQn0WBpPfzZG2ZZvkAtY7cH-x-3FwDIlKqI3cp8RC5TiVdZWC02GkTM1_SThsTVQTMdMvlCb53CFUD90rUkJpIwNGWIZAGUOcuTdva8H0Sz_xpxCDqSl2x6JLlqvVnfQXMy1MYDo3UKcP7_27CnkIh1yp7hPX8C1P1Zl2npCHhuD4fIZIW16MTASjv2QomACH2Sc1g8B2_rqGSrLJvJW94W1wSfjgNkxoJEygfB5j6TXVA5LTMlYlgPGXjaW_Psvu4vvx4XYVcA2i02AO0NJ-9Zz8pVLQ8akY5fUTw7Ubs0YhunmDuay5jub-NbYl50A1iqdiCarfqxuc46vDT2dC_rATOdkSWl85wBXunUxCB9sF1caDzUdwL0CleAW_W6gS4lzSlHrvsF1O0ARvR1PjoymUl.SXIXQNl_3WB5SXSJmzAYSA",
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
        url=url,
        #params=params,
        headers=headers,
        files=files,
        timeout=30  # 超时时间（秒），可根据需求调整
    )

    # 打印响应结果
    print(f"响应状态码：{response.status_code}")
    print(f"响应内容：{response.text}")

    # 若响应是 JSON 格式，可解析为字典
    if response.headers.get("content-type", "").startswith("application/json"):
        response_json = response.json()
        print(f"解析后的 JSON 响应：{response_json}")

except Exception as e:
    print(f"请求失败：{str(e)}")
finally:
    # 确保文件流关闭（with 语句更优雅，也可替换为 with 写法）
    files["file"][1].close()