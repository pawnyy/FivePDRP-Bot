import datetime
import json
import os
import re
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv, find_dotenv
import aiohttp
from json.decoder import JSONDecodeError
from discord.ext.commands import errors
import asqlite
from utils import classes

load_dotenv(find_dotenv(), override = True)

channels = [804226896740483092, 804227342183432252, 811331455417581568, 843542427075870731]
discussionChannels = [835946870253682748]
TOKEN = os.environ.get("token")
PREFIX = ['?', 'fivepdrp']
INTENTS = discord.Intents.all()
ACTIVITY = discord.Game(name = 'with FivePDRP || Bot made by Indecision#7334')
bot = classes.SubclassBot(command_prefix = PREFIX, intents = INTENTS, activity = ACTIVITY, case_insensitive = True,
                          strip_after_prefix = True)
bot.ip = '147.135.127.111:30120'
bot.count = 0
bot.help_command = classes.MyHelp()


async def suggestionWrite(message):
    """Writes a suggestion in a suggestion channel"""
    sug = await message.channel.send(
        f"User {message.author.mention} ({message.author.name}#{message.author.discriminator}) suggested {message.content}")
    await message.delete()  # deletes the message the user sent
    await sug.add_reaction('\U00002705')  # adds the check reaction
    await sug.add_reaction('\U0000274c')  # adds the x reaction


async def suggestion_discussion(message):
    """Sends a embed with the message content when a discord message link is sent"""
    content = message.content
    links = re.findall(r'(https?://[^\s]+)', content)
    ctx = await bot.get_context(message)
    for url in links:
        try:
            suggestion = await commands.MessageConverter().convert(ctx, url)
            if suggestion.author.bot and suggestion.mentions:
                user = suggestion.mentions[0]
                embed = discord.Embed(title=f"{user.name}#{user.discriminator}", description=suggestion.content)
                embed.set_footer(text="FivePDRP Staff Team")
                embed.set_thumbnail(url=user.avatar_url)
                await message.channel.send(embed=embed)
        except commands.errors.MessageNotFound:
            pass



async def traceback_maker(err, advance: bool = True):
    """Makes a traceback for error handling"""
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = '```py\n{1}{0}: {2}\n```'.format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"


@bot.event
async def on_command_error(ctx, err):
    if isinstance(err, errors.MissingRequiredArgument) or isinstance(err, errors.BadArgument):  # If command is missing a argument or has a bad argument
        helper = str(ctx.invoked_subcommand) if ctx.invoked_subcommand else str(ctx.command)
        await ctx.send_help(helper)

    elif isinstance(err, errors.CommandInvokeError):  # Any error triggered by a command
        error = await traceback_maker(err.original)
        _error = err.original

        if isinstance(_error, aiohttp.ClientConnectorError):
            await ctx.send('Uh oh! It seems the server has ratelimited me. Please try again later!')

        elif isinstance(_error, discord.HTTPException):
            await ctx.send('Uh oh! It seems something went wrong when trying to contact discord. Please try again later!.\nA copy of the error has been sent to my developer.')
            await bot.get_user().send(ctx.message.clean_content + ' | ' + ctx.message.jump_url + '\n' + error)

        elif isinstance(_error, JSONDecodeError):
            await ctx.send("The server doesn't seem to be up.")

        elif "2000 or fewer" in str(err) and len(ctx.message.clean_content) > 1900:
            return await ctx.send(
                "You attempted to make the command display more than 2,000 characters...\n"
                "Both error and command will be ignored."
            )

        else:
            await ctx.send(f"There was an error processing the command ;-;\n{error}")

    elif isinstance(err, errors.CheckFailure):
        pass

    elif isinstance(err, errors.MaxConcurrencyReached):
        await ctx.send("You've reached max capacity of command usage at once, please finish the previous one...")

    elif isinstance(err, errors.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown... try again in {err.retry_after:.2f} seconds.")

    elif isinstance(err, errors.CommandNotFound):
        pass


@bot.event
async def on_ready():  # runs on bot startup
    print(f'Logged in as: {bot.user.name}')
    print(f'With ID: {bot.user.id}')
    if bot.session is None:
        bot.session = aiohttp.ClientSession()
        bot.conn = asqlite.connect(r'utils\example.db')
        bot.load_extension('cogs.cog')
        bot.load_extension('cogs.test')
        bot.load_extension('cogs.status')
        bot.load_extension('cogs.commands')


@bot.event
async def on_raw_reaction_add(payload):
    if not payload.member.bot:
        channel = bot.get_channel(payload.channel_id)
        if str(payload.emoji) == '🗑️' and channel.id in channels:
            message = await channel.fetch_message(payload.message_id)
            matches = re.findall(r'<@!?(\d*?)>', message.content)
            if str(matches[0]) == str(payload.member.id):
                await message.delete()


@bot.event
async def on_message(message):
    if not message.author.bot:
        if message.channel.id in channels:
            if '@everyone' in message.content or '@here' in message.content:
                await message.author.send("Don't do that.")
                await message.delete()
            elif message.author.permissions_in(message.channel).manage_messages:
                if message.content.startswith('^'):
                    pass
                else:
                    await suggestionWrite(message)
            else:
                await suggestionWrite(message)

        if message.channel.id in discussionChannels:
            await suggestion_discussion(message)
    await bot.process_commands(message)


@bot.command()
async def ping(ctx):
    """Simply checks if the bot is online"""
    await ctx.send('pong')


@bot.command()
@commands.is_owner()
async def presence(ctx):
    """Changes the presence to the default"""
    if ctx.author.id == 603591384062099477:
        await bot.change_presence(activity = discord.Game(name = 'with FivePDRP || Bot made by Indecision#7334'))


@bot.command()
async def status(ctx):
    """Checks the status of FivePDRP"""
    emb = discord.Embed(title = 'Please wait, checking to see if the server is up...')
    mes = await ctx.reply(embed = emb)
    try:
        async with bot.session.get(f'http://{bot.ip}/players.json') as response:
            playerList = json.loads(str(await response.text(encoding = 'utf-8')))
            numPlayers = len(playerList)
            embed = discord.Embed(title = 'Server Status', description = 'Current server status is **ONLINE!**',
                                  color = 0x0dd940)
            embed.set_footer(text = f'{numPlayers}/150')
            await mes.edit(content = None, embed = embed)
    except:
        embed = discord.Embed(title = 'Server Status', description = 'Current server status is **offline.**',
                              color = 0xd90d0d)
        await mes.edit(content = None, embed = embed)
    if bot.count == 5:
        await ctx.send('You can also look at the status in the <#812393061728518204> channel!')
        bot.count = 0
    bot.count += 1


@bot.command()
@commands.is_owner()
async def changeStatus(ctx, activity=None, *, name=None):
    """Allows a custom status"""
    if activity.lower() == 'clear':
        await bot.change_presence(status = discord.Status.online, activity = None)
        await ctx.send('Cleared status.')
        return
    elif activity.lower() == 'playing':
        await bot.change_presence(activity = discord.Game(name))
        await ctx.send(f'Changed status to `playing {name}``')
        return
    elif activity.lower() == 'listening':
        await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.listening, name = name))
        await ctx.send(f'Changed status to `listening to {name}`')
        return
    elif activity.lower() == 'watching':
        await bot.change_presence(activity = discord.Activity(type = discord.ActivityType.watching, name = name))
        await ctx.send(f'Changed status to `watching {name}`')
        return
    else:
        await ctx.send("lmao you're an idiot bro")
        return


bot.run(TOKEN)
