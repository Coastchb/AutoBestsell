curl --request POST \
     --url https://sandbox.walmartapis.com/v3/token \
     --header 'Authorization: Basic YTgxMGMxN2YtZjg2NC00OTI4LTkwNjUtMTliMjM0Y2IzNmM2OkFQYVhlaFNwdS1Za09mSFAtN0twNHIzSWY5X2JFQ21iYjZPZ29xWGdmeExwd2cxSTBsUHpxSGpySGtvc01MUXRTMnJrcUY2WExWTWJ2N05UQ1p6NXJGbw==' \
     --header 'Content-Type: application/x-www-form-urlencoded' \
     --header 'WM_QOS.CORRELATION_ID: b3261d2d-028a-4ef7-8602-633c23200af6' \
     --header 'WM_SVC.NAME: Walmart Marketplace' \
     --header 'accept: application/json' \
     --data grant_type=client_credentials

echo '\n\n'


curl --request POST \
     --url 'https://sandbox.walmartapis.com/v3/feeds?feedType=MP_ITEM' \
     --header 'WM_SEC.ACCESS_TOKEN:eyJraWQiOiIzMzZkODkyNi0zOWVmLTQ0OTctOWFlNy0wZTVlNDVhODNiOWMiLCJlbmMiOiJBMjU2R0NNIiwiYWxnIjoiZGlyIn0..pXd2ZjzUpbnkc5_f.77TSDSN9Oj5cqvBhEOdZj557RbSBcFxEKhI8mv6r1ekCO9CzU1KrfxwHhrlMA71gngK7qtfGn5TrNMad0KSqwtTAc6ItPTb03k7OoDDOfhIMfIxBiKlX2gSIgZ_59TP2YQ22iewwGlXGfzPtJGyNOe5OM8B0byUL8k6IxoVoAeapGtyMNhbEbzuMDB7o2V5_UTKAl3ZP7kDEQGUVEdJEuQtrArw5gz5-dy5kAtAEq1Yzc0yuI1a6cb1n-lA2xLr2SujNUjB_NtCRtEvY5YKOTYms_dcWn6cu0LsQn0WBpPfzZG2ZZvkAtY7cH-x-3FwDIlKqI3cp8RC5TiVdZWC02GkTM1_SThsTVQTMdMvlCb53CFUD90rUkJpIwNGWIZAGUOcuTdva8H0Sz_xpxCDqSl2x6JLlqvVnfQXMy1MYDo3UKcP7_27CnkIh1yp7hPX8C1P1Zl2npCHhuD4fIZIW16MTASjv2QomACH2Sc1g8B2_rqGSrLJvJW94W1wSfjgNkxoJEygfB5j6TXVA5LTMlYlgPGXjaW_Psvu4vvx4XYVcA2i02AO0NJ-9Zz8pVLQ8akY5fUTw7Ubs0YhunmDuay5jub-NbYl50A1iqdiCarfqxuc46vDT2dC_rATOdkSWl85wBXunUxCB9sF1caDzUdwL0CleAW_W6gS4lzSlHrvsF1O0ARvR1PjoymUl.SXIXQNl_3WB5SXSJmzAYSA' \
     --header 'WM_SVC.NAME: Walmart Marketplace' \
     --header 'WM_QOS.CORRELATION_ID: b3261d2d-028a-4ef7-8602-633c23200af6' \
     --header 'accept: application/json' \
     --header 'content-type: multipart/form-data' \
     --form file='items-feed/V4.8_MP_ITEM.json'