import os

from dotenv import load_dotenv

load_dotenv(encoding="utf-8")

BOT_TOKEN = os.getenv("BOT_TOKEN")

URL_DATASETS = os.getenv("URL_DATASETS")
URL_ITEMS = os.getenv("URL_ITEMS")

TEXT_TITLE_TOP = os.getenv("TEXT_TITLE_TOP")

TEXT_STATS_DESCRIPTION = os.getenv("TEXT_STATS_DESCRIPTION")
TEXT_STATS_TODAY_FORMAT = os.getenv("TEXT_STATS_TODAY_FORMAT")
TEXT_STATS_TOTAL = os.getenv("TEXT_STATS_TOTAL")

TEXT_TOTAL_TITLE = os.getenv("TEXT_TOTAL_TITLE")
TEXT_BY_REGION_TITLE = os.getenv("TEXT_BY_REGION_TITLE")

TEXT_INFECTED_TOTAL = os.getenv("TEXT_INFECTED_TOTAL")
TEXT_INFECTED_NEW = os.getenv("TEXT_INFECTED_NEW")
TEXT_DEATHS = os.getenv("TEXT_DEATHS")
