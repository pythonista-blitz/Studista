import datetime
import os
import sqlite3
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

# 環境変数
load_dotenv("../.env")
TOKEN = os.getenv("TOKEN")
# WATCH_CHANNEL_ID = int(os.getenv("WATCH_CHANNEL_ID"))
NOTIFY_CHANNEL_ID = os.getenv("NOTIFY_CHANNEL_ID")

# コマンドprefix
PREFIX = "/"

# Botの設定
intents = discord.Intents.all()
intents.voice_states = True
intents.typing = True
# ボットのプレフィックスを設定します
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# データベースに接続
conn = sqlite3.connect("study_data.db")
cursor = conn.cursor()

# テーブルを作成（存在しない場合）
cursor.execute(
    """CREATE TABLE IF NOT EXISTS study_time
             (user_id INTEGER PRIMARY KEY, join_date TEXT, stay_seconds INTEGER)"""
)

class StudyLogger(commands.Cog):


def format_total_time(user_id: int) -> str:
    # user_idを指定してstay_secondsの合計時間を計算し、日時分で表示する
    cursor.execute(
        "SELECT SUM(stay_seconds) FROM study_time WHERE user_id=?",
        (user_id,),
    )
    result = cursor.fetchone()
    if result is not None:
        total_seconds = result["stay_seconds"]
    else:
        total_seconds = 0

    delta = datetime.timedelta(seconds=total_seconds)
    day = delta.days
    hour, remainder = divmod(delta, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    time_formatted = f"{day}日 {hour}時間 {minutes}分 {seconds}秒"
    return time_formatted


# ユーザーがボイスチャンネルに参加した場合の処理
async def handle_member_join(member) -> None:
    join_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO study_time (user_id, join_date, stay_seconds) VALUES (?, ?, 0)",
        (member.id, join_date),
    )
    conn.commit()


# ユーザーがボイスチャンネルから退出した場合の処理
async def handle_member_leave(member) -> None:
    cursor.execute(
        "SELECT join_date, stay_seconds FROM study_time WHERE user_id=? ORDER BY join_date DESC LIMIT 1",
        (member.id,),
    )
    join_date, stay_seconds = cursor.fetchone()

    if join_date:
        join_date = datetime.datetime.strptime(join_date, "%Y-%m-%d %H:%M:%S")
        leave_date = datetime.datetime.utcnow()
        new_stay_seconds = stay_seconds + round(
            (leave_date - join_date).total_seconds()
        )

        cursor.execute(
            "UPDATE study_time SET stay_seconds=? WHERE user_id=? AND join_date=?",
            (stay_seconds, member.id, join_date),
        )
        conn.commit()

        # 1分以内の滞在なら通知しない
        if stay_seconds >= 60:
            # 通知用テキストチャンネルにメッセージを送信
            text_channel_name = bot.get_channel(NOTIFY_CHANNEL_ID)
            embed = discord.Embed(title="Result", color=discord.Color.green())
            file = discord.File("icon.png", filename="icon.png", spoiler=True)
            embed.set_author(
                name=bot.user,
                url="https://github.com/pythonista-blitz/Studista",
            )
            embed.add_field(name="Name", value=member.name, inline=True)
            embed.add_field(name="Study Time", value=f"{stay_seconds}分", inline=True)
            embed.add_field(
                name="Total Time", value=format_total_time(member.id), inline=True
            )
            embed.set_footer(
                text="made by nista",
                icon_url="attachment://icon.png",
            )
            await text_channel_name.send(embed=embed)


# ボイスチャンネルのユーザー参加イベントを処理
@bot.event
async def on_voice_state_update(member, before, after):
    # ユーザーがボイスチャンネルに参加した場合
    if not before.channel and after.channel:
        await handle_member_join(member)

    # ユーザーがボイスチャンネルから退出した場合
    if before.channel and not after.channel:
        await handle_member_leave(member)


# ボットを起動
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")


bot.run(TOKEN)
