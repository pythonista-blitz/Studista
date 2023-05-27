import datetime
import os
import sqlite3
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv

# 環境変数
load_dotenv()
TOKEN = os.getenv("TOKEN")
# WATCH_CHANNEL_ID = int(os.getenv("WATCH_CHANNEL_ID"))
NOTIFY_CHANNEL_ID = int(os.getenv("NOTIFY_CHANNEL_ID"))

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
             (user_id INTEGER PRIMARY KEY, join_date TEXT, stay_minutes INTEGER)"""
)


def calc_total_time(user_id: int) -> str:
    # user_idを指定してstay_minutesの合計時間を計算し、日時分で表示する
    cursor.execute(
        "SELECT SUM(stay_minutes) FROM study_time WHERE user_id=?",
        (user_id,),
    )
    total_minutes = cursor.fetchone()[0] or 0  # 結果がNoneの場合は0として扱う

    delta = datetime.timedelta(minutes=total_minutes).seconds
    day, remainder = divmod(delta, 24 * 60 * 60)
    hour, remainder = divmod(delta, 60 * 60)
    minutes, seconds = divmod(remainder, 60)

    time_formatted = f"{day}日 {hour}時間 {minutes}分"
    return time_formatted


# ボイスチャンネルのユーザー参加イベントを処理
@bot.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel:
        # ユーザーがボイスチャンネルに参加した場合
        join_date = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT OR IGNORE INTO study_time (user_id, join_date, stay_minutes) VALUES (?, ?, 0)",
            (member.id, join_date),
        )
        conn.commit()

    if before.channel and not after.channel:
        # ユーザーがボイスチャンネルから退出した場合
        cursor.execute(
            "SELECT join_date, stay_minutes FROM study_time WHERE user_id=? ORDER BY join_date DESC LIMIT 1",
            (member.id,),
        )
        latest_join = cursor.fetchone()

        if latest_join:
            join_date = datetime.datetime.strptime(latest_join[0], "%Y-%m-%d %H:%M:%S")
            leave_date = datetime.datetime.utcnow()
            voice_time = (leave_date - join_date).total_seconds() // 60

            stay_minutes = round(latest_join[1]) + 2
            # 1分以内の滞在なら通知しない
            if stay_minutes >= 1:
                stay_minutes += voice_time

                cursor.execute(
                    "UPDATE study_time SET stay_minutes=? WHERE user_id=? AND join_date=?",
                    (stay_minutes, member.id, latest_join[0]),
                )
                conn.commit()

                # 通知用テキストチャンネルにメッセージを送信
                text_channel_name = bot.get_channel(NOTIFY_CHANNEL_ID)
                embed = discord.Embed(title="Result", color=discord.Color.green())
                file = discord.File("icon.png", filename="icon.png", spoiler=True)
                embed.set_author(
                    name=bot.user,
                    url="https://github.com/pythonista-blitz/Studista",
                )
                embed.add_field(name="Name", value=member.name, inline=True)
                embed.add_field(
                    name="Study Time", value=f"{stay_minutes}分", inline=True
                )
                embed.add_field(
                    name="Total Time", value=calc_total_time(member.id), inline=True
                )
                await text_channel_name.send(embed=embed)


# ボットを起動
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    # 画像をDiscordにアップロード（初回のみ実行）
    # text_channel = bot.get_channel(NOTIFY_CHANNEL_ID)
    # if "uploaded_icon_url" not in bot.__dict__:
    #     with open("./icon.png", "rb") as image_file:
    #         uploaded_icon = await text_channel.send(file=discord.File(image_file))


bot.run(TOKEN)
