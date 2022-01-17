from discord.ext import commands

from database.models import Guilds, Users
from tools.create_embed import EmbedCreator

from typing import Optional


class Admin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name='give-premium',
        description='Give premium any guild.',
        hiden=True
    )
    async def give_premium(self, ctx: commands.Context, guild_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or guild_id is None:
            return

        guild: Guilds = await Guilds.get_or_none(id=guild_id)
        if guild is not None:
            if guild.premium:
                embed: EmbedCreator = EmbedCreator(title='Error', description=f'Guild: {guild_id} already took premium.', avatar_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed.create())
            else:
                await Guilds.filter(id=guild_id).update(premium=True)
                embed: EmbedCreator = EmbedCreator(title='Success', description=f'Guild: {guild_id} was taken premium.', avatar_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed.create())

    @commands.command(
        name='leave-premium',
        description='Leave premium any guild.',
        hiden=True
    )
    async def leave_premium(self, ctx: commands.Context, guild_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or guild_id is None:
            return

        guild: Guilds = await Guilds.get_or_none(id=guild_id)
        if guild is not None:
            if guild.premium:
                await Guilds.filter(id=guild_id).update(premium=False)
                embed: EmbedCreator = EmbedCreator(title='Success',
                                                   description=f'Guild: {guild_id} was remove premium.',
                                                   avatar_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed.create())
            else:
                await Guilds.filter(id=guild_id).update(premium=True)
                embed: EmbedCreator = EmbedCreator(title='Error', description=f'Guild: {guild_id} doesnt have premium.',
                                                   avatar_url=self.bot.user.avatar_url)
                await ctx.send(embed=embed.create())

    @commands.command(
        name='ban-user-global',
        description='Ban user for all servers.',
        hiden=True
    )
    async def ban_user(self, ctx: commands.Context, user_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or user_id is None:
            return

        banned_user = await Users.get_or_none(user_banned_id=user_id)
        if banned_user is None:
            await Users.create(user_banned_id=user_id)
            embed: EmbedCreator = EmbedCreator(title='Success',
                                               description=f'User: <@{user_id}> was banned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())
        else:
            embed: EmbedCreator = EmbedCreator(title='Error',
                                               description=f'User: <@{user_id}> was already banned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())

    @commands.command(
        name='unban-user-global',
        description='Unban user for all servers.',
        hiden=True
    )
    async def unban_user(self, ctx: commands.Context, user_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or user_id is None:
            return

        banned_user = await Users.get_or_none(user_banned_id=user_id)
        if banned_user is not None:
            await Users.filter(user_banned_id=user_id).delete()
            embed: EmbedCreator = EmbedCreator(title='Success',
                                               description=f'User: <@{user_id}> was unbanned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())
        elif banned_user is None:
            embed: EmbedCreator = EmbedCreator(title='Error',
                                               description=f'User: <@{user_id}> had never banned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())

    @commands.command(
        name='ban-guild-global',
        description='Ban guild global.',
        hiden=True
    )
    async def ban_guild(self, ctx: commands.Context, guild_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or guild_id is None:
            return

        guild = await Guilds.get_or_none(id=guild_id)
        if not guild.ban:
            await Guilds.filter(id=guild_id).update(ban=True)
            embed: EmbedCreator = EmbedCreator(title='Success',
                                               description=f'Guild: <@{guild}> was banned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())
        elif guild.ban:
            embed: EmbedCreator = EmbedCreator(title='Error',
                                               description=f'Guild: <@{guild}> was already banned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())

    @commands.command(
        name='unban-guild-global',
        description='Ban guild global.',
        hiden=True
    )
    async def unban_guild(self, ctx: commands.Context, guild_id: Optional[int] = None):
        if ctx.author.id not in self.bot.owner_ids or guild_id is None:
            return

        guild = await Guilds.get_or_none(id=guild_id)
        if guild.ban:
            await Guilds.filter(id=guild_id).update(ban=False)
            embed: EmbedCreator = EmbedCreator(title='Success',
                                               description=f'Guild: <@{guild}> was unbanned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())
        elif not guild.ban:
            embed: EmbedCreator = EmbedCreator(title='Error',
                                               description=f'Guild: <@{guild}> was already unbanned.',
                                               avatar_url=self.bot.user.avatar_url)
            await ctx.send(embed=embed.create())


def setup(bot):
    bot.add_cog(Admin(bot))
