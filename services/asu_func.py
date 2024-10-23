import asyncio
import json
import time

import aiohttp
import requests
import winsound
from aiohttp import ClientTimeout

from config.bot_settings import logger, settings, BASE_DIR

data = {
    'refresh': '',
    'access': ''
}


async def get_token():
    logger.info(f'Получение первичного токена по логину {settings.ASUPAY_LOGIN}')
    try:
        login = settings.ASUPAY_LOGIN
        password = settings.ASUPAY_PASSWORD
        url = f"{settings.ASU_HOST}/api/v1/token/"
        payload = json.dumps({
            "username": login,
            "password": password
        })
        headers = {'Content-Type': 'application/json'}
        print(url)
        response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        logger.info(response.status_code)
        token_dict = response.json()
        data['refresh'] = token_dict.get('refresh')
        data['access'] = token_dict.get('access')
        logger.info(f'data: {data}')
        return token_dict
    except Exception as err:
        logger.error(f'Ошибка получения токена по логину/паролю: {err}')
        raise err


async def refresh_token() -> str:
    logger.info('Обновление токена')
    try:
        url = f"{settings.ASU_HOST}/api/v1/token/refresh/"
        payload = json.dumps({
            "refresh": data['refresh']
        })
        headers = {'Content-Type': 'application/json'}
        response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        if response.status_code == 401:
            await get_token()
            return data['access']
        token_dict = response.json()
        print(token_dict)
        access_token = token_dict.get('access')
        logger.debug(f'access_token: {access_token}')
        data['access'] = access_token
        logger.info(f'data: {data}')
        return access_token
    except Exception as err:
        logger.error(f'Ошибка обновления токена: {err}')


async def check_payment(payment_id, count=0) -> dict:
    url = f"{settings.ASU_HOST}/api/v1/payment_status/{payment_id}/"
    logger.debug(f'Проверка статуса {url}')
    headers = {
        'Authorization': f'Bearer {data["access"]}'
    }
    try:
        async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    logger.debug(f'{response.status}')
                    result = await response.json()
                    return result
                elif response.status == 401:
                    if count > 3:
                        return {'status': 'error check_payment'}
                    logger.debug('Обновляем токен')
                    await asyncio.sleep(count)
                    await refresh_token()
                    return await check_payment(payment_id, count=count + 1)
    except Exception as err:
        logger.error(f'Ошибка: {err}')


async def change_payment_status(payment_id: str, status: int):
    """Смена статуса платежа"""
    try:
        logger.debug(f'Смена статуса платежа {payment_id} на: {status}')
        url = f'{settings.ASU_HOST}/api/v1/payment_status/{payment_id}/'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {data["access"]}'
                   }
        json_data = {
            'status': status,
        }
        async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
            async with session.put(url, headers=headers, json=json_data, ssl=False) as response:
                if response.status == 200:
                    logger.debug(f'Статус {payment_id} изменен на {status}')
                else:
                    logger.warning(f'Статус {payment_id} НЕ ИЗМЕНЕН! {response.status}')
                logger.debug(f'response.status: {response.status}')
                result = await response.json()
                logger.debug(result)
        return result
    except Exception as err:
        logger.error(f'Ошибка при смене статуса платежа: {err}')
        # raise err


async def get_worker_payments(count=0) -> list:
    # Проверка назначенных платежей
    start = time.perf_counter()
    url = f"{settings.ASU_HOST}/api/v1/worker_payments/"
    logger.debug(f'Проверка payments')
    headers = {
        'Authorization': f'Bearer {data["access"]}'
    }
    try:
        async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
            async with session.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    logger.debug(f'{response.status}. {round(time.perf_counter() - start, 2)} c.')
                    result = await response.json()
                    return result.get('results')
                elif response.status == 401:
                    if count > 3:
                        logger.warning('Ошибка при проверке payments 3 раза')
                        return []
                    logger.debug('Обновляем токен')
                    await asyncio.sleep(count)
                    await refresh_token()
                    return await get_worker_payments(count=count + 1)
    except Exception as err:
        logger.warning(f'Ошибка при проверке payments: {err}. {round(time.perf_counter() - start, 2)} c.')
        winsound.PlaySound((BASE_DIR / 'media' / 'sound' / 'wrong.wav').as_posix(), winsound.SND_FILENAME)
        return []


async def main():
    # status = 9
    # p = await check_payment('6e6f23b4-f049-4b74-ac55-235ee61968d6')
    # print(p)
    ps = await get_worker_payments()
    print(ps)
    # await change_payment_status('6e6f23b4-f049-4b74-ac55-235ee61968d6', status)


if __name__ == '__main__':
    asyncio.run(get_token())
    asyncio.run(refresh_token())
    asyncio.run(main())
