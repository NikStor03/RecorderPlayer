import datetime

import discord
from discord.ext import tasks
from discord import VoiceClient
from discord.ext import commands
from dislash import slash_command, ContextMenuInteraction, Option, OptionChoice, OptionType, SlashInteraction

from tools.create_embed import EmbedCreator
from player.player import Player

from typing import Optional

from database.models import Guilds, Songs
from database.tools import Services

from tools.translations import _
from tools.permissions import Permissions


class PlayerFunctions(commands.Cog, Permissions, Player):

    def __init__(self, bot):
        self.bot = bot
        self.player_functions = [
            'join', 'play', 'stop', 'pause',
            'resume', 'join', 'disconnect', 'skip',
            'loop', 'player'
        ]
        self.while_duration.start()
        self.while_voice_is_empty.start()
        super().__init__(bot=bot)

    def cog_unload(self):
        self.while_duration.cancel()
        self.while_voice_is_empty.cancel()

    @commands.Cog.listener()
    async def on_slash_command(self, inter: SlashInteraction):
        # Params which need in :class:Player
        # ==================================
        self.guild = inter.guild
        self.inter = inter
        self.text_channel = inter.channel
        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

        if inter.data.name not in self.player_functions:
            return

        if not await self.user_roll_permissions(inter=inter):
            await inter.reply(
                _("⛔ You are not dj, call someone who have dj role to call this function.",
                  guild_db.lang),
                ephemeral=True)
            return

        try:
            channel = inter.author.voice.channel
        except AttributeError:
            try:
                return await inter.reply(_("⛔ **You are not in voice channel.**", guild_db.lang))
            except:
                return

        voice: VoiceClient = inter.guild.voice_client
        self.voice = voice

        if voice is None and inter.data.name not in ['join', 'play']:
            try:
                await inter.reply(_("⛔ **I'm not in voice channel.**", guild_db.lang))
            except discord.errors.NotFound:
                pass
            return
        if inter.data.name in ['join', 'play']:
            return

        if self.voice is not None and self.voice.channel != channel:
            return await inter.reply(
                _("⛔ {user} **you should be in one voice channel with bot to do it**",
                  guild_db.lang).format(
                  guild_db.lang).format(
                    user=inter.data.author.mention
                )
            )

        if self.voice is None:
            return await inter.reply(
                _("⛔ I'm not playing anything now.",
                  guild_db.lang)
            )

    @tasks.loop(seconds=1)
    async def while_duration(self) -> None:
        try:
            duration = datetime.datetime.strptime(self.current_song.duration, '%H:%M:%S')
            duration = datetime.timedelta(hours=duration.hour, minutes=duration.minute, seconds=duration.second)
            time = datetime.timedelta(seconds=self.song_time)

            if self.voice.is_playing():
                self.song_time += 1

            seconds = str(duration)[5:7]
            if seconds.startswith('0'):
                seconds = int(seconds[1:]) - 1
                seconds = '0' + str(seconds)
            else:
                seconds = int(seconds) - 1

            dur = str(duration)[0:5] + str(seconds)
            print(time, dur)
            if str(time) == dur or time >= duration:
                guild_model = await Guilds.get_or_none(id=self.guild.id)
                song = await guild_model.queue.filter(song_id=self.current_song.song_id).first()
                if not song.loop:
                    await song.delete()

                await self.play_next()
        except AttributeError:
            pass
        except TypeError:
            pass

    @tasks.loop(seconds=1)
    async def while_voice_is_empty(self) -> None:
        try:
            if self.voice and self.voice.is_connected() and len(self.voice.channel.members) <= 1:

                if self.voice.is_playing() and self.current_song is not None:
                    guild_model: Guilds = await Guilds.filter(id=self.inter.guild.id).first()
                    song_model = await guild_model.queue.filter(song_id=self.current_song.song_id).first()
                    await song_model.delete()

                self.voice.stop()
                await self.voice.disconnect()

                try:
                    self.text_channel = None
                    self.song_started_at = None
                    self.current_song = None
                except AttributeError:
                    pass
                self.voice = None
        except AttributeError:
            pass

    @slash_command(
        name='play',
        description='Play song in voice channel.',
        options=[
            Option(
                name="title",
                description='Enter song title.',
                type=OptionType.STRING,
                required=True
            ),
            Option(
                name="service",
                description='Choose service which you prefer more',
                type=OptionType.STRING,
                choices=[
                    OptionChoice(name='YouTube', value=Services.youtube),
                    OptionChoice(name='Soundcloud', value=Services.soundcloud),
                    OptionChoice(name='Twitch', value=Services.twitch),
                    OptionChoice(name='Spotify', value=Services.spotify),
                    OptionChoice(name='YandexMusic', value=Services.yandex_music),
                ],
            )
        ]
    )
    async def play(self, inter: ContextMenuInteraction, service: Optional[str] = None, title: Optional[str] = None):
        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

        channel = inter.author.voice.channel
        # check for bot voice permissions
        if not await self.voice_permissions(inter.guild.id, channel):
            return await inter.reply(_("⛔ I've not permissions to join or speak in this voice channel.", guild_db.lang),
                                     ephemeral=True)

        voice: VoiceClient = inter.guild.voice_client
        self.voice = voice

        # connect bot to voice channel
        if self.voice is None:
            self.voice = await channel.connect()
            await inter.send(
                _("✅ Bot was join to: **<#{channel_id}>**", guild_db.lang).format(channel_id=int(channel.id)))
        elif self.voice.channel != channel:
            self.voice = await self.voice.move_to(channel)
            await inter.send(
                _("✅ Bot was join to: **<#{channel_id}>**", guild_db.lang).format(channel_id=int(channel.id)))
        else:
            await inter.send(_("⚙️ Bot in progress...", guild_db.lang))

        # Params which need in :class:Player
        # ==================================
        self.guild = inter.guild
        self.text_channel = inter.channel
        # ==================================
        if title != 'first':
            if service is None:
                service = guild_db.service

            # create song object in db
            search = await self.search(service, title, inter.author.id)
            if not search:
                return await inter.send(_("**⛔ Something was happened.**\n"
                                          "Why this error happened:\n"
                                          "*Or I didn't find any song by your request.*\n"
                                          "*Or it was live video, but i can't playing live video now :(*", guild_db.lang),
                                        ephemeral=True)

        if self.voice.is_playing():
            next_song = await self.get_next(True)
            embed: EmbedCreator = EmbedCreator(
                title=_("Song `{song}`.", guild_db.lang).format(
                    song=next_song.title,
                ),
                description=_("Song was added to queueButtons by {user}", guild_db.lang).format(user=inter.author.mention),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create())

        if not await self.play_next():
            return await inter.send(_("**⛔ Something was happened.**\n"
                                      "Why this error happened:\n"
                                      "*Or I didn't find any song by your request.*\n"
                                      "*Or it was live video, but i can't playing live video now :(*", guild_db.lang),
                                    ephemeral=True)

    # ======================================= JOIN - DISCONNECT ============================================
    @slash_command(
        name='join',
        description='Join bot to voice channel'
    )
    async def join(self, inter: ContextMenuInteraction):
        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

        try:
            channel = inter.author.voice.channel
        except AttributeError:
            return await inter.reply(_("⛔ You are not in voice channel.", guild_db.lang), ephemeral=True)

        voice: VoiceClient = inter.guild.voice_client
        self.voice = voice
        # check for bot voice permissions
        if not await self.voice_permissions(inter.guild.id, channel):
            return await inter.reply(_("⛔ I've not permissions to join or speak in this voice channel.", guild_db.lang), ephemeral=True)

        try:
            if voice and voice.is_connected():
                self.voice = await voice.move_to(channel)
            else:
                self.voice = await channel.connect()
        except discord.errors.ClientException:
            await inter.send(
                _("⛔ Bot was already connected to: **<#{channel_id}>**", guild_db.lang).format(
                    channel_id=int(channel.id)
                ), ephemeral=True
            )
            return

        await inter.send(_("✅ Bot was join to: **<#{channel_id}>**", guild_db.lang).format(
            channel_id=int(channel.id)))

    @slash_command(
        name='disconnect',
        description='Bot will disconnect from voice channel.'
    )
    async def disconnect(self, inter: ContextMenuInteraction):
        guild_db: Guilds = await Guilds.filter(id=inter.guild.id).first()

        try:
            True if self.voice else False
        except AttributeError:
            return

        if self.voice is None:
            return await inter.reply(_("Call me to voice channel", guild_db.lang))

        try:
            if self.current_song is not None:
                cur_s = await guild_db.queue.filter(song_id=self.current_song.song_id).first()
                await cur_s.delete()
        except AttributeError:
            pass

        try:
            self.text_channel = None
            self.song_started_at = None
            self.current_song = None
        except AttributeError:
            pass

        self.voice.stop()

        channel = self.voice.channel
        await self.voice.disconnect()

        self.voice = None

        await inter.send(
            _("📤 Bot was remove from: **<#{channel_id}>**", guild_db.lang).format(channel_id=int(channel.id)))

    # ======================================= STOP - RESUME - PAUSE ========================================
    @slash_command(
        name='stop',
        description='Stop music.'
    )
    async def stop(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()
        try:
            True if self.voice else False
        except AttributeError:
            return

        if self.voice.is_playing():
            song_model = await guild_model.queue.filter(song_id=self.current_song.song_id).first()
            await song_model.delete()

            try:
                self.text_channel = None
                self.song_started_at = None
                self.current_song = None
            except AttributeError:
                pass

            self.voice.stop()
            embed: EmbedCreator = EmbedCreator(
                title=_('`⏹ Stopped music`', guild_model.lang),
                description=_('Music was stopped by {author}', guild_model.lang).format(author=inter.author.mention),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create())
        elif not self.voice.is_playing():
            embed: EmbedCreator = EmbedCreator(
                title=_('`⏹ Stopped music`', guild_model.lang),
                description=_('Music wasn\'t stopped. Now music isn\'t playing.', guild_model.lang),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create(), ephemeral=True)

    @slash_command(
        name='pause',
        description='Pause music.'
    )
    async def set_pause(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()

        if self.voice is None:
            return

        if self.voice.is_playing():
            self.voice.pause()


            embed: EmbedCreator = EmbedCreator(
                title=_('`⏸ Paused music`', guild_model.lang),
                description=_('Music was paused by {author}', guild_model.lang).format(author=inter.author.mention),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create())
        else:
            embed: EmbedCreator = EmbedCreator(
                title=_('`⏸ Paused music`', guild_model.lang),
                description=_('Music wasn\'t paused. Now music isn\'t playing.', guild_model.lang),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create(), ephemeral=True)

    @slash_command(
        name='resume',
        description='Resume music.'
    )
    async def resume(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()

        if self.voice.is_paused():
            self.voice.resume()

            embed: EmbedCreator = EmbedCreator(
                title=_('`▶️ Resumed music`', guild_model.lang),
                description=_('Music was resumed by {author}', guild_model.lang).format(author=inter.author.mention),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create())
        else:
            embed: EmbedCreator = EmbedCreator(
                title=_('`▶️ Resumed music`', guild_model.lang),
                description=_('Music wasn\'t resumed. Music already is playing.', guild_model.lang),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create(), ephemeral=True)

    # ====================================== VOLUME - SKIP ================================================
    @slash_command(
        name='skip',
        description='Skip to next song in queueButtons.',
    )
    async def skip(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()
        try:
            True if self.voice else False
        except AttributeError:
            return

        if len(await guild_model.queue.all()) <= 1:
            embed: EmbedCreator = EmbedCreator(
                title=_('`⏭ Skipped music`', guild_model.lang),
                description=_('Queue is empty. I can\'t skip music.', guild_model.lang),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create(), ephemeral=True)
        try:
            if self.current_song is None:
                embed: EmbedCreator = EmbedCreator(
                    title=_('`⏭ Skipped music`', guild_model.lang),
                    description=_('I\'m not playing anything now. I can\'t skip song.', guild_model.lang),
                    avatar_url=self.bot.user.avatar_url
                )
                return await inter.send(embed=embed.create(), ephemeral=True)
        except AttributeError:
            embed: EmbedCreator = EmbedCreator(
                title=_('`⏭ Skipped music`', guild_model.lang),
                description=_('I\'m not playing anything now. I can\'t skip song.', guild_model.lang),
                avatar_url=self.bot.user.avatar_url
            )
            return await inter.send(embed=embed.create(), ephemeral=True)
        song_model = await guild_model.queue.filter(id=self.current_song.id).first()
        await song_model.delete()

        self.current_song = None
        self.voice.stop()
        await self.play_next()

        embed: EmbedCreator = EmbedCreator(
            title=_('`⏭ Skipped music`', guild_model.lang),
            description=_('Music was skipped.', guild_model.lang),
            avatar_url=self.bot.user.avatar_url
        )

        await inter.send(embed=embed.create())

    @slash_command(
        name='loop',
        description='Set loop.'
    )
    async def loop(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()
        try:
            True if self.voice else False
        except AttributeError:
            return

        if self.voice.is_playing() and self.current_song is not None:
            if self.current_song.loop:
                await Songs.filter(id=self.current_song.id).update(loop=False)

                embed: EmbedCreator = EmbedCreator(
                    title=_('`🔁 Loop`', guild_model.lang),
                    description=_('Loop song was **DISabled**.', guild_model.lang),
                    avatar_url=self.bot.user.avatar_url
                )
            elif not self.current_song.loop:
                await Songs.filter(id=self.current_song.id).update(loop=True)

                embed: EmbedCreator = EmbedCreator(
                    title=_('`🔁 Loop`', guild_model.lang),
                    description=_('Loop song was **Enable**.', guild_model.lang),
                    avatar_url=self.bot.user.avatar_url
                )
            return await inter.reply(embed=embed.create())

        embed: EmbedCreator = EmbedCreator(
            title=_('`🔁 Loop`', guild_model.lang),
            description=_('Im not playing anything now.', guild_model.lang),
            avatar_url=self.bot.user.avatar_url
        )
        await inter.reply(embed=embed.create())

    @slash_command(
        name='player',
        description='Call current cong player'
    )
    async def player(self, inter: ContextMenuInteraction):
        guild_model: Guilds = await Guilds.filter(id=inter.guild.id).first()
        try:
            True if self.voice else False
        except AttributeError:
            return

        if self.voice is not None and self.voice.is_playing() and self.current_song is not None:
            await self.player_embed()
            await inter.reply('\❤️')
            return
        try:
            if self.current_song is None or not self.voice.is_playing():
                return await inter.reply(
                    _("⛔ I'm not playing anything now.",
                      guild_model.lang), ephemeral=True
                )
        except AttributeError:
            return await inter.reply(
                _("⛔ I'm not playing anything now.",
                  guild_model.lang), ephemeral=True
            )



def setup(bot):
    bot.add_cog(PlayerFunctions(bot))
