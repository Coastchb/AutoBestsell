### 一、踩坑
#### 1、沃尔玛
（1）利用client id和client secret获取access_token，参考官方的指引：https://developer.walmart.com/us-marketplace/reference/tokenapi
将client id和client secret用:连接，然后base64编码后，加上"Basic "前缀，作为"Authorization"参数的值

（2）调用接口批量上架商品，出现以下情况：
<br>**响应状态码：401**
<br>响应内容：{"error":[{"code":"UNAUTHORIZED.GMP_GATEWAY_API","field":"UNAUTHORIZED","description":"Unauthorized","info":"Unauthorized token or incorrect authorization header. Please verify correct format: \"Authorization: Basic Base64Encode(clientId:clientSecret)\" For more information, see https://developer.walmart.com/#/apicenter/marketPlace/latest#apiAuthentication.","severity":"ERROR","category":"DATA","causes":[],"errorIdentifiers":{}}]}
<br>解析后的 JSON 响应：{'error': [{'code': 'UNAUTHORIZED.GMP_GATEWAY_API', 'field': 'UNAUTHORIZED', 'description': 'Unauthorized', 'info': 'Unauthorized token or incorrect authorization header. Please verify correct format: "Authorization: Basic Base64Encode(clientId:clientSecret)" For more information, see https://developer.walmart.com/#/apicenter/marketPlace/latest#apiAuthentication.', 'severity': 'ERROR', 'category': 'DATA', 'causes': [], 'errorIdentifiers': {}}]}

问题解法：要用https://marketplace.walmartapis.com/v3/feeds，不要用https://sandbox.walmartapis.com/v3/feeds
（但是奇怪的是，报错信息似乎在提示access_token的错误）