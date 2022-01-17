import configparser

import discord
from discord.ext import commands

from tortoise.exceptions import DoesNotExist
from tools.create_embed import EmbedCreator

from database.models import *
from database.tools import Languages


class GuildJoin(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.conf = configparser.ConfigParser()
        self.conf.read('tools/config.ini')

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild) -> None:
        try:
            model_guild: Guilds = await Guilds.get(id=guild.id)

            # if bot was banned - leave
            if model_guild.ban:
                print(model_guild.ban)
                await guild.leave()
                return

        except DoesNotExist:
            region: str = guild.region
            if region == 'russia':
                lang = Languages.russian
            else:
                lang = Languages.english

            await Guilds.create(id=guild.id, lang=lang)

        log_channel: discord.TextChannel = self.bot.get_channel(int(self.conf['channel_ids']['log_guilds_join']))

        # crete embed
        embed: EmbedCreator = EmbedCreator(
            title='Guild join',
            description=f'**info**\n'
                        f'> ID: {guild.id}\n'
                        f'> Name: {guild.name}\n'
                        f'> Members:\n'
                        f'> . . . . All: {len(guild.members)}\n'
                        f'> . . . . Bots: {len([member for member in guild.members if member.bot])}\n'
                        f'> Region: {guild.region}',
            avatar_url=self.bot.user.avatar_url
        )
        embed: discord.Embed = embed.create()

        await log_channel.send(embed=embed)


def setup(bot):
    bot.add_cog(GuildJoin(bot))
