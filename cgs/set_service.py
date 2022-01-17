import discord
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType

from tools.create_embed import EmbedCreator
from tools.translations import _
from tools.permissions import Permissions

from database.models import *
from database.tools import Services


class Service(commands.Cog, Permissions):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot=bot)

    @slash_command(
        name='service',
        description='Set default service on your guild.',
        options=[
            Option(
                name="service",
                description='Choose your prefer service.',
                type=OptionType.STRING,
                required=True,
                choices=[
                    OptionChoice(name='Youtube', value=Services.youtube),
                    OptionChoice(name='Soundcloud', value=Services.soundcloud),
                    OptionChoice(name='Yandex Music', value=Services.yandex_music),
                    OptionChoice(name='Spotify', value=Services.spotify),
                    OptionChoice(name='Twitch', value=Services.twitch),
                ],
            )
        ]
    )
    async def set_services(self, inter: ContextMenuInteraction, service: str):
        if await self.admin_permissions(member=inter.author):
            await Guilds.filter(id=inter.guild.id).update(service=service)
            guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

            embed: EmbedCreator = EmbedCreator(
                title=_('✅ Service has been change to:`{service}`.', guild_db.lang).format(service=service),
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
        await inter.reply(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(Service(bot))
