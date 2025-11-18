import http.client
import mimetypes
from codecs import encode
import time 
import hashlib
import json
import requests


app_id = 'dh2511ujbi5lzy3z84'
app_secret = 'e22557f526d04a387e104352f723c99d'
version = '2.0.0'
cur_timestamp = int(time.time())


def download_image_by_url(image_url, save_path="downloaded_image.jpg"):
    """
    下载网络图片到本地
    :param image_url: 图片的 HTTPS/HTTP URL（必填）
    :param save_path: 保存路径（默认当前目录，可自定义文件名/路径）
    :return: 下载成功返回 True，失败返回 False
    """
    # 自定义请求头（模拟浏览器，避免部分网站反爬）
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        # 发送 GET 请求获取图片（stream=True 避免一次性加载大文件到内存）
        response = requests.get(
            url=image_url,
            headers=headers,
            stream=True,
            timeout=10  # 超时时间 10 秒，防止卡壳
        )
        
        # 检查请求是否成功（状态码 200 为成功）
        response.raise_for_status()
        
        # 确保保存目录存在（若路径含文件夹，如 "images/1.jpg"，自动创建文件夹）
        save_dir = os.path.dirname(save_path)
        if save_dir and not os.path.exists(save_dir):
            os.makedirs(save_dir)
        
        # 以二进制模式写入文件（图片是二进制数据）
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):  # 分块写入，适配大图片
                if chunk:
                    f.write(chunk)
        
        print(f"✅ 图片下载成功！保存路径：{os.path.abspath(save_path)}")
        return True
    
    except requests.exceptions.RequestException as e:
        print(f"❌ 图片下载失败：{str(e)}")
        if hasattr(response, "status_code"):
            print(f"错误状态码：{response.status_code}")
        return False

def calculate_str_md5(input_str, encoding="utf-8"):
    """
    计算字符串的 MD5 值
    :param input_str: 待计算的字符串
    :param encoding: 编码格式（默认 utf-8）
    :return: 32位小写 MD5 哈希值
    """
    # 1. 创建 md5 哈希对象
    md5_obj = hashlib.md5()
    
    # 2. 更新哈希对象（字符串需先编码为字节流）
    md5_obj.update(input_str.encode(encoding))
    
    # 3. 获取 MD5 值（hexdigest() 返回 32位小写字符串）
    md5_value = md5_obj.hexdigest()
    
    return md5_value

def get_sign():
    return calculate_str_md5(f'{app_id}{cur_timestamp}{version}{app_secret}')


# 认证信息
authorization = {
    'version': version,
    'timestamp': cur_timestamp,
    'appid': app_id,
    'sign': get_sign()
}

# 请求数据
url = 'https://dhd.douhuiai.com/api/aiart/doGennanoimg'
data = {
    'dhAiType': 'nanoimg',
    'dhPrompt': '给图片加个合适的背景，背景虚化一下，透明度60%；其他部分不要变动',
    'dhInputImgs': ['https://m.media-amazon.com/images/I/71CZ9WJJviL._AC_SL1500_.jpg']
}

headers = {
    'authorization': json.dumps(authorization),
    'Content-Type': 'application/x-www-form-urlencode; charset=UTF-8',
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    response = requests.post(
        url=url,
        data=data,
        headers=headers,
        timeout=60
    )
    response_json = json.loads(response.text)
    print(response_json)
except requests.exceptions.RequestException as e:
    print(f'请求失败:{e}')

