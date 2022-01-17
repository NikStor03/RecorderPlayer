import discord
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType, SlashInteraction

from database.models import Guilds

from tools.translations import _
from tools.create_embed import EmbedCreator
from tools.permissions import Permissions
from queueButtons.queue_buttons import QueueReactions


class Queue(commands.Cog, Permissions, QueueReactions):

    def __init__(self, bot):
        self.bot = bot
        self.inter = None
        super().__init__(bot=bot)

    @slash_command(
        name='queue',
        description='Queue functions.'
    )
    async def queue(self, inter: ContextMenuInteraction):
        pass

    @queue.sub_command(
        name='show',
        description='Show active queue.'
    )
    async def show(self, inter: ContextMenuInteraction):
        if self.inter is None or self.inter != inter:
            self.inter = inter
            self.embed_msg = None
        await self.update_message()

    @queue.sub_command(
        name='clear-duplicate',
        description='Clear from all duplicate songs queue.'
    )
    async def clear_duplicate(self, inter: ContextMenuInteraction):
        guild_model = await Guilds.get_or_none(id=inter.guild.id)

        if not await self.user_roll_permissions(inter=inter):
            await inter.reply(
                _("⛔ You are not dj, call someone who have dj role to call this function.",
                  guild_model.lang),
                ephemeral=True)
            return

        queue = await guild_model.queue.all()
        queue_songs_id = [song.song_id for song in queue]
        queue_songs_id = list(set([(song, queue_songs_id.count(song)) for song in queue_songs_id]))

        duplicate_count = 0
        for song, count in queue_songs_id:
            if count > 1:
                delete_songs = await guild_model.queue.filter(song_id=song)
                for s in delete_songs[1:]:
                    duplicate_count += 1
                    await s.delete()

        embed: EmbedCreator = EmbedCreator(
            title=_('Queue `{guild}`.', guild_model.queue).format(
                guild=inter.guild.name
            ),
            description=_('Was deleted {count} duplicates.', guild_model.lang).format(count=duplicate_count),
            avatar_url=self.bot.user.avatar_url
        )
        await inter.send(embed=embed.create())


def setup(bot):
    bot.add_cog(Queue(bot))
