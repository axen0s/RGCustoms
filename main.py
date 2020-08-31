import discord_bot

with open('token.txt', 'r') as token_file:
    token = token_file.read()  # make your own token.txt =)

RGCustomsBot = discord_bot.RGCustoms()
RGCustomsBot.run(token)
