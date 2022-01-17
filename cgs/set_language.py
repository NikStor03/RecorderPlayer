import discord
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType

from tools.create_embed import EmbedCreator
from tools.translations import _
from tools.permissions import Permissions

from database.models import *
from database.tools import Languages


class Language(commands.Cog, Permissions):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot=bot)

    @slash_command(
        name='language',
        description='Set language on your guild.',
        options=[
            Option(
                name="language",
                description='Choose your prefer language.',
                type=OptionType.STRING,
                required=True,
                choices=[
                    OptionChoice(name='Russian', value=Languages.russian),
                    OptionChoice(name='English', value=Languages.english),
                    OptionChoice(name='Ukrainian', value=Languages.ukrainian),
                ],
            )
        ]
    )
    async def set_language(self, inter: ContextMenuInteraction, language: str):
        if await self.admin_permissions(member=inter.author):
            await Guilds.filter(id=inter.guild.id).update(lang=language)
            guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

            embed: EmbedCreator = EmbedCreator(
                title=_('✅ Language has been changed to: `{language}`.', guild_db.lang).format(language=language),
                avatar_url=self.bot.user.avatar_url
            )
            embed: discord.Embed = embed.create()
            await inter.send(embed=embed)
            return

        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()
        embed: EmbedCreator = EmbedCreator(
            title=_('⛔️ You don\'t have enough permissions.', guild_db.lang),
            avatar_url=self.bot.user.avatar_url
        )
        embed: discord.Embed = embed.create()
        await inter.send(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Language(bot))
