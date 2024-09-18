import time

import requests
import base64
import json


def restart(device, token, headers):
    device_url = f'http://localhost:8090/TotalControl/v2/devices/device@{device}'
    url = f'{device_url}/apps/com.m10?state=restart&token={token}'
    res = requests.post(url)
    print('result:', res.text)
    time.sleep(1)

    # Ждем экран кода:
    req_data = {"token": token,
                'params':
                    '{query:"TP:more&&D:7"}'
                }
    value = None
    while not isinstance(value, dict):
        url = f'{device_url}/sendAai'
        res = requests.post(url, json.dumps(req_data))
        json_res = res.json()
        value = json_res.get('value')
        print(value)
        if isinstance(value, dict):
            if value.get('count') == 1:
                break
        print(res.json(), 'Ждем панель')
        time.sleep(1)
    time.sleep(1)
    for i in '7350':
        req_data = {"token": token,
                    'params':
                        f'{{action:"click",query:"TP:more&&D:{i}"}}'
                    }
        res = requests.post(url, json.dumps(req_data), headers=headers)
        print('result:', res.text)

    # Ждем экран кода:
    req_data = {"token": token,
                'params':
                    '{query:"TP:all&&D:Top up"}'
                }
    value = None
    while not isinstance(value, dict):
        url = f'{device_url}/sendAai'
        res = requests.post(url, json.dumps(req_data), headers=headers)
        json_res = res.json()
        value = json_res.get('value')
        print(value)
        if isinstance(value, dict):
            if value.get('count') == 1:
                break
        print(res.json(), 'Ждем панель')
        time.sleep(1)
    time.sleep(1)
    req_data = {"token": token,
                'params':
                    '{action:"click",query:"TP:all&&D:Top up"}'
                }
    res = requests.post(url, json.dumps(req_data), headers=headers)
    print(res.text)

def main():
    s = 'sigma:177AE5C7'
    userpass = base64.b64encode(s.encode('utf-8'))
    print('encode:', userpass)
    if userpass:
        url = "http://localhost:8090/TotalControl/v2/login"
        device = 1021923620
        headers = {
            'Authorization': userpass
        }
        res = requests.get(url, headers=headers)
        print('login:', res.text)
        if res.text:
            # 解析JSON字符串
            parsed_data = json.loads(res.text)
            token = parsed_data['value']['token']
            print('token:', token)
            if token:
                restart(device, token, headers)
                headers = {}
                device_url = f'http://localhost:8090/TotalControl/v2/devices/device@{device}'
                # Ввод суммы
                url = f'{device_url}/sendAai'
                req_data = {"token": token,
                            'params': '{action:["click","sleep(500)","setText(123)"],query:"TP:findText,Top-up wallet&&OY:1"}'}

                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Ввод суммы:', res.text)
                time.sleep(1)
                # Нажатие продолжить
                req_data = {"token": token,
                            'params':
                                '{action:"click",query:"TP:findText,Continue"}'
                            }
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result продолжить:', res.text)
                time.sleep(1)

                # Ждем поле карты
                req_data = {"token": token,
                            'params':
                            # '{query:"TP:more&&T:Please enter card details"}'
                            '{query:"TP:more&&R:cardPan"}'

                            }
                value = None
                count = 1
                while not isinstance(value, dict):
                    req_data = {"token": token,
                                'params':
                                # '{query:"TP:more&&T:Please enter card details"}'
                                    '{query:"TP:more&&R:cardPan"}'

                                }
                    url = f'{device_url}/sendAai'
                    res = requests.post(url, json.dumps(req_data), headers=headers)
                    print('result поиска карты:', res.text)
                    json_res = res.json()
                    value = json_res.get('value')
                    print(value)
                    if isinstance(value, dict):
                        if value.get('count') == 1:
                            break
                    time.sleep(1)
                    count += 1
                    if count > 10 and count % 3 == 0:
                        url = f'{device_url}/screen/inputs'
                        req_data = {"token": token, "coord": "[[600,300],[610,310]]"}
                        res = requests.post(url, json.dumps(req_data), headers=headers)
                        print('result клика:', res.text)



                # # Клик на чекбокс
                # time.sleep(1)
                # req_data = {"token": token,
                #             'params':
                #                 '{action:"click",query:"TP:more&&R:Сохранить карту"}'
                #             }
                # url = f'{device_url}/sendAai'
                # res = requests.post(url, json.dumps(req_data), headers=headers)
                # print('result Клик на чекбокс:', res.text)

                # Ввод карты
                # Клик на поле карты
                req_data = {"token": token,
                            'params':
                                '{action:["click","sleep(1000)","click","sleep(500)"],query:"TP:more&&R:cardPan"}'
                            }
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Клик на поле карты:', res.text)

                # Вставка номера карты
                url = f'{device_url}/screen/texts'
                req_data = {"token": token,
                            "text": "5462 6312 1882 6164"
                            }
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Вставка номера карты:', res.text)

                # Ввод exp
                # Клик на exp
                req_data = {"token": token,
                            'params':
                                '{action:"click",query:"TP:more&&R:expDate"}'
                            }
                url = f'{device_url}/sendAai'
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Клик на exp:', res.text)
                # time.sleep(1)
                # Вставка exp
                url = f'{device_url}/screen/texts'
                req_data = {"token": token,
                            "text": "12/26"
                            }
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Вставка exp:', res.text)
                # time.sleep(1)

                # Ввод cvv
                # Клик на cvv
                req_data = {"token": token,
                            'params':
                                '{action:"click",query:"TP:more&&R:cvv"}'
                            }
                url = f'{device_url}/sendAai'
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Клик на cvv:', res.text)

                # Вставка cvv
                url = f'{device_url}/screen/texts'
                req_data = {"token": token,
                            "text": "123"
                            }
                res = requests.post(url, json.dumps(req_data), headers=headers)
                print('result Вставка cvv:', res.text)


if __name__ == '__main__':
    count = 0
    while True:
        main()
        count += 1
        print(f'закончено циклов: {count}')
        time.sleep(1)