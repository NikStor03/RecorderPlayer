import datetime
import discord
from discord.ext import commands, tasks
from dislash import SlashInteraction

from youtube_dl import YoutubeDL
from typing import Optional
from database.models import Guilds, Songs
from database.tools import Services

from tools.create_embed import EmbedCreator
from tools.translations import _
from tools.permissions import Permissions


class PlayerButtons:

    buttons_emoji = {
        'resume': '▶️',
        'pause': '⏸',
        'skip': '⏭',
        'loop': '🔁',
    }

    def __init__(self, bot):
        self.bot: Optional[discord.ext.commands.Bot] = bot
        self.embed_msg: Optional[discord.Message] = None

    async def append_reactions(self):

        for emoji in self.buttons_emoji.values():
            try:
                await self.embed_msg.add_reaction(str(emoji))
            except discord.errors.Forbidden:
                return

    @tasks.loop(seconds=0.2)
    async def buttons_control(self, inter, play_next, current_song) -> None:
        reaction, user = await self.bot.wait_for(
            'reaction_add',
            check=lambda reaction,
                         user: user == inter.author and \
                               not user.bot and \
                               reaction.message.id == self.embed_msg.id and \
                               reaction.emoji in self.buttons_emoji.values())
        emoji = reaction.emoji
        if reaction and user:
            try:
                await self.embed_msg.remove_reaction(str(emoji), user)
            except discord.errors.Forbidden:
                pass

        guild_model = await Guilds.filter(id=inter.guild.id).first()
        bot_voice = inter.guild.voice_client

        permissions = Permissions(bot=self.bot)
        if not await permissions.user_roll_permissions(inter):
            embed: EmbedCreator = EmbedCreator(
                title=_('Error: Role', guild_model.lang),
                description=_('{author} don\'t have dj role.', guild_model.lang).format(
                    author=inter.author.mention),
                avatar_url=self.bot.user.avatar_url
            )
            await inter.send(embed=embed.create(), delete_after=5)

        elif bot_voice is not None and \
                user.voice is not None and \
                user.voice.channel == bot_voice.channel:
            if emoji == self.buttons_emoji['resume']:
                if bot_voice.is_paused():
                    bot_voice.resume()

                    embed: EmbedCreator = EmbedCreator(
                        title=_('`▶️ Resumed music`', guild_model.lang),
                        description=_('Music was resumed by {author}', guild_model.lang).format(
                            author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )
                    return await inter.send(embed=embed.create(), delete_after=5)
                else:
                    embed: EmbedCreator = EmbedCreator(
                        title=_('`▶️ Resumed music`', guild_model.lang),
                        description=_('Music **wasn\'t** resumed by {author}. Music already is playing.',
                                      guild_model.lang).format(
                            author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )
                    return await inter.send(embed=embed.create(), delete_after=3)
            elif emoji == self.buttons_emoji['pause']:
                if bot_voice.is_playing():
                    bot_voice.pause()

                    embed: EmbedCreator = EmbedCreator(
                        title=_('`⏸ Paused music`', guild_model.lang),
                        description=_('Music was paused by {author}',
                                      guild_model.lang).format(author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.send(embed=embed.create(), delete_after=5)
                else:
                    embed: EmbedCreator = EmbedCreator(
                        title=_('`⏸ Paused music`', guild_model.lang),
                        description=_('Music wasn\'t paused {author}. Now music isn\'t playing.',
                                      guild_model.lang).format(author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.send(embed=embed.create(), delete_after=3)
            elif emoji == self.buttons_emoji['skip']:
                if len(await guild_model.queue.all()) <= 1:
                    embed: EmbedCreator = EmbedCreator(
                        title=_('`⏭ Skipped music`', guild_model.lang),
                        description=_('Queue is empty. I can\'t skip music by {author}.',
                                      guild_model.lang).format(author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.send(embed=embed.create(), delete_after=3)
                else:
                    song_model = await guild_model.queue.filter(song_id=current_song.song_id).first()
                    await song_model.delete()

                    bot_voice.stop()
                    await play_next()

                    embed: EmbedCreator = EmbedCreator(
                        title=_('`⏭ Skipped music`', guild_model.lang),
                        description=_('Music was skipped by {author}.',
                                      guild_model.lang).format(author=inter.author.mention),
                        avatar_url=self.bot.user.avatar_url
                    )

                    await inter.send(embed=embed.create())
            elif emoji == self.buttons_emoji['loop']:
                if not bot_voice.is_playing():
                    embed: EmbedCreator = EmbedCreator(
                        title=_('`🔁 Loop`', guild_model.lang),
                        description=_('Im not playing anything now.', guild_model.lang),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.channel.send(embed=embed.create(), delete_after=3)

                elif current_song.loop:
                    await Songs.filter(id=current_song.id).update(loop=False)

                    embed: EmbedCreator = EmbedCreator(
                        title=_('`🔁 Loop`', guild_model.lang),
                        description=_('Loop song was **DISabled**.', guild_model.lang),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.channel.send(embed=embed.create(), delete_after=5)

                elif not current_song.loop:
                    await Songs.filter(id=current_song.id).update(loop=True)

                    embed: EmbedCreator = EmbedCreator(
                        title=_('`🔁 Loop`', guild_model.lang),
                        description=_('Loop song was **Enable**.', guild_model.lang),
                        avatar_url=self.bot.user.avatar_url
                    )
                    await inter.channel.send(embed=embed.create(), delete_after=5)


class Player(PlayerButtons):

    def __init__(self):
        self.bot: Optional[discord.ext.commands.Bot] = None
        super().__init__(bot=self.bot)

        self.guild: Optional[discord.Guild] = None
        self.voice: Optional[discord.VoiceClient] = None
        self.text_channel: Optional[discord.TextChannel] = None
        self.inter: Optional[SlashInteraction] = None

        self.song_time: int = 0
        self.song_started_at: Optional[datetime.timedelta] = None
        self.current_song: Optional[Songs] = None
        self.current_task = None

    @staticmethod
    async def create_duration_line(time_start, time_end):
        duration = "{:.2%}".format(time_start.total_seconds() / time_end.total_seconds())[:-1]
        duration = int(float(duration))

        if not str(duration).endswith("0") and len(str(duration)) > 1:
            last_num = int(str(duration)[-1])
            if last_num <= 5:
                duration = duration - last_num
            else:
                last_num = 10 - last_num
                duration = duration + last_num
        duration = int(duration) // 10
        line = '➖' * (duration - 1) + '🟠'
        return "`" + line + '➖'*(9 - duration) + '`'

    async def player_embed(self) -> None:
        next = await self.get_next()
        guild_db = await Guilds.get_or_none(id=self.guild.id)
        current_song = await guild_db.queue.filter(id=self.current_song.id).first()

        self.current_song = current_song
        duration = datetime.datetime.strptime(self.current_song.duration, '%H:%M:%S')
        duration = datetime.timedelta(hours=duration.hour, minutes=duration.minute, seconds=duration.second)

        embed: EmbedCreator = EmbedCreator(
            title=_('❤️ {title}', guild_db.lang).format(
                title=self.current_song.title
            ),
            url=self.current_song.link,
            description=_('**Author:** `{author}`.\n'
                          '**Loop:** `{loop}`\n'
                          '**Next song:** `{next_song}`', guild_db.lang).format(
                author="Didn\'t found" if self.current_song.author is None else self.current_song.author,
                next_song="Queue empty" if next is None else next.title,
                loop='On' if self.current_song.loop else 'Off'
            ),
            avatar_url=self.bot.user.avatar_url
        )
        order = await self.guild.fetch_member(self.current_song.order)
        player_duration = await Player.create_duration_line(
            datetime.timedelta(seconds=self.song_time), duration)

        embed: discord.Embed = embed.create()
        embed.add_field(
            name=f'Duration `{datetime.timedelta(seconds=self.song_time)}/{self.current_song.duration}`\n',
            value=f'{player_duration}')
        embed.set_image(url=self.current_song.thumbnail)
        embed.set_footer(
            text=_('Order by {name}', guild_db.lang
                   ).format(
                name=order.display_name))
        self.embed_msg = await self.text_channel.send(embed=embed)
        await self.append_reactions()
        try:
            self.buttons_control.start(inter=self.inter, play_next=self.play_next, current_song=current_song)
        except RuntimeError:
            self.buttons_control.restart(inter=self.inter, play_next=self.play_next, current_song=current_song)

    async def play_next(self) -> bool:
        guild_model = await Guilds.get_or_none(id=self.guild.id)

        FFMPEG_OPTS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
        self.current_song = await guild_model.queue.all().order_by('-id')
        self.current_song = self.current_song[0]
        if self.current_song is not None:
            self.song_time = 0
            self.voice.stop()
            if self.voice.is_playing():
                self.voice.stop()

            stream = await self.search_by_title(self.current_song.serves, self.current_song.link)

            if not stream:
                wrong_stream = await guild_model.queue.filter(stream=stream).first()
                await wrong_stream.delete()
                return False
            source = await discord.FFmpegOpusAudio.from_probe(
                stream,
                **FFMPEG_OPTS,
                executable='/opt/homebrew/var/homebrew/linked/ffmpeg/bin/ffmpeg')
            try:
                self.voice.play(source)
            except AttributeError:
                return False

            self.voice.is_playing()
            now = datetime.datetime.now()
            self.song_started_at = datetime.timedelta(hours=now.hour, minutes=now.minute, seconds=now.second)

            await self.player_embed()
            return True

        return False

    async def get_next(self, add: bool = False) -> Songs:
        guild_model = await Guilds.get_or_none(id=self.guild.id)
        next_song = await guild_model.queue.all().order_by('-id')
        if len(next_song) >= 2 and not add:
            return next_song[1]
        elif len(next_song) >= 1 and add:
            return next_song[0]

    async def search(self, service: str, title: str, author_id: int) -> bool:
        guild_model = await Guilds.get_or_none(id=self.guild.id)

        if service == Services.youtube:
            print('[+] Opening yt-dl')
            with YoutubeDL({
                'format': 'bestaudio',
                'youtubeincludedashmanifest': 'False',
                'noplaylist': 'True',
                'ignoreerrors': 'True',
                'quiet': 'True'}
            ) as ydl:
                print('[+] Load info yt-dl...')
                data = ydl.extract_info(f"ytsearch:{title}", download=False)['entries'][0]

                if data is None:
                    print('[-] No info got')
                    return False

                print('[+] Info got')
                song = await Songs.create(
                    thumbnail=data['thumbnails'][-1]['url'],
                    title=data['title'],
                    serves=service,
                    song_id=data["id"],
                    link=f'https://www.youtube.com/watch?v={data["id"]}',
                    loop=False,
                    author=data['uploader'],
                    duration=str(datetime.timedelta(seconds=data['duration'])),
                    order=author_id,
                )
                print('[+] Song object created')
                await guild_model.queue.add(song)
                return True
        return False

    async def search_by_title(self, service: str, title: str):
        if service == Services.youtube:
            print('[+] ID: Opening yt-dl')
            with YoutubeDL({
                'format': 'bestaudio',
                'youtubeincludedashmanifest': 'False',
                'noplaylist': 'True',
                'ignoreerrors': 'True',
                'quiet': 'True'}
            ) as ydl:
                print('[+] ID: Load info yt-dl...')
                try:
                    data = ydl.extract_info(f"ytsearch:{title}", download=False)['entries'][0]
                except IndexError:
                    return False

                if data is None:
                    print('[-] ID: No info got')
                    return False

                print('[+] ID: Info got')
                return data['formats'][0]['url']
        return False
