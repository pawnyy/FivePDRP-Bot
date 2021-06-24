from discord.ext import commands
import discord


class SubclassBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = None
        self.conn = None

    async def close(self):
        await self.session.close()
        try:
            for extension in tuple(self.__extensions):
                try:
                    self.unload_extension(extension)
                except Exception:
                    pass

            for cog in tuple(self.__cogs):
                try:
                    self.remove_cog(cog)
                except Exception:
                    pass
        except Exception:
            pass
        await super().close()


class MyHelp(commands.HelpCommand):
    def get_command_signature(self, command):
        return '%s%s %s' % (self.clean_prefix, command.qualified_name, command.signature)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title = "Help")
        for cog, _commands in mapping.items():
            filtered = await self.filter_commands(_commands, sort = True)
            command_signatures = [self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name = cog_name, value = "\n".join(command_signatures).lower(), inline = False)

        channel = self.get_destination()
        await channel.send(embed = embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title = self.get_command_signature(command))
        embed.add_field(name = "Help", value = command.help)
        alias = command.aliases
        if alias:
            embed.add_field(name = "Aliases", value = ", ".join(alias), inline = False)

        channel = self.get_destination()
        await channel.send(embed = embed)

    async def send_group_help(self, group):
        embed = discord.Embed(title = group.full_parent_name)
        for subcommand in group.commands:
            embed.add_field(name = subcommand.name, value = subcommand.description)

        channel = self.get_destination()
        await channel.send(embed = embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(title = cog.qualified_name)
        _commands = cog.get_commands()
        filtered = await self.filter_commands(_commands, sort = True)
        command_signatures = [self.get_command_signature(c) for c in filtered]
        if command_signatures:
            cog_name = getattr(cog, "qualified_name", "No Category")
            embed.add_field(name = cog_name, value = "\n".join(command_signatures), inline = False)

        channel = self.get_destination()
        await channel.send(embed = embed)
