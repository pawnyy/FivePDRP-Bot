import datetime
import json
import os
import re

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv, find_dotenv
import aiohttp
import asyncio
from dateutil import tz
from json.decoder import JSONDecodeError
import asqlite


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.loop.start()

    async def cog_command_error(self, ctx, error):
        if isinstance(error, JSONDecodeError):
            self.loop.restart()
            pass


    @tasks.loop(seconds = 60)
    async def loop(self):
        bot = self.bot
        channel = bot.get_channel(812393061728518204)
        mes = None
        EST = tz.gettz('America/New York')
        time = datetime.datetime.strftime(datetime.datetime.now(tz = EST), '%x %X')
        async for message in channel.history(limit = 50):
            if message.author == bot.user:
                mes = message

        if mes is None:
            embed = discord.Embed(title = 'Gathering information...')
            mes = await channel.send(embed = embed)

        try:
            async with bot.session.get(f'http://{bot.ip}/players.json') as response:
                try:
                    playerList = json.loads(str(await response.text(encoding = 'utf-8')))
                    bot.playerList = playerList
                except JSONDecodeError:
                    playerList = None
                numPlayers = len(playerList)
                embed = discord.Embed(title = 'Server Status', description = 'Current server status is **ONLINE!**',
                                      color = 0x0dd940)
                embed.set_footer(text = f'{numPlayers}/150, Last updated at {time}')
                embed.set_author(
                    icon_url = 'https://cdn.discordapp.com/attachments/803311825512300554/846722418911346698/Logo.png',
                    name = 'FivePDRP')
                await mes.edit(content = None, embed = embed)

        except:
            embed = discord.Embed(title = 'Server Status', description = 'Current server status is **offline.**',
                                  color = 0xd90d0d)
            embed.set_author(
                icon_url = 'https://cdn.discordapp.com/attachments/803311825512300554/846722418911346698/Logo.png',
                name = 'FivePDRP')
            embed.set_footer(text = f'Last updated at {time}')
            await mes.edit(content = None, embed = embed)

    @loop.before_loop
    async def loop_before(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(1)

    @commands.group(name = 'loop')
    @commands.is_owner()
    async def _loop(self, ctx):
        """
        A way to control the status loop.
        """
        pass

    @_loop.command()
    @commands.is_owner()
    async def restart(self, ctx):
        self.loop.restart()
        await ctx.message.add_reaction('✅')

    @_loop.command()
    @commands.is_owner()
    async def stop(self, ctx):
        self.loop.stop()
        await ctx.message.add_reaction('✅')

    @_loop.command()
    @commands.is_owner()
    async def start(self, ctx):
        self.loop.start()
        await ctx.message.add_reaction('✅')


def setup(bot):
    bot.add_cog(Status(bot))
