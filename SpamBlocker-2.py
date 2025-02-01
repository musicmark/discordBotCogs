import asyncio, discord, requests
from discord.ext import commands

log_channel_id = int(discord.TextChannel.id)  # Enter the unique ID for the log channel (로그 채널로 사용할 채널의 ID를 입력해주세요)

async def spam_chack(bot: commands.Bot, message: discord.Message):
    split_message = message.content.replace("[", "splitwordmumaasdf").replace(")", "splitwordmumaasdf").split("splitwordmumaasdf")
    for msg in split_message:
        if "](https://" in msg and "." in msg:
            response = requests.get("https://data.iana.org/TLD/tlds-alpha-by-domain.txt")
            html_text = response.text.lower()
            asdf = html_text.splitlines()
            domains = asdf[1:]
            domain = msg.split(".")
            if domain[-1].split("/")[0] in domains:
                await message.delete()
                embed=discord.Embed(title="스팸 메시지가 감지되었습니다.", description="스팸 메시지가 감지되어 삭제 처리 하였습니다.", colour=discord.Colour.red())
                send_message = await message.channel.send(embed=embed)
                embed.add_field(name="메시지 내용", value=message.content)
                embed.add_field(name="하이퍼링크", value=f"\\[{msg})")
                log_channel = await bot.get_channel(log_channel_id)
                await log_channel.send(embed=embed)
                await asyncio.sleep(5)
                await send_message.delete()

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        await spam_chack(self.bot, message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after: discord.Message):
        await spam_chack(self.bot, after)

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))