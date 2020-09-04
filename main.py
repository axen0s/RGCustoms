from src import discord_bot
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
section = config['CONFIG']
token = section['token']
prefix = section['prefix']

RGCustomsBot = discord_bot.RGCustoms(prefix)
RGCustomsBot.run(token)
