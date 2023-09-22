import sqlite3

import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
import pytest
import pytest_asyncio
from discord.ext.commands import Cog, command


class Misc(Cog):
    @command()
    async def ping(self, ctx):
        await ctx.send("Pong !")

    @command()
    async def echo(self, ctx, text: str):
        await ctx.send(text)


@pytest_asyncio.fixture
async def bot():
    # コマンドprefix
    PREFIX = "/"

    # Botの設定
    intents = discord.Intents.all()
    intents.voice_states = True
    intents.typing = True
    # ボットのプレフィックスを設定します
    b = commands.Bot(command_prefix=PREFIX, intents=intents)
    # データベースに接続
    conn = sqlite3.connect("study_data.db")
    cursor = conn.cursor()

    # テーブルを作成（存在しない場合）
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS study_time
                (user_id INTEGER PRIMARY KEY, join_date TEXT, stay_seconds INTEGER)"""
    )
    await b._async_setup_hook()  # setup the loop
    await b.add_cog(Misc())

    dpytest.configure(b)
    return b


@pytest.mark.asyncio
async def test_ping(bot):
    await dpytest.message("!ping")
    assert dpytest.verify().message().content("Pong !")


@pytest.mark.asyncio
async def test_echo(bot):
    await dpytest.message("!echo Hello world")
    assert dpytest.verify().message().contains().content("Hello")
