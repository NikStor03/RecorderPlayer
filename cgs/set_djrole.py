import discord
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType

from database.models import Guilds

from tools.translations import _
from tools.create_embed import EmbedCreator
from tools.permissions import Permissions


class DjRole(commands.Cog, Permissions):

    def __init__(self, bot):
        self.bot = bot
        super().__init__(bot=bot)

    @slash_command(
        name='dj-role'
    )
    async def dj_role(self, inter: ContextMenuInteraction):
        pass

    @dj_role.sub_command(
        name='set',
        description='Set dj role.',
        options=[
            Option(
                name="role",
                description='Enter any role, which should be dj.',
                type=OptionType.ROLE,
                required=True,
            )
        ]
    )
    async def set_dj_role(self, inter: ContextMenuInteraction, role: discord.Role):
        if not await self.admin_permissions(member=inter.author):
            return

        guild: Guilds = await Guilds.get_or_none(id=inter.guild.id)

        await Guilds.filter(id=inter.guild.id).update(dj_role_id=role.id)
        embed: EmbedCreator = EmbedCreator(
            title=_('Dj role', guild.lang),
            description=_('✅Dj role was updated to: {role}\n'
                          'Now users only with this role can call player functions.\n', guild.lang).format(role=role.mention),
            avatar_url=self.bot.user.avatar_url)
        await inter.send(embed=embed.create())

    @dj_role.sub_command(
        name='delete',
        description='Delete dj role.'
    )
    async def delete_dj_role(self, inter: ContextMenuInteraction):
        if not await self.admin_permissions(member=inter.author):
            return
        guild: Guilds = await Guilds.get_or_none(id=inter.guild.id)

        if not guild.dj_role_id:
            embed: EmbedCreator = EmbedCreator(
                title=_("Dj role", guild.lang),
                description=_("⛔This guild does not have dj role", guild.lang),
                avatar_url=self.bot.user.avatar_url)
            await inter.send(embed=embed.create())
            return

        await Guilds.filter(id=inter.guild.id).update(dj_role_id=None)
        embed: EmbedCreator = EmbedCreator(
            title=_('Dj role', guild.lang),
            description=_(
                '✅Dj role was deleted\nNow all users can call player functions.', guild.lang),
            avatar_url=self.bot.user.avatar_url)
        await inter.send(embed=embed.create())


def setup(bot):
    bot.add_cog(DjRole(bot))