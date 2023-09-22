import datetime
import os
import sqlite3
import time

import discord
import studytime_logger
from discord.ext import commands
from dotenv import load_dotenv

# 環境変数
load_dotenv("../.env")
TOKEN = os.getenv("TOKEN")
# WATCH_CHANNEL_ID = int(os.getenv("WATCH_CHANNEL_ID"))
NOTIFY_CHANNEL_ID = os.getenv("NOTIFY_CHANNEL_ID")


# データベースに接続
conn = sqlite3.connect("study_data.db")
cursor = conn.cursor()

# テーブルを作成（存在しない場合）
cursor.execute(
    """CREATE TABLE IF NOT EXISTS study_time
             (user_id INTEGER PRIMARY KEY, join_date TEXT, stay_seconds INTEGER)"""
)

extensions = ("study_timer",)


class Studista(commands.Bot):
    def __init__(self, command_prefix, intents, description=None):
        super().__init__(
            command_prefix=command_prefix, intents=intents, description=description
        )

    async def on_ready(self):
        print(f"Logged in as {bot.user.name} ({bot.user.id})")
        await self.change_presense(
            activity=discord.Game(name=f"{len(self.guilds)}servers")
        )

    async def setup_hook(self):
        print("setup hook activate")
        for extension in extensions:
            await self.load_extension(extension)


# コマンドprefix
PREFIX = "/"

# Botの設定
intents = discord.Intents.all()
intents.voice_states = True
intents.typing = True

# ボットのプレフィックスを設定します
bot = Studista(command_prefix=PREFIX, intents=intents)


if __name__ == "__main__":
    bot().run(TOKEN)
