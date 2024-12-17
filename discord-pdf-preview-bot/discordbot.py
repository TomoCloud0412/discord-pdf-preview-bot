from discord.ext import commands
import discord
import datetime
from dotenv import load_dotenv
from os.path import join, dirname
import pdf2image
import os
from PIL import Image
from io import BytesIO

intents = discord.Intents.default()
intents.members = True # メンバー管理の権限
intents.message_content = True # メッセージの内容を取得する権限


# Botをインスタンス化
# discordpy の機能で一部イベントの受け取り・スルーを制御できる=>通信量の削減
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.message_content = True  # メッセージコンテントの有効化

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"), # !コマンド名またはメンションでコマンドを実行できるようになる
    case_insensitive=True, # コマンドの大文字小文字を区別しない ($hello も $Hello も同じ!)
    intents=intents # 権限を設定
)
dotenv_path = join(dirname(__name__), '.env')
load_dotenv(verbose=True, dotenv_path=dotenv_path)

print(intents.members)


@bot.event
async def on_ready():
    print(datetime.datetime.now().time(),
          "on_ready/discordVer", discord.__version__)
    await bot.change_presence(activity=discord.Activity(name="!pdfでPDFをjpgに", type=discord.ActivityType.playing))
    
@bot.command(name="howto",description="botの使い方を表示する。")
async def howto(ctx):
    usage = "使い方:\n!pdf - コマンドと一緒にpdfを送信すると、pdfのプレビューができる。"

    await ctx.send(usage)

    



@bot.command(name="pdf", description="pdfのプレビューを行います。")
async def pdf(ctx):
    if ctx.message.author.bot:
        return

    image_files = []  # 一時的に保存する画像ファイルのリスト

    for attachment in ctx.message.attachments:
        if attachment.content_type != "application/pdf":
            continue
        
        await attachment.save(f"{ctx.message.id}.pdf")
        images = pdf2image.convert_from_path(f"{ctx.message.id}.pdf")
        for index, image in enumerate(images):
            image_file = f"{ctx.message.id}-{str(index+1)}.jpg"
            image.save(image_file)
            image_files.append(discord.File(image_file))  # discord.Fileオブジェクトをリストに追加

        # 10個の画像ファイルがたまったら送信してリストをクリア
            if len(image_files) >= 10:
                await ctx.message.channel.send(files=image_files)
                for image_file in image_files:
                    os.remove(image_file.filename)
                image_files = []

    # 残っている画像ファイルを送信してクリア
    if len(image_files) > 0:
        await ctx.message.channel.send(files=image_files)
        for image_file in image_files:
            os.remove(image_file.filename)
    
    os.remove(f"{ctx.message.id}.pdf")



bot.run("ここにdiscordebotのトークンを入力")