import io
import aiohttp
import discord

from typing import Any
from datetime import datetime

from redbot.core import Config, checks, commands
from redbot.core.bot import Red

Cog: Any = getattr(commands, "Cog", object)

class Gallery(Cog):

    __author__ = "shivo58"

    def __init__(self, bot: Red):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=476311479898398327, force_registration=True
        )
        default_guild = {
            "logchannel": None,
            "channels": [],
            "emojis": []
        }
        self.config.register_guild(**default_guild)

    async def red_delete_data_for_user(self, **kwargs):
        return

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def gallerylogchannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set log channel"""
        if channel is not None:
            await self.config.guild(ctx.guild).logchannel.set(channel.id)
            await ctx.send(f"{channel.mention} has been set as log channel")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def dsgallerylogchannel(self, ctx: commands.Context):
        """Disable log channel"""
        await self.config.guild(ctx.guild).logchannel.set(None)
        await ctx.send(f"Log channel has been disabled")

    async def downloadimage(self, str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            async with session.get(str) as response:
                if response.status != 200:
                    return None
                return io.BytesIO(await response.read())

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def gallerychannel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Add or remove channel"""
        async with self.config.guild(ctx.guild).channels() as channels:
            if channel.id not in await self.config.guild(ctx.guild).channels():
                channels.append(channel.id)
                await ctx.send(f"{channel.mention} has been added.")
            else:
                channels.remove(channel.id)
                await ctx.send(f"{channel.mention} has been removed.")

    @commands.command()
    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    async def galleryreaction(self, ctx: commands.Context, emoji):
        """Add or remove reaction"""
        async with self.config.guild(ctx.guild).emojis() as emojis:
            if emoji not in await self.config.guild(ctx.guild).emojis():
                emojis.append(emoji)
                await ctx.send(f"{emoji} has been added.")
            else:
                emojis.remove(emoji)
                await ctx.send(f"{emoji} has been removed.")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.channel.id not in await self.config.guild(reaction.message.guild).channels():
            return
        channel = await self.bot.fetch_channel(reaction.message.channel.id)
        message = await channel.fetch_message(reaction.message.id)
        for r in message.reactions:
            if user in await r.users().flatten() and not user.bot and str(r) != str(reaction.emoji):
                await message.remove_reaction(reaction.emoji, user)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.channel.id not in await self.config.guild(message.guild).channels():
            return
        if message.author.bot:
            return
        if not message.attachments:
            await message.delete()
            return
        channel = self.bot.get_channel(message.channel.id)
        if not channel.permissions_for(message.guild.me).embed_links:
            return
        embedcolor = 0x2a6ed4
        await message.delete()
        embed = discord.Embed(color=embedcolor, timestamp=datetime.utcnow())
        messages = list()
        for attachment in message.attachments:
            if attachment.filename.endswith(".gif") or attachment.filename.endswith(".jpg") or attachment.filename.endswith(".png") or attachment.filename.endswith(".webp"):
                pass
            else:
                return
            imagedata = await self.downloadimage(attachment.url)
            if imagedata is None:
                return
            file = discord.File(imagedata, filename=attachment.filename) 
            embed.set_image(url="attachment://"+attachment.filename)
            if message.content in [".nick"]:
                embed.set_author(name=message.author, icon_url=str(message.author.avatar_url))
            botmsg = await channel.send(embed=embed, file=file)
            for emoji in await self.config.guild(message.guild).emojis():
                await botmsg.add_reaction(emoji)
            messages.append(botmsg)
        logchannelcfg = await self.config.guild(message.guild).logchannel()
        if logchannelcfg is not None:
            logchannel = self.bot.get_channel(logchannelcfg)
            description = f"{message.author.mention} posted {len(messages)} images\n"
            for singlemessage in messages:
                description += f"[#{singlemessage.id}]({singlemessage.jump_url})\n"
            logembed = discord.Embed(color=embedcolor, timestamp=datetime.utcnow(), description=description)
            await logchannel.send(embed=logembed)