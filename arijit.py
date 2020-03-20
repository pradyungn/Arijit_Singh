import discord
import traceback
from discord.ext import commands
import requests
import asyncio
import re
import json
import youtube_dl
import urllib.parse
import urllib.request
import random
from secret import TOKEN, api_key

client = commands.Bot(command_prefix='$')
client.remove_command("help")

curr = []

player = 0

forced = False
songs = []
source = 1

def get_pre(bot):
    try:
        return bot.command_prefix
    except AttributeError:
        return '!'


def usage(command):
    compalias = command.qualified_name
    if len(command.aliases) > 0:
        for alias in command.aliases:
            compalias = f'{compalias}|{alias}'
        compalias = f'[{compalias}]'
    return f'{get_pre(client)}{compalias} {command.signature}'


def cogster():
    embed=discord.Embed(title=f'Command List', color=0xff5555)
    embed.set_author(name="Arijit Singh", icon_url=client.user.avatar_url)
    for cmd in client.commands:
        embed.add_field(name=cmd.name, value=cmd.brief, inline=False)
    return embed


@client.check
async def globally_block_dms(ctx):
    if ctx.guild is not None:
        return True
    else:
        await ctx.send("You can't use commands in direct messages!")

@client.command(brief='Displays this command.', description='The help command\'s usage portion can be a little difficult to understand.\nThe [] means that you can use any of the command aliases, or the argument is optional.\n<> indicates that an argument must be supplied.')
async def help(ctx, *, cmdcog=None):
#Let's see if the user supplied an argument! If not, let's send the default help text.
    if cmdcog is None:
        #  embed=discord.Embed(title='Help', description=f"I see that you've come seeking help... look no further!\nTo get help with a command, do {client.command_prefix}help <command>", color=0xff5555)
        #  embed.set_author(name="IIT IT", icon_url=client.user.avatar_url)
        await ctx.send(embed=cogster())
        return
    
    posscmd = client.get_command(cmdcog.lower())
    if posscmd is not None:
        desc = f'{posscmd.description if posscmd.description != "" else posscmd.brief}'
        desc = f'{desc}\n```{usage(posscmd)}```'
        embed=discord.Embed(title=posscmd.name, description=desc, color=0xff5555)
        embed.set_author(name="Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
        return
    embed=discord.Embed(title='Help', description='That\'s weird... I can\'t find a command with that name! Try again!', color=0xff5555)
    embed.set_author(name="Arijit Singh", icon_url=client.user.avatar_url)
    await ctx.send(embed=embed)

@client.command(brief="A little about me")
async def about(ctx):
    await ctx.send("I am Arijit Singh, greatest singer of all time beta.")

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'before_options' : '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def mushelper(e, ctx):
    global songs
    global forced
    global source
    if e:
        embed=discord.Embed(title='Turntables', description='Player error: %s' % e, color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
        return
    if len(songs)>0 and ctx.voice_client is not None:
        async with ctx.typing():
            player = songs[0]['src']
            ctx.voice_client.play(player, after=lambda e: synchelper(e, ctx))
            source = random.randint(1111111111,9999999999)
            embed=discord.Embed(title='**Now Playing**', description='{}\n[{}]({})\n{}'.format(songs[0]['channtitle'] ,songs[0]['title'], songs[0]['url'], songs[0]['duration']), color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=f"http://img.youtube.com/vi/{songs[0]['res']}/0.jpg")
            await ctx.send(embed=embed)
            songs.pop(0)
    elif ctx.voice_client is not None and not forced:
        embed=discord.Embed(title='Turntables', description="That's all folks... play some more jams!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
        await ctx.voice_client.disconnect()

    elif forced:
        forced = False

def synchelper(error, ctx):
    coro = mushelper(error, ctx)
    fut = asyncio.run_coroutine_threadsafe(coro, client.loop)

@client.command(brief='Make the bot join a voice channel. Defaults to yours.', description="Joins a voice channel. PS: The 'channel' argument is just the name of the channel.")
async def join(ctx, *, channel: discord.VoiceChannel=None):
    if channel==None:
        channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()
    embed=discord.Embed(title='Movers', description=f"We in da house boi! We jammin in {channel}", color=0xff8c00)
    embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
    await ctx.send(embed=embed)

@client.command(brief='There are some songs you just don\'t like...', description='Entering this will skip to the next track in the queue, if there is one.')
async def skip(ctx):
    global songs
    if ctx.voice_client is not None:
        if len(songs)>0:
            ctx.voice_client.stop()
            embed=discord.Embed(title='Turntables', description="Skipping...", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description=f"There isn't a track for me to skip to... maybe add something to the queue with $play?", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title='Turntables', description="I can't skip if I'm not even playing stuff to begin with!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)



@client.command(brief='Time to break out the myoosic!', description='Enter the command with the name of the song (or just a youtube search), and the bot will play the first video it finds.')
async def play(ctx, *, query: str=None):
    global songs
    global source
    global api_key
    if query is not None:
        async with ctx.typing():
            embed=discord.Embed(title='Turntables', description=":mag: **| Searching the underbelly of youtube**", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
            query = urllib.parse.urlencode({'search_query':query})
            rawcon = urllib.request.urlopen(f'https://www.youtube.com/results?{query}')
            res  = re.findall('href=\"\\/watch\\?v=(.{11})', rawcon.read().decode())
            res = res[0]
            url = f'https://www.youtube.com/watch?v={res}'
            searchUrl=f"https://www.googleapis.com/youtube/v3/videos?id={res}&key="+api_key+"&part=snippet%2CcontentDetails"
            response = urllib.request.urlopen(searchUrl).read()
            data = json.loads(response)
            duration=data['items'][0]['contentDetails']['duration']
            duration = duration.replace('PT', '')
            duration = duration.replace('M', ' Minutes, ')
            duration = duration.replace('S', ' Seconds')
            duration = duration.replace('D', ' Days, ')
            duration = duration.replace('H', ' Hours, ')
            title = data['items'][0]['snippet']['title']
            channelTitle = data['items'][0]['snippet']['channelTitle']
    elif query is None:
        await ctx.send('You have to pick something to play doofus.')
        return

    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: synchelper(e, ctx))
            source = random.randint(1111111111,9999999999)
            embed=discord.Embed(title='**Now Playing**', description='{}\n[{}]({})\n{}'.format(channelTitle, title, url, duration), color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            embed.set_thumbnail(url=f"http://img.youtube.com/vi/{res}/0.jpg")
            await ctx.send(embed=embed)
    else:
        player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
        playdic = {'src': player, 'url': url, 'duration': duration, 'res': res, 'channtitle':channelTitle, 'title': title}
        songs.append(playdic)
        embed=discord.Embed(title='**Queued Up**', description='**{}**\n[{}]({})\n{}'.format(channelTitle, title, url, duration), color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        embed.set_thumbnail(url=f"http://img.youtube.com/vi/{res}/0.jpg")
        await ctx.send(embed=embed)

@client.command(brief="See what's coming up, or delete something.", description='Use the command with no arguments to see the queue. After seeing the queue, enter the command again with the number of the song you want to delete (i.e `!queue 1`).')
async def queue(ctx,*, remove: int=None):
    global songs
    if remove is not None:
        if remove > len(songs):
            embed=discord.Embed(title='Queue', description=f"The number of the song you wanted to delete was too high... there's only {len(songs)} songs!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            remove -= 1
            cache = songs[remove]
            songs.pop(remove)
            embed=discord.Embed(title='Queue', description=f"Removed `{cache['title']}`", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

    else:
        if len(songs) == 0:
            embed=discord.Embed(title='Queue', description="There aren't any songs queued up!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            msg = f'There\'s {len(songs)} song(s) queued up:\n'
            for i in list(range(len(songs))):
                msg = msg + f"{i+1}: [{songs[i]['src'].title}]({songs[i]['url']})\n"
            embed=discord.Embed(title='Queue', description=msg, color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)


@client.command(brief='Change the volume, and see what the volume is.', description='Use the command with no argument to see the volume. Use the command with a positive argument to set the volume.')
async def volume(ctx,*, volume: int=None):
    if ctx.voice_client is None:
        return await ctx.send("Not connected to a voice channel.")
    if volume is not None:
        ctx.voice_client.source.volume = volume / 100
        embed=discord.Embed(title='Sound', description="Changed volume to {}%".format(volume), color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
    elif volume is None:
        try:
            vol = ctx.voice_client.source.volume * 100
            embed=discord.Embed(title='Sound', description="The volume is {}%".format(vol), color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        except:
            embed=discord.Embed(title='Sound', description="You can't have a volume if you're not playing anything stupid.", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

@client.command(description='Stops the myoosic, and disconnects the bot.')
async def stop(ctx):
    global songs
    global forced
    if ctx.voice_client is not None:
        songs = []
        forced = True
        await ctx.voice_client.disconnect()
        embed=discord.Embed(title='We the best Myoosic...', description="We out!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title='We the best Myoosic...', description="You can't stop something that doesn't exist!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)

@client.command(brief='Take a break if you need it!',description='You can take a break if you need to... but after 5 minutes the bot stops completely.')
async def pause(ctx):
    global source
    if ctx.voice_client is not None:
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            ctx.sourcepause = source
            embed=discord.Embed(title='Turntables', description="Paused!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description="You're not playing anything for me to pause!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title='Turntables', description="You're not playing anything for me to pause!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)

@client.command(brief='Done with that break?', description='Resumes your current song.')
async def resume(ctx):
    if ctx.voice_client is not None:
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            embed=discord.Embed(title='Turntables', description="Resuming your song!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed=discord.Embed(title='Turntables', description="You're don't have anything paused for me to resume!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)
    else:
        embed=discord.Embed(title='Turntables', description="You're don't have anything paused for me to resume!", color=0xff8c00)
        embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
        await ctx.send(embed=embed)


@join.before_invoke
async def ensure_voice(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send(":no_entry_sign:  You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")

@play.before_invoke
async def playchann(ctx):
    if ctx.voice_client is None:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            await ctx.send(":no_entry_sign:  You are not connected to a voice channel.")
            raise commands.CommandError("Author not connected to a voice channel.")
    if ctx.voice_client and ctx.author.voice:
        if ctx.author.voice.channel != ctx.voice_client.channel:
            await ctx.send(":no_entry_sign: | **You aren't in my channel!**")
            raise commands.CommandError("Author not connected to a voice channel.")


@queue.before_invoke
@skip.before_invoke
async def samechann(ctx):
    if ctx.voice_client and ctx.author.voice:
        if ctx.author.voice.channel != ctx.voice_client.channel:
            await ctx.send(":no_entry_sign: | **You aren't in my channel!**")
            raise commands.CommandError("Author not connected to a voice channel.")



@pause.after_invoke
async def still_playing(ctx):
    global songs
    global forced
    global source
    await asyncio.sleep(300)
    if ctx.voice_client is not None:
        if ctx.voice_client.is_paused() and ctx.sourcepause == source:
            songs = []
            forced = True
            await ctx.voice_client.disconnect()
            embed=discord.Embed(title='We the best Myoosic...', description="It looks like you aren't playing that song anymore... we're out!", color=0xff8c00)
            embed.set_author(name=f"DJ Arijit Singh", icon_url=client.user.avatar_url)
            await ctx.send(embed=embed)

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    await client.change_presence(activity = discord.CustomActivity(name=get_pre(client)+"help"))

client.run(TOKEN)
