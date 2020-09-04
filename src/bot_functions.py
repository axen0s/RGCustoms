from src import image_gen, replay_reader, summoner_data
from discord import File
import os


def msg2sum(content, d_id):
    space_split = content.split(" ")
    if space_split[1].startswith('<@!') and space_split[1].endswith('>'):
        return " ".join(space_split[2:]), space_split[1][3:-1]  # given summonername, given discord id
    else:
        return " ".join(space_split[1:]), d_id  # given summoner name, author's discord id


class BotFunctions:
    def __init__(self, prefix):
        self.summoner_data = summoner_data.SummonerData()
        self.image_gen = image_gen.ImageGen()
        self.prefix = prefix
        self.commands = {"id": {"func": self.id, "help": "rg:id {ID} - Gets info of match ID"},
                         "replay": {"func": self.replay,
                                    "help": "rg:replay - Attach a .ROFL or .json from a replay for the bot to display"},
                         "log": {"func": self.log, "help": "rg:log - Log a replay ID into the database"},
                         "link": {"func": self.link,
                                  "help": "rg:link {Summoner Name} - Links a summoner name to your Discord. Mention someone before the summoner name to link it to their Discord instead"},
                         "unlink": {"func": self.unlink, "help": "rg:unlink {Summoner Name} - Opposite of rg:link"},
                         "profile": {"func": self.profile,
                                     "help": "rg:profile {Summoner Name or @} {ha or sr, leave blank for all} - Get player's stats"},
                         "history": {"func": self.history,
                                     "help": "rg:history {Summoner Name or @} {ha or sr, leave blank for all} - Get recent matches"},
                         "help": {"func": self.help,
                                  "help": "rg:help {command} - Get syntax for given command, leave blank for list of commands"}}

    async def log(self, message=None, ids=None):
        if ids is None:
            ids = message.content[7:].split(",")
        for replay_id in ids:
            if os.path.exists("../data/logged.txt"):
                with open("../data/logged.txt", "r") as f:
                    logged_ids = f.readlines()
                    if replay_id + '\n' in logged_ids:
                        if message:
                            await message.channel.send(
                                content=f"Match {replay_id} was previously logged")  # The match has already been logged.
                        return
            elif not os.path.exists("../data/logged.txt"):
                with open("../data/logged.txt", "w") as f:
                    pass
            with open("../data/logged.txt", "a") as f:
                f.write(f"{replay_id}\n")
            self.summoner_data.log(replay_id)
            if message:
                await message.channel.send(content=f"Match {replay_id} logged")

    async def id(self, message=None, ids=None):  # Get match from ID
        if ids is None:
            ids = message.content[6:].split(',')
        for replay_id in ids:
            try:
                replay = replay_reader.ReplayReader(replay_id)
            except FileNotFoundError:
                await message.channel.send(content="Replay file not found")
                return
            if not os.path.exists(f'data/match_imgs/{replay_id}.png'):
                replay.generate_game_img()
            await message.channel.send(file=File(f'data/match_imgs/{replay_id}.png'))

    async def replay(self, message):  # Submit new replay
        attachments = message.attachments
        ids = []
        if len(attachments) > 0:
            for attachment in attachments:
                if attachment.filename.endswith('.rofl') or attachment.filename.endswith('.json'):
                    await attachment.save(f"data/replays/{attachment.filename}")
                    await message.channel.send(content=f"Replay {attachment.filename[:-5]} saved")
                    ids.append(attachment.filename[:-5])
                else:
                    await message.channel.send(content=f"File {attachment.filename} is not a supported file type")
        if len(ids) > 0:
            await self.id(message, ids)
        else:
            await message.channel.send(content="No replay file attached")

    async def link(self, message):
        summoner_name, discord_id = msg2sum(message.content, message.author.id)
        await message.channel.send(content=self.summoner_data.link(summoner_name, str(discord_id)))

    async def unlink(self, message):
        summoner_name, discord_id = msg2sum(message.content, message.author.id)
        await message.channel.send(content=self.summoner_data.unlink(summoner_name, str(discord_id)))

    async def profile(self, message):
        matches = self.get_history(message)
        await message.channel.send(content=self.summoner_data.profile(matches))

    async def history(self, message):
        matches = self.get_history(message)
        match_history = []
        for match in matches:
            champ, result, kda, game_id, csm = match.split("|")
            replay = replay_reader.ReplayReader(game_id)
            stats = replay.get_player_stats(champ=champ)
            match_history.append(
                [champ, result, stats['keystone'], stats['subperk'], kda, stats['cs'], stats['items'], stats['gold']])
        self.image_gen.generate_player_history(match_history)
        await message.channel.send(file=File('temp.png'))
        os.remove('temp.png')

    def get_history(self, message):
        game_map = "all"
        summoner_name, discord_id = msg2sum(message.content, message.author.id)
        # Warning : The if statement below will mess up if the given summoner name ends with " sr" or " ha"
        if summoner_name[-3:].lower() == "sr" or summoner_name[-3:].lower() == "ha":
            game_map = summoner_name[-3:].lower()
            if summoner_name is not None:
                summoner_name = summoner_name[:-3]
        return self.summoner_data.history(summoner_name=summoner_name, discord_id=discord_id, mode=game_map)

    async def help(self, message):
        space_split = message.content.split(" ")
        if len(space_split) == 1:
            cmd_list = ""
            for cmd in self.commands:
                cmd_list += cmd + ", "
            await message.channel.send(content=cmd_list[:-2])
        elif len(space_split) == 2:
            for cmd in self.commands:
                if cmd.lower() == space_split[1].lower():
                    help_str = self.commands[cmd]["help"]
            await message.channel.send(content=help_str)
        else:
            await message.channel.send(content="Invalid syntax. Try rg:help {command}")

    async def handle_message(self, message):
        cmd_split = message.content.split(self.prefix)
        space_split = cmd_split[1].split(" ")
        if space_split[0] in self.commands:
            await self.commands[space_split[0]]["func"](message)
        else:
            await message.channel.send(content="Command not found")
