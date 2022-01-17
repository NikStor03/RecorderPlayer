import datetime
import discord
import dislash
from discord.ext import commands, tasks
from dislash import SlashInteraction

from youtube_dl import YoutubeDL
from typing import Optional, List
from database.models import Guilds, Songs
from database.tools import Services

from tools.create_embed import EmbedCreator
from tools.translations import _
from tools.permissions import Permissions


class QueueReactions:

    page = 1
    buttons_emoji = {
        'first': '⏮',
        'previous': '◀️',
        'next': '▶️',
        'last': '⏭'
    }

    def __init__(self, bot):
        self.queue_songs: Optional[List[str]] = None
        self.embed_msg: Optional[discord.Message] = None

        self.bot = bot
        self.inter: Optional[dislash.ContextMenuInteraction] = None

    async def update_message(self):
        guild_model = await Guilds.get_or_none(id=self.inter.guild.id)
        queue = await guild_model.queue.all()

        # all songs in queueButtons
        self.queue_songs = [
            f"{index + 1}. "
            f"[{song.title}]({song.link}) "
            f"{str(song.serves).title()} <@!{song.order}>\n"
            for index, song in enumerate(queue[::-1])]

        # songs which shows on page
        page_songs = ""
        for index, i in enumerate(range(0, len(self.queue_songs), 5)):
            if i == 0:
                i = 1
            if index+1 == self.page:
                for song in self.queue_songs[(i+5)-5:i+5]:
                    page_songs += f"{song}"
                break

        if not page_songs:
            page_songs = _('Queue is empty.')

        totalpages = len(self.queue_songs)
        if totalpages == 0:
            totalpages = 1
        embed: EmbedCreator = EmbedCreator(
            title=_('Queue `{guild}`.', guild_model.queue).format(
                guild=self.inter.guild.name
            ),
            description=f'[{self.page}/{totalpages}]\n{page_songs}',
            avatar_url=self.bot.user.avatar_url
        )
        try:
            if self.embed_msg is None:
                self.embed_msg = await self.inter.send(embed=embed.create())
                await self.append_reactions()
            else:
                await self.embed_msg.edit(embed=embed.create())
        except AttributeError:
            self.embed_msg = await self.inter.send(embed=embed.create())
            await self.append_reactions()
        try:
            self.buttons_control.start(inter=self.inter)
        except RuntimeError:
            self.buttons_control.restart(inter=self.inter)

    async def append_reactions(self):

        for emoji in self.buttons_emoji.values():
            try:
                await self.embed_msg.add_reaction(str(emoji))
            except discord.errors.Forbidden:
                return

    @tasks.loop(seconds=0.2)
    async def buttons_control(self, inter) -> None:
        reaction, user = await self.bot.wait_for(
            'reaction_add',
            check=lambda reaction,
                         user: user == inter.author and \
                               not user.bot and \
                               reaction.message.id == self.embed_msg.id and \
                               reaction.emoji in self.buttons_emoji.values())
        emoji = reaction.emoji
        try:
            await self.embed_msg.remove_reaction(str(emoji), user)
        except discord.errors.Forbidden:
            pass

        total_pages = len(self.queue_songs) // 5
        if total_pages == 0:
            total_pages = 1

        if emoji == self.buttons_emoji['first']:
            self.page = 1
        elif emoji == self.buttons_emoji['next']:
            if self.page >= total_pages:
                self.page = total_pages
            else:
                self.page += 1
        elif emoji == self.buttons_emoji['previous']:
            if self.page <= 1:
                self.page = 1
            else:
                self.page -= 1
        elif emoji == self.buttons_emoji['last']:
            self.page = total_pages
        await self.update_message()

