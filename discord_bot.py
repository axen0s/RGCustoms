from discord import Client
import bot_functions


class RGCustoms(Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}, ID {self.user.id}")

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not message.content.startswith('rg:'):
            return
        bot_funcs = bot_functions.BotFunctions()
        await bot_funcs.handle_message(message)
        # await message.channel.send(embed=discord.Embed.from_dict(embed_data))
