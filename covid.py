import asyncio
from datetime import datetime
from typing import Union, Tuple

import aiohttp

from settings import URL_DATASETS

tz = datetime.now().astimezone().tzinfo


def _get_date(date: str) -> datetime:
    return datetime.fromisoformat(date.replace("Z", "+00:00")).astimezone(tz)


class Covid:
    def __init__(self, base_url) -> None:
        self._session = aiohttp.ClientSession()
        self._base_url = base_url

    async def get_dataset_id(self, country: str) -> Union[Tuple[str, str], None]:
        try:
            async with self._session.get(URL_DATASETS) as response:
                country = next(
                    item
                    for item in await response.json()
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
        items.sort(key=lambda x: x["infected"])
        result = []

        for item in items:
            count = {
                "date": _get_date(item["lastUpdatedAtApify"]),
                "infected": item["infected"],
                "deaths": item["deceased"],
                "byRegion": [],
            }
            if "infectedByRegion" in item:
                for region in item["infectedByRegion"]:
                    count["byRegion"].append(
                        {
                            "region": region["region"],
                            "infected": region["infectedCount"],
                            "deaths": region["deceasedCount"],
                        }
                    )
            result.append(count)
        return result

    def get_diffs(self, items: list) -> list:
        items.sort(key=lambda x: x["infected"])
        result = []
        i = iter(items)
        prev_item = next(i)

        for item in i:
            diff = {
                "date": _get_date(item["lastUpdatedAtApify"]),
                "infected": item["infected"] - prev_item["infected"],
                "deaths": item["deceased"] - prev_item["deceased"],
                "byRegion": [],
            }
            if "infectedByRegion" in item:
                for index, region in enumerate(item["infectedByRegion"]):
                    prev_region = prev_item["infectedByRegion"][index]
                    diff["byRegion"].append(
                        {
                            "region": region["region"],
                            "infected": region["infectedCount"]
                            - prev_region["infectedCount"],
                            "deaths": region["deceasedCount"]
                            - prev_region["deceasedCount"],
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
