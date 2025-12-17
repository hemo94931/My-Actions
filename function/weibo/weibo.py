import json
import requests
import random
import time
from urllib.parse import urlparse, parse_qs
# from notify import send, pushplus_bot
import re
import os

API_URL = "https://api.weibo.cn/2/cardlist"
SIGN_URL = "https://api.weibo.cn/2/page/button"

def send_request(url, params, headers):
    response = requests.get(url, params=params, headers=headers)
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            return None
    return None

def extract_params(url):
    parsed_url = urlparse(url)
    params_from_url = parse_qs(parsed_url.query)
    params_from_url = {k: v[0] for k, v in params_from_url.items()}
    return params_from_url

def get_card_type_11(params, headers):
    data = send_request(API_URL, params, headers)
    if data is None:
        return []
    cards = data.get("cards", [])
    card_type_11_info = []
    for card in cards:
        if card.get("card_type") == 11:
            card_group = card.get("card_group", [])
            for item in card_group:
                if item.get("card_type") == 8 and item.get("buttons")[0]["name"] in ["已关注", "已签", "签到"]:
                    info = {
                        "scheme": item.get("scheme"),
                        "title_sub": item.get("title_sub")
                    }
                    card_type_11_info.append(info)
    return card_type_11_info

def sign_in(headers, base_params, scheme):
    params = extract_params(scheme)
    request_url = f"http://i.chaohua.weibo.com/mobile/shproxy/active_fcheckin?cardid=bottom_one_checkin&container_id={params['containerid']}&pageid={params['containerid']}&scene_id=bottom_mine_checkin&scheme_type=1"
    sign_in_params = {
        "aid": base_params.get("aid"),
        "b": base_params.get("b"),
        "c": base_params.get("c"),
        "from": base_params.get("from"),
        "ft": base_params.get("ft"),
        "gsid": base_params.get("gsid"),
        "lang": base_params.get("lang"),
        "launchid": base_params.get("launchid"),
        "networktype": base_params.get("networktype"),
        "s": base_params.get("s"),
        "sflag": base_params.get("sflag"),
        "skin": base_params.get("skin"),
        "ua": base_params.get("ua"),
        "v_f": base_params.get("v_f"),
        "v_p": base_params.get("v_p"),
        "wm": base_params.get("wm"),
        "fid": "232478_-_one_checkin",
        "lfid": base_params.get("lfid"),
        "luicode": base_params.get("luicode"),
        "moduleID": base_params.get("moduleID"),
        "orifid": base_params.get("orifid"),
        "oriuicode": base_params.get("oriuicode"),
        "request_url": request_url,
        "source_code": base_params.get("source_code"),
        "sourcetype": "page",
        "uicode": base_params.get("uicode"),
        "ul_sid": base_params.get("ul_sid"),
        "ul_hid": base_params.get("ul_hid"),
        "ul_ctime": base_params.get("ul_ctime"),
    }
    data = send_request(SIGN_URL, sign_in_params, headers)
    return data

headers = {
    "Accept": "*/*",
    "User-Agent": "Weibo/81434 (iPhone; iOS 17.0; Scale/3.00)",
    "SNRT": "normal",
    "X-Sessionid": "6AFD786D-9CFA-4E18-BD76-60D349FA8CA2",
    "Accept-Encoding": "gzip, deflate",
    "X-Validator": "QTDSOvGXzA4i8qLXMKcdkqPsamS5Ax1wCJ42jfIPrNA=",
    "Host": "api.weibo.cn",
    "x-engine-type": "cronet-98.0.4758.87",
    "Connection": "keep-alive",
    "Accept-Language": "en-US,en",
    "cronet_rid": "6524001",
    "Authorization": "",
    "X-Log-Uid": "5036635027",
}

def pushplus_bot(title: str, content: str, token=None) -> None:
    """
    通过 push+ 推送消息。
    """
    if token is None:
        print("PUSHPLUS 服务的 PUSH_PLUS_TOKEN 未设置!!\n取消推送")
        return
    print("PUSHPLUS 服务启动")

    url = "http://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content,
        "topic": "",
    }
    body = json.dumps(data).encode(encoding="utf-8")
    headers = {"Content-Type": "application/json"}
    response = requests.post(url=url, data=body, headers=headers).json()

    if response["code"] == 200:
        print("PUSHPLUS 推送成功！")

    else:
        url_old = "http://pushplus.hxtrip.com/send"
        headers["Accept"] = "application/json"
        response = requests.post(url=url_old, data=body, headers=headers).json()

        if response["code"] == 200:
            print("PUSHPLUS(hxtrip) 推送成功！")

        else:
            print("PUSHPLUS 推送失败！")

if __name__ == "__main__":
    if os.environ.get('WEIBO_COOKIE'):
        urls = os.environ.get('WEIBO_COOKIE').split("\n")
    else:
        print("未填写微博Cookie")
        exit(0)

    if os.environ.get('PUSH_TOKEN'):
        tokens = os.environ.get('PUSH_TOKEN').split("\n")
    else:
        print("未填写PLUS TOKEN")
        exit(0)

    resultStr = f"超话列表："
    for url in urls:
        params = extract_params(url)
        # 获取超话列表
        card_type_11_info = get_card_type_11(params, headers)
        # 打印获取的超话列表信息
        super_topic_list = "\n".join([f"    {info['title_sub']}" for info in card_type_11_info])
        print("超话列表：")
        print(super_topic_list)
        
        # 依次进行签到
        result_message = "\n签到结果：\n"
        for info in card_type_11_info:
            if info['title_sub'] != '周深':
                continue
            
            result = sign_in(headers, params, info['scheme'])
            # 判断签到结果
            if result and result.get('msg') == '已签到':
                status = '成功'
            else:
                status = '失败'
            result_message += f"    {info['title_sub']}超话：{status}\n"
            time.sleep(random.randint(1, 3))  # 避免请求过于频繁

        print(result_message)
        resultStr += f"\n{super_topic_list}\n{result_message}"
        resultStr += f"\n{super_topic_list}\n"

    for token in tokens:
        pushplus_bot("微博签到结果:", resultStr, token)
