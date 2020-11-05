import sqlite3
from typing import List

from discord import User, Guild, TextChannel


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class Database:
    def __init__(self, filename: str = "covid.db") -> None:
        self._conn = sqlite3.connect(filename)
        self._conn.row_factory = dict_factory

    def add_guild(self, guild: Guild, country_name: str = None, dataset_id: str = None):
        c = self._conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO guild (guildId) VALUES (?);",
            (guild.id,),
        )
        if dataset_id:
            c.execute(
                "UPDATE guild SET countryName = ?, datasetId = ? WHERE guildId = ?;",
                (country_name, dataset_id, guild.id),
            )
        self._conn.commit()

    def remove_guild(self, guild: Guild):
        c = self._conn.cursor()
        c.execute(
            "DELETE FROM guild WHERE guildId = ?;",
            (guild.id,),
        )
        self._conn.commit()

    def add_channel(self, user: User, channel: TextChannel, run_at: str):
        c = self._conn.cursor()
        c.execute(
            "REPLACE INTO channel "
            "(guildId, channelId, addedById, addedByName, runAt) "
            "VALUES (?, ?, ?, ?, ?);",
            (
                channel.guild.id,
                channel.id,
                user.id,
                f"{user.name}#{user.discriminator}",
                run_at,
            ),
        )
        self._conn.commit()

    def get_by_guild(self, guild: Guild) -> List[dict]:
        c = self._conn.cursor()
        c.execute(
            "SELECT channel.guildId, channelId, countryName, datasetId, mentionEveryone, runAt "
            "FROM guild LEFT JOIN channel "
            "WHERE guild.guildId = ?;",
            (guild.id,),
        )
        return c.fetchall()

    def get_by_channel(self, channel: TextChannel) -> dict:
        c = self._conn.cursor()
        c.execute(
            "SELECT "
            "channel.guildId, channelId, countryName, datasetId, mentionEveryone, runAt "
            "FROM channel JOIN guild "
            "WHERE channel.guildId = ? AND channel.channelId = ?;",
            (channel.guild.id, channel.id),
        )
        return c.fetchone()

    def get_all(self) -> List[dict]:
        c = self._conn.cursor()
        c.execute(
            "SELECT channel.guildId, channelId, countryName, datasetId, mentionEveryone, runAt "
            "FROM guild LEFT JOIN channel "
            "WHERE runAt IS NOT NULL;"
        )
        return c.fetchall()
