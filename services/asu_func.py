import asyncio
import json
import time

import aiohttp
import requests
import structlog
import winsound
from aiohttp import ClientTimeout
from aiohttp_retry import RetryClient, ExponentialRetry

from config.bot_settings import settings, BASE_DIR, logger

data = {
    'refresh': '',
    'access': ''
}
retry_options = ExponentialRetry(attempts=3, start_timeout=5, factor=5)

async def get_token(count=0):
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
        # response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        async with aiohttp.ClientSession(timeout=ClientTimeout(5)) as session:
            retry_client = RetryClient(session, raise_for_status=False, retry_options=retry_options)
            async with retry_client.post(url, headers=headers, data=payload, ssl=False) as response:
                token_dict = await response.json()
                data['refresh'] = token_dict.get('refresh')
                data['access'] = token_dict.get('access')
                logger.info(f'data: {data}')
                return token_dict
    except aiohttp.client_exceptions.ClientConnectorError:
        logger.warning(f'Нет интернета. Попытка {count}')
        if count < 3:
            await asyncio.sleep(count * 5)
            return await get_token(count=count + 1)
    except Exception as err:
        logger.error(f'Ошибка получения токена по логину/паролю: {err}')
        print('----------')
        print(err, type(err), err.__class__)
        print('----------')


async def refresh_token() -> str:
    logger.info('Обновление токена')
    try:
        url = f"{settings.ASU_HOST}/api/v1/token/refresh/"
        payload = json.dumps({
            "refresh": data['refresh']
        })
        headers = {'Content-Type': 'application/json'}
        # response = requests.request("POST", url, headers=headers, data=payload, timeout=5)
        async with aiohttp.ClientSession(timeout=ClientTimeout(5)) as session:
            retry_client = RetryClient(session, raise_for_status=False, retry_options=retry_options)
            async with retry_client.post(url, headers=headers, data=payload, ssl=False) as response:
                if response.status == 401:
                    await get_token()
                    return data['access']
                token_dict = await response.json()
                access_token = token_dict.get('access')
                logger.debug(f'access_token: {access_token}')
                data['access'] = access_token
                logger.info(f'data: {data}')
                return access_token
    except Exception as err:
        logger.error(f'Ошибка обновления токена: {err}')


async def check_payment(payment_id, count=0) -> dict:
    url = f"{settings.ASU_HOST}/api/v1/payment_status/{payment_id}/"
    log = logger.bind(payment_id=payment_id)
    log.debug(f'Проверка статуса {url}')
    headers = {
        'Authorization': f'Bearer {data["access"]}'
    }
    try:
        # async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
        #     async with session.get(url, headers=headers, ssl=False) as response:
        async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
            retry_client = RetryClient(session, raise_for_status=False, retry_options=retry_options)
            async with retry_client.get(url, headers=headers, ssl=False) as response:
                if response.status == 200:
                    log.debug(f'{response.status}')
                    result = await response.json()
                    return result
                elif response.status == 401:
                    if count > 3:
                        return {'status': 'error check_payment'}
                    log.debug('Обновляем токен')
                    await asyncio.sleep(count)
                    # await refresh_token()
                    await get_token()
                    return await check_payment(payment_id, count=count + 1)
                elif response.status == 400:
                    log.error(f'Плохой статус: {response.status} {await response.text()}')

    except Exception as err:
        log.error(f'Ошибка: {err}')
        return {}


async def change_payment_status(payment_id: str, status: int, count=1, logger=structlog.get_logger('main'), phone_name=None, balance_i=0, turnover=0):
    """Смена статуса платежа
    Заявка создана - 0.
    Переданы данные карты - 3
    Назначена оператору - 4
    Бот взял в работу - 8
    Бот ввел данные карты в М10 - 5
    Мерч передал смс - 6.
    """
    log = logger.bind(payment_id=payment_id, operation=f'Смена статуса платежа на {status}')
    try:
        log.debug(f'Смена статуса платежа № {count} {payment_id} на: {status}')
        url = f'{settings.ASU_HOST}/api/v1/payment_status/{payment_id}/'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {data["access"]}'
                   }
        json_data = {
            'status': status,
            'phone_name': phone_name,
            'balance_i': balance_i,
            'turnover': turnover
        }
        # async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
        #     async with session.put(url, headers=headers, json=json_data, ssl=False) as response:
        async with aiohttp.ClientSession(timeout=ClientTimeout(10)) as session:
            retry_client = RetryClient(session, raise_for_status=False, retry_options=retry_options)
            async with retry_client.put(url, headers=headers, json=json_data, ssl=False) as response:
                text = await response.text()
                log.debug(f'{response.status} {text}')
                if response.status == 200:
                    log.debug(f'Статус {payment_id} изменен на {status}')
                    result = await response.json()
                    log.debug(result)
                    return result
                elif response.status == 401:
                    await get_token()
                    if count < 3:
                        return await change_payment_status(payment_id, status, count=count + 1, logger=logger)
                elif response.status in [400, 404]:
                    log.warning(f'Статус {payment_id} НЕ ИЗМЕНЕН!: {text}')
                    return
                else:
                    log.warning(f'Статус {payment_id} НЕ ИЗМЕНЕН! response: {response.status} {text}')
                    if count >= 3:
                        log.error(f'Ошибка при изменении статуса после 3 попыток {payment_id}: {text}')
                        return {'status': 'error check_payment'}
                    delay = count * 5
                    log.debug(f'ждем {delay}')
                    await asyncio.sleep(delay)
                    log.debug(f'Еще попытка сменить статус {payment_id}')
                    return await change_payment_status(payment_id, status, count=count+1, logger=logger)
    except Exception as err:
        log.error(f'Неизвестная Ошибка при смене статуса {count} раз {payment_id}: {type(err)} {err}')
        if count < 3:
            return await change_payment_status(payment_id=payment_id, status=status, count=count + 1, logger=logger, phone_name=phone_name)


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
                    return result.get('results', [])
                elif response.status == 401:
                    if count > 3:
                        logger.warning('Ошибка при проверке payments 3 раза')
                        return []
                    logger.debug('Обновляем токен')
                    await asyncio.sleep(count)
                    await refresh_token()
                    return await get_worker_payments(count=count + 1)
        return []
    except Exception as err:
        logger.warning(f'Ошибка при проверке payments. {err} {type(err)}{round(time.perf_counter() - start, 2)} c.')
        # winsound.PlaySound((BASE_DIR / 'media' / 'sound' / 'wrong.wav').as_posix(), winsound.SND_FILENAME)
        return []


async def main():
    # winsound.PlaySound((BASE_DIR / 'media' / 'sound' / 'wrong.wav').as_posix(), winsound.SND_FILENAME)
    await get_token()
    status = 9
    start = time.perf_counter()
    payment_id = 'f2eea28b-d477-47c2-b0fc-be02c270c6e1'
    p = await check_payment(payment_id)
    print(p, type(p))
    await change_payment_status(payment_id, status, logger=logger,
                                phone_name='xxx1',
                                balance_i='1', turnover='1'
                                )
    print(time.perf_counter() - start)

if __name__ == '__main__':
    # asyncio.run(get_token())
    # asyncio.run(refresh_token())
    asyncio.run(main())
