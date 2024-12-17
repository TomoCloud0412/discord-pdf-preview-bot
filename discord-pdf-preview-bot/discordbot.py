from discord.ext import commands
import discord
import datetime
from dotenv import load_dotenv
from os.path import join, dirname
import pdf2image
import os
from nbconvert import HTMLExporter
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


@bot.command(name="ipynb", description="ipynbのプレビューを行います。")
async def ipynb(ctx):
    if ctx.message.author.bot:
        return
    
    image_files = []  # 一時的に保存する画像ファイルのリスト

    if ctx.message.attachments and any(a.filename.endswith('.ipynb') for a in ctx.message.attachments):
        for attachment in ctx.message.attachments:
            if attachment.filename.endswith('.ipynb'):
                # ファイルをダウンロード
                file_path = await attachment.save()

                # HTMLに変換
                exporter = HTMLExporter()
                html, resources = exporter.from_filename(file_path)


                 # HTMLからイメージを抽出
                images = [Image.open(BytesIO(v)) for k, v in resources['outputs'].items() if k.endswith('.png')]


                for i, img in enumerate(images):
                    img_bytes = BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_bytes.seek(0)
                    image_files.append(discord.File(img_bytes, f"{os.path.splitext(attachment.filename)[0]}_{i+1}.png"))

                    # 10枚ごとに送信
                    if len(image_files) == 10:
                        await ctx.message.channel.send(files=image_files)
                        image_files = []

                # 残りの画像を送信
                if image_files:
                    await ctx.message.channel.send(files=image_files)

                # 一時ファイルを削除
                os.remove(file_path)


bot.run("ここにdiscordebotのトークンを入力")
