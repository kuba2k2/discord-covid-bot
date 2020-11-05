import time

from discord import Embed, Guild
from discord.ext import commands
from discord.ext.commands.context import Context

from covid import Covid
from database import Database
from settings import *

database = Database()
bot = commands.Bot(command_prefix="!")
covid = Covid(URL_ITEMS)


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
    if not today or not yesterday:
        return
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


async def covid_setup(ctx: Context, *args):
    if len(args) == 1:
        await ctx.send("Usage: `!covid setup <country>`")
        return

    country = await covid.get_dataset_id(country=args[1])
    if country is None:
        await ctx.send(f"The country name `{args[1]}` is invalid.")
        return
    (country_name, dataset_id) = country

    database.add_guild(ctx.guild, country_name, dataset_id)
    await ctx.send(f"The guild is now set up for country `{country_name}`. "
                   "Try it using `!covid`.\n"
                   "Set up daily statistics for a channel using `!covid notify`.")


async def covid_get(ctx: Context, time_start: float, country_name: str, dataset_id: str):
    items = await covid.get_items(dataset_id=dataset_id, limit=3, descending=True)

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

    time_end = time.time() * 1000
    embed.set_footer(text=f"{int(time_end - time_start)} ms")

    await ctx.send(embed=embed)


@bot.command(name="covid")
async def main(ctx: Context, *args):
    time_start = time.time() * 1000
    try:
        if args:
            if args[0] == "setup":
                await covid_setup(ctx, args)
                return
            elif args[0] == "notify":
                await covid_setup(ctx, args)
                return
            else:
                country = await covid.get_dataset_id(country=args[0])
                if country is None:
                    await ctx.send(f"The country name `{args[0]}` is invalid.")
                    return
                (country_name, dataset_id) = country
        else:
            config = database.get_by_guild(ctx.guild)
            if not config or not config[0]["datasetId"]:
                await ctx.send("Configure the guild first using `!covid setup <country>`.")
                return
            config = config[0]
            country_name = config["countryName"]
            dataset_id = config["datasetId"]

        async with ctx.channel.typing():
            await covid_get(ctx, time_start, country_name, dataset_id)
    except Exception as e:
        await ctx.send(str(e))


@bot.event
async def on_guild_join(guild: Guild):
    database.add_guild(guild)


@bot.event
async def on_guild_remove(guild: Guild):
    database.remove_guild(guild)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
