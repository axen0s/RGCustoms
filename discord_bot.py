from discord import Client
import bot_functions


class RGCustoms(Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}, ID {self.user.id}")
        self.bot_funcs = bot_functions.BotFunctions()

    async def on_message(self, message):
        if message.author == self.user:
            return
        if not message.content.startswith('rg:'):
            return
        await self.bot_funcs.handle_message(message)
