import asyncio
from datetime import datetime
from time import time
from typing import Union, Tuple

import aiohttp

from settings import URL_DATASETS

tz = datetime.now().astimezone().tzinfo

BY_REGION = 0
REGION = 1
INFECTED = 2
DEATHS = 3
RECOVERED = 4
TESTED = 5


def _get_date(date: str) -> datetime:
    return datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(tz)


def v(obj: dict, type: int):
    keys = []
    if type == BY_REGION:
        keys = ["infectedByRegion", "casesByState"]
    elif type == REGION:
        keys = ["region", "name"]
    elif type == INFECTED:
        keys = ["infected", "infectedCount", "casesReported", "totalCases"]
    elif type == DEATHS:
        keys = ["deceased", "deceasedCount", "deaths", "deathCount", "totalDeaths"]
    elif type == RECOVERED:
        keys = ["recovered", "recoveredCount", "discharged"]
    elif type == TESTED:
        keys = ["tested", "testedCount", "testsPerformed"]
    try:
        return next(obj[key] for key in keys if key in obj)
    except StopIteration:
        return None


class Covid:
    def __init__(self, base_url) -> None:
        self._session = aiohttp.ClientSession()
        self._base_url = base_url
        self._country_cache = None
        self._country_cache_time = None

    async def get_dataset_id(self, country: str) -> Union[Tuple[str, str], None]:
        try:
            if not self._country_cache_time or time() - self._country_cache_time > 24*60*60:
                async with self._session.get(URL_DATASETS) as response:
                    self._country_cache = await response.json()
                    self._country_cache_time = time()

            country = next(
                item
                for item in self._country_cache
                if item["country"].lower() == country.lower()
            )
            return (
                country["country"],
                country["historyData"].split("/")[
                    5
                ],  # just don't ask; a part of the URL
            )
        except:
            pass
        return None

    async def get_items(
        self, dataset_id: str, limit: int = None, descending: bool = True
    ) -> list:
        params = {
            "limit": limit,
            "desc": 1 if descending else 0,
            "clean": 1,
            "format": "json",
        }
        url = (
            self._base_url.replace("$ID", dataset_id)
            + "?"
            + "&".join(
                param[0] + "=" + str(param[1]) for param in params.items() if param[1]
            )
        )

        async with self._session.get(url) as response:
            return await response.json()

    def get_counts(self, items: list) -> list:
        items.sort(key=lambda x: v(x, INFECTED))
        result = []

        for item in items:
            count = {
                "date": _get_date(item["lastUpdatedAtApify"]),
                "infected": v(item, INFECTED),
                "deaths": v(item, DEATHS),
                "byRegion": [],
            }
            by_region = v(item, BY_REGION)
            if by_region:
                for region in by_region:
                    count["byRegion"].append(
                        {
                            "region": v(region, REGION),
                            "infected": v(region, INFECTED),
                            "deaths": v(region, DEATHS),
                        }
                    )
            result.append(count)
        return result

    def get_diffs(self, items: list) -> list:
        items.sort(key=lambda x: v(x, INFECTED))
        result = []
        i = iter(items)
        prev_item = next(i)

        for item in i:
            diff = {
                "date": _get_date(item["lastUpdatedAtApify"]),
                "infected": (v(item, INFECTED) or 0) - (v(prev_item, INFECTED) or 0),
                "deaths": (v(item, DEATHS) or 0) - (v(prev_item, DEATHS) or 0),
                "byRegion": [],
            }
            by_region = v(item, BY_REGION)
            prev_by_region = v(prev_item, BY_REGION)
            if by_region:
                for index, region in enumerate(by_region):
                    prev_region = prev_by_region[index]
                    diff["byRegion"].append(
                        {
                            "region": v(region, REGION) or "",
                            "infected": (v(region, INFECTED) or 0) - (v(prev_region, INFECTED) or 0),
                            "deaths": (v(region, DEATHS) or 0) - (v(prev_region, DEATHS) or 0),
                        }
                    )
            result.append(diff)
            prev_item = item
        return result


async def main():
    covid = Covid("https://api.apify.com/v2/datasets/L3VCmhMeX0KUQeJto/items")
    items = await covid.get_items(limit=3, descending=True)
    counters = covid.get_counts(items)
    diffs = covid.get_diffs(items)
    # print()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
