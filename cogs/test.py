import datetime
import json

import discord
from discord.ext import commands

path = r'/srv/server/data/civwarnings.json'
allowed_roles = [781402142794973198, 781402142749098040]
allowed_users = [603591384062099477]


class Civ(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        a = False
        b = (ctx.author.id in allowed_users)
        c = ctx.author.guild_permissions.administrator
        for i in ctx.author.roles:
            if i.id in allowed_roles:
                a = True
        if a is True or b is True or c is True:
            return True


    @commands.command()
    async def civwarn(self, ctx, member: discord.Member = None, *, reason: str = None):
        """
        Warns a civ

        Args:
            member: The member to warn.
            reason: The reason to warn the user.
        """
        if member is None or reason is None:
            await ctx.send('Something went wrong. Please make sure you are including both a user and a reason.')
            return

        mem = str(member.id)

        with open(path) as json_file:
            data = json.load(json_file)

        try:
            if data[mem]:
                things = {
                    "date": datetime.datetime.today().strftime('%x'),
                    "reason": reason,
                    "cm": str(ctx.author)
                }
                nums = []
                for key in data[mem]:
                    nums.append(int(key))
                ID = str(max(nums) + 1)
                data[mem][ID] = things

                e = discord.Embed(title = 'New Civ Warning')
                e.add_field(name = ID,
                            value = f'Date: {things["date"]}\nReason: {things["reason"]}\nCM: {things["cm"]}')

        except KeyError:
            things = {
                mem: {
                    "1": {
                        "date": datetime.datetime.today().strftime('%x'),
                        "reason": reason,
                        "cm": str(ctx.author)
                    }
                }
            }
            data.update(things)
            ID = 1
            e = discord.Embed(title = 'New Civ Warning')
            e.add_field(name = "1",
                        value = f'Date: {things[mem]["1"]["date"]}\nReason: {things[mem]["1"]["reason"]}\nCM: {things[mem]["1"]["cm"]}')

        try:
            await member.send(embed = e)
        except discord.HTTPException:
            await ctx.send('Failed to DM user.')

        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent = 4)

        await ctx.send(
            f'Successfully warned `{str(member)}` for `{reason}`. That user now has `{ID}` warnings.')

    @commands.command(aliases = ['civwarning'])
    async def civwarnings(self, ctx, member: discord.Member = None):
        """
        Find the warnings of a civ

        Args:
            member: The user to lookup
        """
        with open(path) as json_file:
            data = json.load(json_file)

        try:
            data[str(member.id)]
        except KeyError:
            await ctx.send('No warnings found for this user.')
            return

        embed = discord.Embed(title = f'Warnings for {str(member)}')
        for key in data[str(member.id)]:
            embed.add_field(name = key,
                            value = f'Date: {data[str(member.id)][key]["date"]}\nReason: {data[str(member.id)][key]["reason"]}\nCM: {data[str(member.id)][key]["cm"]}',
                            inline = True)
        await ctx.send(embed = embed)

    @commands.command(aliases = ['civremovewarning', 'civremovewarnings'])
    async def civremovewarn(self, ctx, member: discord.Member = None, num=None):
        """
        Removes a civwarning from a civ.

        Args:
            member: Which member to remove a warning from.
            num: The ID of the warning to remove.
        """
        if member is None or num is None:
            await ctx.send('Something went wrong. Please make sure you specify a user and a warning number.')
            return

        with open(path) as json_file:
            data = json.load(json_file)

        if num == '*':
            data.pop(str(member.id), None)
            with open(path, 'w') as json_file:
                json.dump(data, json_file, indent = 4)
            await ctx.send(f'Successfully removed all warnings from `{str(member)}`!')
            return

        warning = data[str(member.id)].pop(num, None)

        if warning:
            if len(data[str(member.id)]) == 0:
                del data[str(member.id)]
            with open(path, 'w') as json_file:
                json.dump(data, json_file, indent = 4)

            await ctx.send(f'Successfully removed warning `{num}` from `{str(member)}`!')
        else:
            await ctx.send('Warning not found.')

    @commands.command()
    @commands.is_owner()
    async def export(self, ctx):
        """Exports the json of all the civwarnings."""
        with open(path) as json_file:
            data = json.load(json_file)
        f = discord.File(path, filename = 'civwarnings.json')
        await ctx.send(content = f'If you know what to do with this, here ya go.', file = f)


def setup(bot):
    bot.add_cog(Civ(bot))
