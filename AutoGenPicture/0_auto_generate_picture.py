import os
import time 
import hashlib
import json
import requests


app_id = 'dh2511ujbi5lzy3z84'
app_secret = 'e22557f526d04a387e104352f723c99d'
version = '2.0.0'
cur_timestamp = int(time.time())

input_img_paths = [#'https://m.media-amazon.com/images/I/71CZ9WJJviL._AC_SL1500_.jpg',
                   # 'https://m.media-amazon.com/images/I/71M6+8Xn2YL._AC_SL1500_.jpg']
                    'https://m.media-amazon.com/images/I/81KZJl+1xtL._AC_SL1500_.jpg']

def download_image_by_url(image_url, save_path="downloaded_image.jpg"):
    """
    下载网络图片到本地
    :param image_url: 图片的 HTTPS/HTTP URL（必填）
    :param save_path: 保存路径（默认当前目录，可自定义文件名/路径）
    :return: 下载成功返回 True，失败返回 False
    """
    headers = {
        # 关键：模拟浏览器的User-Agent（必须有）
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        # 关键：添加Referer（来源页面，模拟从官网访问图片）
        "Referer": "https://www.douhuiai.com/",  # 图片域名的主站（根据URL推断）
        # 补充其他浏览器常见请求头，进一步伪装
        "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive"
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

# 认证信息
authorization = {
    'version': version,
    'timestamp': cur_timestamp,
    'appid': app_id,
    'sign': hashlib.md5(
        f"{app_id}{cur_timestamp}{version}{app_secret}".encode("utf-8")
    ).hexdigest()
}

# 请求数据
gen_img_url = 'https://dhd.douhuiai.com/api/aiart/doGennanoimg'
get_img_url = 'https://dhd.douhuiai.com/api/ai/getimgstatus'

data = {
    'dhAiType': 'nanoimg', #'txt2img',
    'dhPrompt': '给输入的图片加个或者换一个合适的背景，背景虚化一下，多加一些点缀，透明度40%；如果图片中有人物，就给人物换张脸；其他部分不要变动',
    'dhInputImgs': json.dumps(input_img_paths)
}

headers = {
    'authorization': json.dumps(authorization),
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    gen_img_response = requests.post(
        url=gen_img_url,
        data=data,
        headers=headers,
        timeout=60
    )
    gen_img_response_json = json.loads(gen_img_response.text)
    print(gen_img_response_json)

    
    if gen_img_response_json['status'] == 200:
        img_paths = gen_img_response_json['imgs']['imgs']
        print('下载并保存原图片')
        for img_idx, input_img_path in enumerate(input_img_paths):
            download_image_by_url(input_img_path, f'images/input/{img_idx}.jpg')

        request_cnt = 1
        uuid = gen_img_response_json['uuid']
        image_is_generating = True
        while image_is_generating:
            print(f'轮询图片生成状态, 第{request_cnt}次...')
            try:
                get_img_response = requests.get(f'{get_img_url}?uuid={uuid}&source=api', headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"})
                get_img_response_json = json.loads(get_img_response.text)
                get_img_status = get_img_response_json['status']

                image_is_generating = False
                if get_img_status == 200:
                    print(f'出图成功！{get_img_response_json}')
                    for img_idx, img_path in enumerate(get_img_response_json['imglist']):
                        print(f'img_path:{img_path}')
                        download_image_by_url(img_path, f'images/output/{img_idx}.{img_path.split(".")[-1]}')
                elif get_img_status == -200:
                    image_is_generating = True
                elif get_img_status == 404:
                    print("任务过期或不存在")
                elif  get_img_status == 500:
                    print("出图失败")

                time.sleep(10)
                request_cnt += 1
            except requests.exceptions.RequestException as e:
                print(f'轮询图片状态的请求失败:{e}')
    
except requests.exceptions.RequestException as e:
    print(f'生成图片的请求失败:{e}')

