import sys
from datetime import datetime, timedelta

import httpx
import asyncio
import platform

API_URL = 'https://api.privatbank.ua/p24api/exchange_rates?date='


class HttpError(Exception):
    pass


async def request(url: str):
    """Виконує асинхронний GET-запит до вказаного URL-адреси і повертає результат у форматі JSON."""
    timeout = httpx.Timeout(2.0, read=None) # Встановлюється таймаут для запиту. У цьому випадку таймаут встановлено
    # на 2 секунди.
    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=timeout)
        if r.status_code == 200:
            result = r.json()
            return result
        else:
            raise HttpError(f"Error status: {r.status_code} for {url}")


async def get_date(input_day: int) -> list[str]:
    result_list = [(datetime.now() - timedelta(days=index - 1)).strftime("%d.%m.%Y") for index in
                   range(1, input_day + 1)]
    return result_list


async def get_data(dates_list: list):
    """Виконує асинхронне отримання даних з вказаних URL-адрес за допомогою списку дат."""
    exchange_rate_data = [request(f'{API_URL}{date}') for date in dates_list]
    results = await asyncio.gather(*exchange_rate_data)
    result_list = list()
    for r in results:
        result = await normalize_response(r)
        result_list.append(result)
    return result_list


async def normalize_response(response: dict):
    res_dict = dict()
    res_dict_inner = dict()
    cur_date = response.get('date')
    exchange_rate = response.get('exchangeRate')
    for i in exchange_rate:
        if i['currency'] == 'EUR':
            res_dict_inner.update({i['currency'] : {'sale': i['saleRateNB'], 'purchase': i['purchaseRateNB']}})
        elif i['currency'] == 'USD':
            res_dict_inner.update({i['currency'] : {'sale': i['saleRateNB'], 'purchase': i['purchaseRateNB']}})
        res_dict[cur_date] = res_dict_inner
    return res_dict


async def main():
    """основна функція в якій реалізована логіка """
    if len(sys.argv) < 2:
        sys.exit("You need enter Days.")
    get_argv = int(sys.argv[1])
    if get_argv > 10:
        sys.exit(f"Days {get_argv} more then 10.")
    dates_list = await get_date(get_argv)
    try:
        result = await get_data(dates_list=dates_list)
        print(result)  # Вивід в консоль списку, без трансформації в JSON
    except HttpError as err:
        print(err)
        return None


if __name__ == '__main__':
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
