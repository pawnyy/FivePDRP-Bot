import datetime
import json
import pprint
import re
from datetime import datetime as dtime
from json import JSONDecodeError

import asqlite
import discord
import humanize
import pandas as pd
from dateutil import parser
from discord.ext import commands, tasks
import os


def is_trusted(ctx):
    trusted = [147475280699719680, 603591384062099477]
    return ctx.author.id in trusted


class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild = self.bot.get_guild(781402142183129100)
        self.takeRoles = [
            self.guild.get_role(781402142794973198),  # mod
            self.guild.get_role(819780890498564106),  # staff member
            self.guild.get_role(781402142794973199),  # senior mod
            self.guild.get_role(819781260595298335)  # trial mod
        ]
        self.giveRoles = [self.guild.get_role(844665950754046044)]
        self.getUsers.start()
        pd.set_option('display.max_columns', 20)
        pd.set_option('display.max_rows', 50)
        pd.set_option('display.expand_frame_repr', False)

    @commands.command(aliases = ['userinfo'])
    async def whois(self, ctx, *, arg):
        """
        Get various information about a user.

        Args:
             arg: The user or string to lookup.

        Returns:
            A embed displaying information about the user
        """
        def isint(argument: str):
            try:
                int(argument)
            except ValueError:
                return False
            else:
                return float(argument).is_integer()

        member = None
        name = None
        ID = None
        if isint(arg):
            async with self.bot.session.get(f'http://{self.bot.ip}/players.json') as response:
                playerList = json.loads(str(await response.text(encoding = 'utf-8')))
                for user in playerList:
                    if str(user['id']) == str(arg):
                        userObject = user
                try:
                    ID = userObject['id']
                    for identifier in userObject['identifiers']:
                        if identifier.startswith('discord:'):
                            discordID = int(identifier.replace('discord:', ''))
                    name = userObject['name']
                    member = ctx.guild.get_member(discordID)
                except UnboundLocalError:
                    pass

        if member is None:
            try:
                member = await commands.MemberConverter().convert(ctx, arg)
            except commands.BadArgument:
                pass
            if arg is None:
                member = ctx.author
            if member is None:
                async with asqlite.connect(r'utils/example.db') as conn:
                    async with conn.cursor() as cursor:
                        query = 'SELECT * FROM users WHERE name LIKE ?'
                        await cursor.execute(query, '%' + arg + '%')
                        data = await cursor.fetchone()
                        if not data:
                            await ctx.send('Nothing found.')
                            return
                        data = data['discord']
                        if data:
                            data = data.replace('discord:', '')
                            if not member:
                                member = ctx.guild.get_member(int(data))
                        if not member:
                            await ctx.send('No member found.')
                            return

        mentionRoles = []
        for role in member.roles:
            if role.name != '@everyone':
                mentionRoles.append(role.mention)
        mentionRoles.reverse()
        a = str(mentionRoles).strip('[]').replace('\'', '')
        join = member.joined_at - datetime.timedelta(hours = -5)
        joinDate = join.strftime("%c")
        create = member.created_at - datetime.timedelta(hours = -5)
        createDate = create.strftime("%c")
        embed = discord.Embed(color = 0x872222)
        embed.set_author(name = f"{member.name}#{member.discriminator}", icon_url = member.avatar_url)
        if name and ID:
            embed.add_field(name = "In Game Name", value = name, inline = True)
            embed.add_field(name = "In Game ID", value = ID, inline = True)
        embed.add_field(name = "Created At", value = createDate, inline = True)
        embed.add_field(name = "Joined At", value = joinDate, inline = True)
        embed.add_field(name = "Avatar", value = f"[Avatar URL]({member.avatar_url})", inline = True)
        embed.add_field(name = f"Roles: ({len(member.roles) - 1})", value = a, inline = False)
        embed.add_field(name = "ID", value = member.id, inline = True)
        try:
            await ctx.send(embed = embed)
        except discord.HTTPException:
            if name and ID:
                embed.set_field_at(5, name=f"Roles: ({len(member.roles) - 1})",
                                   value=f'Too many roles to display.\nInstead, you can click the user to see for yourself. {member.mention}, ')
            else:
                embed.set_field_at(3, name = f"Roles: ({len(member.roles) - 1})", value = f'Too many roles display.\nInstead, you can click the user to see for yourself. {member.mention}, ')
            await ctx.send(embed = embed)


    @commands.command(aliases = ['serverinfo'])
    async def GuildInfo(self, ctx):
        """
           Get various information about the current guild.

           Returns:
               A embed displaying information about the guild/
        """
        guild = ctx.guild
        time = guild.created_at.strftime('%x %X')
        embed = discord.Embed(title = guild.name, color = discord.Colour(0xa20003))
        embed.set_footer(text = str(guild.id))
        embed.set_thumbnail(url = guild.icon_url)

        embed.add_field(name = 'Name', value = guild.name, inline = True)
        embed.add_field(name = '# of categories', value = str(len(guild.categories)), inline = True)
        embed.add_field(name = '# of channels', value = str(len(guild.channels)), inline = True)
        embed.add_field(name = '# of emojis', value = str(len(guild.emojis)), inline = True)
        embed.add_field(name = 'Member Count', value = str(guild.member_count), inline = True)
        embed.add_field(name = 'Owner', value = str(guild.owner), inline = True)
        embed.add_field(name = 'Verification Level', value = str(guild.verification_level), inline = True)
        embed.add_field(name = 'Created At', value = time, inline = True)
        if guild.description:
            embed.add_field(name = 'Created At', value = guild.description, inline = True)

        await ctx.send(embed = embed)

    @commands.Cog.listener('on_raw_reaction_add')
    async def staffLOA(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) == '🧳' and payload.channel_id == 852307561466167356 and payload.message_id == 852350705284415488:
            member: discord.Member = self.guild.get_member(payload.user_id)
            for role in self.takeRoles:
                try:
                    await member.remove_roles(role)
                except discord.HTTPException:
                    pass
            for role in self.giveRoles:
                await member.add_roles(role)

    @commands.command()
    @commands.has_any_role(819780890498564106, 781402142749098040, 707766292660355122, 803657811435192341)
    async def lookup(self, ctx, *, name: str = None):
        """
        A way to lookup identifiers of a user.

        Args:
            name: The name of the user to lookup.

        Returns:
            A embed displaying all identifiers of the user.
        """
        if name is None:
            await ctx.send('Please specify a name to lookup.')
            return
        try:
            member = await commands.MemberConverter().convert(ctx, name)
            name = str(member.id)
        except commands.BadArgument:
            pass

        async with asqlite.connect(r'utils/example.db') as conn:
            async with conn.cursor() as cursor:
                query = 'SELECT * from users WHERE name LIKE ? OR steam LIKE ? OR license LIKE ? OR xbl LIKE ? OR discord LIKE ? OR live LIKE ? OR fivem LIKE ? OR  license2 LIKE ?'
                param = []
                for i in range(8):
                    param.append('%' + name + '%')
                param = tuple(param)
                await cursor.execute(query, param)
                data = await cursor.fetchone()
                if data:
                    embed = discord.Embed(title = f'Identifiers of {data["name"]}')
                    for key in data.keys():
                        embed.add_field(name = key, value = data[key], inline = True)
                    await ctx.send(embed = embed)

                else:
                    await ctx.send('No records found with that name.')

    @commands.command()
    @commands.has_any_role(819780890498564106, 781402142749098040, 707766292660355122, 803657811435192341)
    async def punishments(self, ctx, *, args):
        """
        Get all the punishments of a user.

        Args:
            args: The name of the user you want to search.

        Returns:
            A list of all punishments of the user wrapped in a embed.
        """
        data = None
        try:
            user = await commands.UserConverter().convert(ctx, args)
        except commands.BadArgument or commands.CommandError:
            pass

        async with asqlite.connect(r'utils/example.db') as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute('SELECT * FROM punishments WHERE discord LIKE ?', ('%' + str(user.id) + '%'))
                    data = await cursor.fetchall()
                except NameError:
                    pass
                if not data:
                    await cursor.execute('SELECT * FROM punishments WHERE user LIKE ?', ('%' + args + '%'))
                    data = await cursor.fetchall()
                    if not data:
                        await ctx.send('No records found.')
                        return
                embed = discord.Embed(title = 'Punishment List')
                outputList = pd.DataFrame(list(data))

                for row in data:
                    if row['discord']:
                        try:
                            ID = row['discord'].replace('discord:', '')
                            userr = self.bot.get_user(int(ID))
                            mentioned = userr.mention
                        except AttributeError:
                            mentioned = 'None found.'
                    else:
                        mentioned = 'None found.'

                    time = parser.parse(row['time'])
                    humanizedTime = humanize.precisedelta(time, minimum_unit = 'days')

                    embed.add_field(name = str(row['ID']), value = f"**Time:** {row['time']} - {humanizedTime} ago.\n"
                                                                   f"**Action:** {row['action']}\n"
                                                                   f"**User:** {row['user']}\n"
                                                                   f"**Moderator:** {row['mod']}\n"
                                                                   f"**Discord ID:** {mentioned}\n"
                                                                   f"**Reason:** {row['reason']}\n")
                try:
                    await ctx.send(embed = embed)
                except discord.HTTPException:
                    try:
                        await ctx.send(f'```{outputList}```')
                    except discord.HTTPException:
                        def chunks(s, n):
                            """Produce `n`-character chunks from `s`."""
                            for start in range(0, len(s), n):
                                yield s[start:start + n]

                        for chunk in chunks(str(outputList), 1994):
                            if not chunk.endswith("```"):
                                chunk = chunk + "```"
                            if not chunk.startswith("```"):
                                chunk = "```" + chunk
                            await ctx.send(chunk)

    @commands.Cog.listener('on_message')
    async def logs(self, message):
        if message.channel.id == 816466656561856562:
            match = re.findall(r'\*\*(.*)\*\* (kicked|offline banned|banned|warned) \*\*(.*)\*\*, Reason: (.*)',
                               message.content)
            if len(match) > 0:
                match = match[0]
                async with asqlite.connect(r'utils/example.db') as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT discord FROM users WHERE name LIKE ?", '%' + match[2] + '%')
                        try:
                            Discord = await cursor.fetchone()
                            Discord = Discord['discord']
                        except KeyError:
                            pass
                        except TypeError:
                            pass

                        strtime = dtime.strftime(message.created_at, "%x %X %Z")

                        matches = (match[0], match[1], match[2], match[3], Discord, strtime)
                        await cursor.execute(
                            "INSERT INTO punishments (mod, action, user, reason, discord, time) VALUES (?, ?, ?, ?, ?, ?)",
                            matches)

                    await conn.commit()
                await message.add_reaction('<:2942_Check:811707735653220373>')

    @commands.command()
    @commands.is_owner()
    async def fix(self, ctx):
        channel = self.bot.get_channel(816466656561856562)
        async with ctx.channel.typing():
            async for message in channel.history(limit = None, oldest_first = True):
                if message.channel.id == 816466656561856562:
                    match = re.findall(r'\*\*(.*)\*\* (kicked|offline banned|banned|warned) \*\*(.*)\*\*, Reason: (.*)',
                                       message.content)
                    if len(match) > 0:
                        match = match[0]
                        async with asqlite.connect(r'utils/example.db') as conn:
                            async with conn.cursor() as cursor:
                                await cursor.execute("SELECT discord FROM users WHERE name LIKE ?",
                                                     '%' + match[2] + '%')
                                try:
                                    Discord = await cursor.fetchone()
                                    Discord = Discord['discord']
                                except KeyError:
                                    pass
                                except TypeError:
                                    pass

                                strtime = dtime.strftime(message.created_at, "%x %X %Z")

                                matches = (match[0], match[1], match[2], match[3], Discord, strtime)
                                await cursor.execute(
                                    "INSERT INTO punishments (mod, action, user, reason, discord, time) VALUES (?, ?, ?, ?, ?, ?)",
                                    matches)
                            await conn.commit()
                        await message.add_reaction('<:2942_Check:811707735653220373>')
        await ctx.send('done :)')

    @tasks.loop(seconds = 60)
    async def getUsers(self):
        bot = self.bot
        async with bot.session.get(f'http://{bot.ip}/players.json') as response:
            try:
                playerList = json.loads(str(await response.text(encoding = 'utf-8')))
            except JSONDecodeError:
                playerList = None
        async with asqlite.connect(r'utils/example.db') as conn:
            async with conn.cursor() as cursor:
                if playerList:
                    response = playerList

                    for user in response:
                        licenses = []

                        name = '"' + user['name'] + '"'
                        try:
                            await cursor.execute("INSERT INTO users (name) VALUES (?)", name)
                        except asqlite.sqlite3.IntegrityError:
                            pass

                        for identifier in user['identifiers']:
                            try:
                                if identifier.startswith('steam:'):
                                    licenses.append('steam')
                                    await cursor.execute("UPDATE users SET steam = ? WHERE name = ?",
                                                         (identifier, name))
                                elif identifier.startswith('license:'):
                                    licenses.append('license')
                                    await cursor.execute("UPDATE users SET license = ? WHERE name = ?",
                                                         (identifier, name))
                                elif identifier.startswith('xbl:'):
                                    licenses.append('xbl')
                                    await cursor.execute("UPDATE users SET xbl = ? WHERE name = ?", (identifier, name))
                                elif identifier.startswith('discord:'):
                                    licenses.append('discord')
                                    await cursor.execute("UPDATE users SET discord = ? WHERE name = ?",
                                                         (identifier, name))
                                elif identifier.startswith('live:'):
                                    licenses.append('live')
                                    await cursor.execute("UPDATE users SET live = ? WHERE name = ?", (identifier, name))
                                elif identifier.startswith('fivem'):
                                    licenses.append('fivem')
                                    await cursor.execute("UPDATE users SET fivem = ? WHERE name = ?",
                                                         (identifier, name))
                                elif identifier.startswith('license2'):
                                    licenses.append('license2')
                                    await cursor.execute("UPDATE users SET license2 = ? WHERE name = ?",
                                                         (identifier, name))
                            except asqlite.sqlite3.IntegrityError:
                                pass

                # Save (commit) the changes
                await conn.commit()

    @getUsers.before_loop
    async def before_getUsers(self):
        print('getUsers has started.')
        await self.bot.wait_until_ready()

    @commands.command()
    @commands.is_owner()
    async def test(self, ctx):
        async with asqlite.connect(r'utils/example.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT user, discord FROM punishments WHERE discord is null')

    @commands.command(aliases = ['removepu', 'rpu'])
    @commands.has_any_role(803657811435192341, 781402142787371055)
    async def removePunishments(self, ctx, num: str):
        """
        Removes a punishment from the database.

        Args:
            num: The number of the punishment to remove.
        """
        async with asqlite.connect(r'utils/example.db') as conn:
            async with conn.cursor() as cursor:
                await cursor.execute('SELECT * FROM punishments WHERE ID = ?', num)
                row = await cursor.fetchone()
                try:
                    row = row[0]
                except TypeError or IndexError:
                    pass
                if row:
                    await cursor.execute('DELETE FROM punishments WHERE ID = ?', num)
                    await ctx.send(f'Deleted punishment #{num}')
                else:
                    await ctx.send('Nothing found.')

    @commands.command()
    @commands.has_any_role(819780890498564106, 781402142749098040, 707766292660355122, 803657811435192341)
    async def onlinePlayers(self, ctx):
        """
        Get a table of all the online players.

        Returns:
            A table of all the online players.
        """
        pd.set_option('display.max_rows', 100)
        pd.set_option('max_colwidth', 500)
        bot = self.bot
        async with bot.session.get(f'http://{bot.ip}/players.json') as response:
            try:
                playerList = json.loads(str(await response.text(encoding = 'utf-8')))
                for user in playerList:
                    del user['endpoint']
                    del user['ping']
                    for identifier in user['identifiers']:
                        if 'discord' in identifier or 'steam' in identifier:
                            pass
                        else:
                            user['identifiers'].remove(identifier)
                data = pd.DataFrame(playerList)
                try:
                    await ctx.send('```' + str(data) + '```')
                except discord.HTTPException:
                    def chunks(s, n):
                        """Produce `n`-character chunks from `s`."""
                        for start in range(0, len(s), n):
                            yield s[start:start + n]

                    for chunk in chunks(str(data), 1994):
                        if not chunk.endswith("```"):
                            chunk = chunk + "```"
                        if not chunk.startswith("```"):
                            chunk = "```" + chunk
                        await ctx.send(chunk)
            except JSONDecodeError:
                await ctx.send('Server seems to not be up right now. Try again later?')

    @commands.command()
    @commands.check(is_trusted)
    async def restart(self, ctx):
        os.execv(__file__, sys.argv)


def setup(bot):
    bot.add_cog(Commands(bot))
