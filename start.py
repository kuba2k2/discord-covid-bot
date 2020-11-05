from discord import Embed
from discord.ext import commands
from discord.ext.commands.context import Context

from covid import Covid
from settings import *

bot = commands.Bot(command_prefix="!")
covid = Covid("https://api.apify.com/v2/datasets/L3VCmhMeX0KUQeJto/items")


def get_field_value(
    prefix: str, count: int, diff: int, show_diff: bool, bold: bool = False
) -> str:
    diff = diff if diff < 0 else f"+{diff}"
    diff = f" ({diff})" if show_diff else ""
    bold = "**" if bold else ""
    return f"{prefix}: __{bold}{count}{bold}__{diff}"


def add_counts(embed: Embed, counts: list, show_diff: bool):
    today = counts[0]
    yesterday = counts[1]
    title = TEXT_TOTAL_TITLE

    keys = {
        "infected": TEXT_INFECTED_NEW if show_diff else TEXT_INFECTED_TOTAL,
        "deaths": TEXT_DEATHS,
    }.items()
    first = True
    for key, prefix in keys:
        day_diff = today[key] - yesterday[key]
        embed.add_field(
            name=title if first else "\u200b",
            value=get_field_value(prefix, today[key], day_diff, show_diff, show_diff),
            inline=True,
        )
        first = False


def add_region_counts(embed: Embed, counts: list, show_diff: bool, limit: int = None):
    today = counts[0]["byRegion"]
    yesterday = counts[1]["byRegion"]
    title = TEXT_BY_REGION_TITLE

    keys = ["infected"]
    first = True
    for key in keys:
        regions = list(
            {
                "name": region["region"],
                "count": region[key],
                "diff": region[key] - yesterday[index][key],
            }
            for index, region in enumerate(today)
        )
        regions.sort(key=lambda x: -x["count"])
        text = "\n".join(
            f"{index + 1}. {get_field_value(region['name'], region['count'], region['diff'], show_diff)}"
            for index, region in enumerate(regions)
            if not limit or index < limit
        )
        embed.add_field(
            name=title if first else "\u200b",
            value=text,
            inline=False,
        )


@bot.command(name="covid")
async def main(ctx: Context):
    async with ctx.channel.typing():
        items = await covid.get_items(limit=3, descending=True)

        counts = covid.get_counts(items)
        diffs = covid.get_diffs(items)
        counts.reverse()
        diffs.reverse()

        today_date = diffs[0]["date"]

        embed = Embed(title=today_date.strftime(TEXT_STATS_TODAY_FORMAT))
        embed.description = TEXT_STATS_DESCRIPTION
        embed.set_author(
            name=TEXT_TITLE_TOP,
            icon_url="https://cdn.discordapp.com/embed/avatars/4.png",
        )

        add_counts(embed, diffs, show_diff=True)
        add_region_counts(embed, diffs, show_diff=True, limit=5)
        embed.add_field(
            name="\u200b",
            value=TEXT_STATS_TOTAL,
            inline=False,
        )
        add_counts(embed, counts, show_diff=False)
        # add_region_counts(embed, counts, show_diff=False, limit=5)

        await ctx.send(embed=embed)


if __name__ == "__main__":
    bot.run(BOT_TOKEN)
