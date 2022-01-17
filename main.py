import os
import configparser
import asyncio

import discord
from discord.ext import commands, tasks
from dislash import InteractionClient
from database.start_db import InitializationDB


class Bot(commands.Bot, InitializationDB):

    def __init__(self) -> None:
        super().__init__(
            command_prefix='!',
            intents=discord.Intents.all(),
            help_command=None,
            owner_ids=[398538710993600523]
        )

    @tasks.loop(minutes=10)
    async def while_description(self) -> None:
        activity = discord.Activity(
            name=f"{len(self.guilds)} servers",
            type=discord.ActivityType.listening)

        await self.change_presence(
            activity=activity,
            status=discord.Status.online
        )

    async def on_ready(self) -> None:
        print('I\'m ready')
        await self.run_tortoise()

        try:
            await self.while_description.start()
        except RuntimeError:
            pass


conf = configparser.ConfigParser()
conf.read("tools/config.ini")

bot = Bot()
inter_client = InteractionClient(bot, test_guilds=[int(conf['guilds_id'][guild_id]) for guild_id in conf['guilds_id']])


@bot.command()
async def load(ctx, extensions):
    bot.load_extensions(f'cgs.{extensions}')


@bot.command()
async def reload(ctx, extensions):
    bot.unload_extension(f'cgs.{extensions}')


@bot.command()
async def unload(ctx, extensions):
    bot.unload_extension(f'cgs.{extensions}')
    bot.load_extensions(f'cgs.{extensions}')

for filename in os.listdir('./cgs'):
    if filename.endswith('.py'):
        bot.load_extension(f'cgs.{filename[:-3]}')

bot.run(conf['bot']['token'])
