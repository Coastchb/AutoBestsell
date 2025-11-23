#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import hashlib
import json
import requests

appid = 'dh2511ujbi5lzy3z84'
appsecret = 'e22557f526d04a387e104352f723c99d'
timestamp = int(time.time())
version = "2.0.0"

authorization = {
    "version": version,
    "timestamp": timestamp,
    "appid": appid,
    "sign": hashlib.md5(
        f"{appid}{timestamp}{version}{appsecret}".encode("utf-8")
    ).hexdigest(),
}

headers = {
    "authorization": json.dumps(authorization),
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
}

# 此处以 文生图 接口为示例
url = "https://dhd.douhuiai.com/api/aiart/doGentxt2img"

# 请求参数
data = {
    "dhAiType": "txt2img",
    "dhPrompt": "一群小孩追着风筝跑",
    "dhModel": 12157,
    "dhImgSize": 304,
    "dhImgNum": 1,
}

print("请求参数：", data)
print("请求头：", headers)

try:
    response = requests.post(url, headers=headers, data=data, timeout=30)
    print(response.text)
except requests.exceptions.RequestException as e:
    print("Request failed: %s", e)
