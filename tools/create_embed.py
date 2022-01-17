import discord
from typing import Optional


class EmbedCreator:

    def __init__(
            self,
            title: Optional[str] = None,
            description: str = '',
            color: int = 0xFF7606,
            avatar_url: Optional[str] = None,
            url: str = '') -> None:
        self.title = title
        self.description = description
        self.color = color
        self.avatar_url = avatar_url
        self.url = url

    def create(self):
        embed: discord.Embed = discord.Embed(
            title=self.title,
            url=self.url,
            description=self.description,
            color=self.color)
        embed.set_footer(text='All rights reserved', icon_url=self.avatar_url)
        return embed
