# requires db:
# LAST_SONG = 0

import json
import os
from threading import Thread

import discord
import flask
import httpx
import yt_dlp as youtube_dl
from replit import db

from cooldown import NewCooldown
from editor import Editor

intents = discord.Intents.default()
intents.message_content = True
cooldown = NewCooldown(2, 5)
app = flask.Flask(__name__)
discord.opus.load_opus('opus/libopus.so')

@app.route('/')
def index():
    return "<a href=\"https://youtu.be/dQw4w9WgXcQ\">arnold's youtube channel</a>"

client = discord.Bot(
    intents=intents,
    activity=discord.Activity(type=discord.ActivityType.watching, name="/ask"),
    status=discord.Status.idle
)

def get_regular_prompt() -> str:
    with open("prompt.txt") as file:
        return file.read()

def get_arnold_prompt() -> str:
    with open("arnold.prompt.txt") as file:
        return file.read()

def get_maoyue_prompt() -> str:
    with open("maoyue.prompt.txt") as file:
        return file.read()

@client.event
async def on_ready():
    print('uwu ready!')
    await start_player()

async def start_player():
    TEMPLATES: list[str] = [
        "https://www.youtube.com/watch?v=JYTQIMoel2c",
        "https://www.youtube.com/watch?v=_x8LmSdDvCQ",
        "https://www.youtube.com/watch?v=Jm2LtXgsGjY"
    ]

    category: discord.CategoryChannel = client.get_channel(1126092825285627904)
    vc_choice = None

    for channel in category.channels:
        if channel.id in [1126098224218914837, 1126098976660258929]:
            continue

        if not channel.voice_states.keys():
            vc_choice = channel

    channel = vc_choice or client.get_channel(1126098585423990834)
    voice_client = await channel.connect()

    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'noplaylist': 'True',
        'dump_single_json': 'True',
        'extract_flat': 'True',
        'quiet': 'True'
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(
            TEMPLATES[db['LAST_SONG']],
            download=False,
        )
        url = info['url']
        db['LAST_SONG'] += 1
        db['LAST_SONG'] %= len(TEMPLATES)

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn'
    }
    player = await discord.FFmpegOpusAudio.from_probe(
        url,
        **FFMPEG_OPTIONS
    )

    def handler(*args):
        async def runner():
            await channel.disconnect()
            await start_player()

        asyncio.run_coroutine_threadsafe(runner(), client.loop) # noqa

    voice_client.play(
        player,
        after=handler
    )

@client.command(
    name="ask",
    description="Ask me anything!",
    name_localizations={
        "zh-TW": "詢問"
    },
    description_localizations={
        "zh-TW": "問我任何問題！"
    }
)
async def ask(
    ctx, 
    question: discord.Option(
        str,
        "Any question related to this server.",
        name_localizations={
            "zh-TW": "問題"
        },
        description_localizations={
            "zh-TW": "和這個伺服器有關的任何問題"
        }
    ),
    person: discord.Option(
        str,
        "對象 :scream:",
        choices=[
            discord.OptionChoice(name="default"),
            discord.OptionChoice(name="arnold"),
            discord.OptionChoice(name="maoyue"),
        ]
    ) = "default"
):
    result = cooldown(ctx.author.id)
    if not result:
      return await ctx.reply(f'冷卻 {result.retry_after:.2f}s') # type: ignore

    await ctx.defer(invisible=False)
    
    content: str = question
    f: str = ""

    editor = Editor()
    async def ask_test():
        async with httpx.AsyncClient() as client:
            # ~~im so good at reverse engineering~~
            async with client.stream(
                'POST', 
                "https://gpt4free.awdev.repl.co/chat",
                headers={
                    "User-Agent": ua.random,
                    "Origin": "https://gpt4.xunika.uk",
                    "Referer": "https://gpt4.xunika.uk",
                    "Authorization": "Bearer nk-chatgptorguk"
                },
                json={
                    "frequency_penalty": 0,
                    "messages": [
                        {
                            "role": "system",
                            "content": {
                                "default": get_regular_prompt,
                                "arnold": get_arnold_prompt,
                                "maoyue": get_maoyue_prompt
                            }[person]()
                        },
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "model": "gpt-3.5-turbo",
                    "presence_penalty": 0,
                    "stream": True,
                    "temperature": 0.5,
                    "top_p": 1
                }
            ) as response:
                async for chunk in response.aiter_bytes():
                    await editor.edit(ctx, chunk.decode('utf-8'))

    while not editor.f:
        await ask_test()

    await editor.done(ctx)

# ignore
async def check_status(ctx):
    await ctx.defer()

    async with httpx.AsyncClient() as client:
        resp = await client.get('https://mcapi.us/server/status?ip=milkteamc.org')
        data = resp.json()
        embed = discord.Embed(
            title="🧋 milkteamc.org",
            description=":green_circle: 線上" if data['online'] else ":red_circle: 下線ㄌ",
            color=0x2f3136
        )
        embed.add_field(
            name="玩家人數",
            value=str(data['players']['now'])
        )
        embed.add_field(
          name="伺服器類型",
          value=str(data['server']['name'])
        )
        embed.add_field(
            name="上次更新",
            value=f"<t:{data['last_updated']}:R>"
        )

    await ctx.respond(embed=embed)

Thread(target=lambda: app.run(host="0.0.0.0", port=8080)).start()
client.run(os.environ['TOKEN'])
