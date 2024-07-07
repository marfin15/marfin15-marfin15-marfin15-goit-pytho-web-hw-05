import aiohttp
import asyncio
import datetime
import json
from typing import List, Dict, Any


class CurrencyFetcher:
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?json&date="

    def __init__(self, days: int):
        self.days = days
        self.dates = self.get_dates()

    def get_dates(self) -> List[str]:
        today = datetime.datetime.today()
        return [(today - datetime.timedelta(days=i)).strftime("%d.%m.%Y") for i in range(1, self.days + 1)]

    async def fetch_currency_rate(self, session: aiohttp.ClientSession, date: str) -> Dict[str, Any]:
        url = self.BASE_URL + date
        try:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return self.parse_response(date, data)
        except aiohttp.ClientError as e:
            return {date: f"Error fetching data: {str(e)}"}

    def parse_response(self, date: str, data: Dict[str, Any]) -> Dict[str, Any]:
        rates = {date: {}}
        for rate in data.get('exchangeRate', []):
            if rate.get('currency') in ['EUR', 'USD']:
                rates[date][rate['currency']] = {
                    'sale': rate.get('saleRate', rate.get('saleRateNB')),
                    'purchase': rate.get('purchaseRate', rate.get('purchaseRateNB'))
                }
        return rates

    async def fetch_all_rates(self) -> List[Dict[str, Any]]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_currency_rate(session, date) for date in self.dates]
            return await asyncio.gather(*tasks)


class CurrencyRateService:
    def __init__(self, days: int):
        self.days = days

    async def get_currency_rates(self) -> List[Dict[str, Any]]:
        fetcher = CurrencyFetcher(self.days)
        return await fetcher.fetch_all_rates()


def main(days: int):
    if not 1 <= days <= 10:
        print("Please enter a number of days between 1 and 10.")
        return

    service = CurrencyRateService(days)
    rates = asyncio.run(service.get_currency_rates())
    print(json.dumps(rates, indent=2))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python main.py <number_of_days>")
    else:
        try:
            days = int(sys.argv[1])
            main(days)
        except ValueError:
            print("Please enter a valid number of days.")