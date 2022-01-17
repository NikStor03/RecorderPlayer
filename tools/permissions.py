import discord
from database.models import Guilds
from tools.translations import _


class Permissions:

    def __init__(self, bot):
        self.bot = bot

    async def voice_permissions(self, guild_id: int, channel: discord.VoiceChannel) -> bool:
        guilds: list[discord.Guild] = self.bot.guilds
        for guild in guilds:
            if guild.id == guild_id:
                bot_member = guild.get_member(self.bot.user.id)
                permissions = bot_member.permissions_in(channel)
                if permissions.speak and permissions.connect and permissions.view_channel:
                    return True
                else:
                    return False

    async def user_roll_permissions(self, inter):
        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()
        if guild_db.dj_role_id is not None:

            role = inter.guild.get_role(guild_db.dj_role_id)
            if role not in inter.author.roles and \
                    not (inter.author.guild_permissions.administrator or inter.author.id == inter.guild.owner.id):
                return False
            return True

    async def admin_permissions(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator:
            return True
        else:
            return False
