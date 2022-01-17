import datetime
import time

import discord
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType

from tools.translations import _
from database.models import Guilds
from tools.permissions import Permissions
from tools.create_embed import EmbedCreator


class InfoAboutBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.start = datetime.datetime.now()

    @slash_command(
        name='bot-info',
        description='See all need info about bot.'
    )
    async def info_bot(self, inter: ContextMenuInteraction):
        guild: Guilds = await Guilds.get_or_none(id=inter.guild.id)
        bot_active = datetime.datetime.now() - self.start
        users = [guild_.members for guild_ in self.bot.guilds]
        users_count = 0
        for i in users:
            users_count += len(i)

        embed: EmbedCreator = EmbedCreator(
            title=_('Info', guild.lang),
            description=_('**Bot info**\n'
                          '> **🏰 Guilds:** {guilds}\n'
                          '> **🟢 Active guilds now:** {active_guilds}\n'
                          '> **👤 Users:** {users}\n\n'
                          '**Creators**\n'
                          '> **👑 Members:** {creators}\n'
                          '> **🛠 Support Guild:** {support_guild}\n\n'
                          '**Another**\n'
                          '> **🔋Bot online more than:** {bot_online}\n'
                          '> **🔋Bot was created at:** {bot_created}\n', guild.lang).format(
                guilds=len(self.bot.guilds),
                active_guilds=" ",
                users=users_count,
                creators="<@" + ">, <@".join([f"{own_id}" for own_id in self.bot.owner_ids]) + ">",
                support_guild='[RecorderPlayer](https://discord.gg/7hVvAhwJ2u)',
                bot_online=f"{bot_active.days}:"
                           f"{int(bot_active.seconds/3600)}:{int(bot_active.seconds/60)}:{bot_active.seconds}",
                bot_created=self.bot.user.created_at.strftime('%d.%m.%Y')
            ),
            avatar_url=self.bot.user.avatar_url
        )
        embed: discord.Embed = embed.create()
        embed.set_thumbnail(url=str(self.bot.user.avatar_url))
        await inter.send(embed=embed)

    @slash_command(
        name='terms-of-use',
        description='See terms of use.'
    )
    async def info_bot(self, inter: ContextMenuInteraction):
        guild: Guilds = await Guilds.get_or_none(id=inter.guild.id)
        embed: EmbedCreator = EmbedCreator(
            title=_('Terms of use 📜', guild.lang),
            description=_('**Terms of Bot 🤖**\n'
                          '> To make the bot work without any problems, give it permission like:\n'
                          '> *Create Instant Invite, Read messages/View Channels, Send Messages,\n'
                          '> Send messages in threads, Embed Links, Attach files, Read Message History,\n'
                          '> Use External Emojis, Use External Stickers, Add Reactions,\n'
                          '> Use Slash Commands, Connect, Speak.*\n\n'
                          '**Terms of User 👤**\n'
                          '> The user gives permission to process his personal data.\n'
                          '> *Namely: user id, username, user roles, user avatar, user permissions.*\n'
                          '> And also user gives permissions to show him any links.\n\n'
                          '**Terms of Guild 🏰**\n'
                          '> The guild permits things like:\n'
                          '> *Processing guild data, show guild links, send out premature messages,*\n'
                          '> *Get a bot a guild link without permission from admins or with permission.*\n\n'
                          'If you have any questions as you read, contact us on our guild [RecorderPlayer](https://discord.gg/7hVvAhwJ2u).', guild.lang),
            avatar_url=self.bot.user.avatar_url
        )
        await inter.send(embed=embed.create())


def setup(bot):
    bot.add_cog(InfoAboutBot(bot))
