import replay_reader
import summoner_data
from discord import Embed
import os


class BotFunctions:
    def __init__(self):
        self.summoner_data = summoner_data.SummonerData()

    async def log(self, message=None, ids=None):
        if ids is None:
            ids = message.content[7:].split(",")
        for replay_id in ids:
            if os.path.exists("data/logged.txt"):
                with open("data/logged.txt", "r") as f:
                    logged_ids = f.readlines()
                    if replay_id + '\n' in logged_ids:
                        await message.channel.send(content=f"Match {replay_id} was previously logged")  # The match has already been logged.
            self.summoner_data.log(replay_id)
            if not os.path.exists("data/logged.txt"):
                with open("data/logged.txt", "w") as f:
                    f.write(f"{replay_id}\n")
            else:
                with open("data/logged.txt", "a") as f:
                    f.write(f"{replay_id}\n")
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
            winners, losers = replay.results()
            player_stats = replay.get_player_stats()
            embed_data = {"title": f"Game {replay_id}", "description": f"{replay.map}\n {replay.game_time_str}",
                          "fields": []}
            winning_kda, losing_kda = replay.get_team_kdas()
            winner_embed_field = {"name": f"Winning Team ({winning_kda})", "value": ""}
            for winner in winners:
                winner_embed_field[
                    "value"] += f"{winner} ({player_stats[winner]['champion']}) {player_stats[winner]['kda']}\n"
            embed_data["fields"].append(winner_embed_field)
            loser_embed_field = {"name": f"Losing Team ({losing_kda})", "value": ""}
            for loser in losers:
                loser_embed_field[
                    "value"] += f"{loser} ({player_stats[loser]['champion']}) {player_stats[loser]['kda']}\n"
            embed_data["fields"].append(loser_embed_field)
            await message.channel.send(embed=Embed.from_dict(embed_data))  # apparently theres no way to send multiple embeds in 1
            await self.log(message=message, ids=ids)

    async def replay(self, message):  # Submit new replay
        attachments = message.attachments
        if len(attachments) > 0:
            ids = []
            for attachment in attachments:
                if attachment.filename.endswith('.rofl') or attachment.filename.endswith('.json'):
                    await attachment.save(f"replays/{attachment.filename}")
                    await message.channel.send(content=f"Replay {attachment.filename[:-5]} saved")
                    ids.append(attachment.filename[:-5])
            if len(ids) > 0:
                await self.id(message, ids)
            else:
                await message.channel.send(content="No replay file attached")
        else:
            await message.channel.send(content="No replay file attached")

    async def link(self, message):
        space_split = message.content.split(" ")
        if space_split[1].startswith('<@!') and space_split[1].endswith('>'):
            summoner_name = " ".join(space_split[2:])
            discord_id = space_split[1][3:-1]
        else:
            summoner_name = " ".join(space_split[1:])
            discord_id = message.author.id
        await message.channel.send(content=self.summoner_data.link(summoner_name, str(discord_id)))

    async def unlink(self, message):
        space_split = message.content.split(" ")
        if space_split[1].startswith('<@!') and space_split[1].endswith('>'):
            summoner_name = " ".join(space_split[2:])
            discord_id = space_split[1][3:-1]
        else:
            summoner_name = " ".join(space_split[1:])
            discord_id = message.author.id
        await message.channel.send(content=self.summoner_data.unlink(summoner_name, str(discord_id)))

    async def profile(self, message):
        matches = self.get_history(message)
        await message.channel.send(content=self.summoner_data.profile(matches))

    async def history(self, message):
        matches = self.get_history(message)
        pretty_matches = []
        for match in matches:
            champ, result, kda, game_id = match.split("|")
            pretty_matches.append(f"{champ} {result} {kda} ({game_id})")
        await message.channel.send(content="\n".join(pretty_matches))

    def get_history(self, message):
        space_split = message.content.split(" ")
        summoner_name = None
        discord_id = None
        game_map = "all"
        if len(space_split) == 1 or (len(space_split) == 2 and (space_split[1].lower() == "ha" or space_split[1].lower() == "sr")):
            discord_id = message.author.id
        elif space_split[1].startswith('<@!') and space_split[1].endswith('>'):
            discord_id = space_split[1][3:-1]
        else:
            summoner_name = " ".join(space_split[1:])
        # Warning : The if statement below will mess up if the given summoner name ends with " sr" or " ha"
        if space_split[-1].lower() == "sr" or space_split[-1].lower() == "ha":
            game_map = space_split[-1].lower()
            if summoner_name is not None:
                summoner_name = summoner_name[:-3]
        return self.summoner_data.history(summoner_name=summoner_name, discord_id=discord_id, mode=game_map)

    async def handle_message(self, message):
        commands = {"id": {"func": self.id, "help": "rg:id {ID} - Gets info of match ID"},
                    "replay": {"func": self.replay, "help": "rg:help - Attach a .ROFL or .json extracted from one for the bot to record"},
                    "link": {"func": self.link, "help": "rg:link {Summoner Name} - Links a summoner name to your Discord. Mention someone before the summoner name to link it to their Discord instead"},
                    "unlink": {"func": self.unlink, "help": "rg:unlink {Summoner Name} - Opposite of rg:link"},
                    "profile": {"func": self.profile, "help": "rg:profile {Summoner Name or @} {ha or sr, leave blank for all} - Get player's stats"},
                    "history": {"func": self.history, "help": "rg:history {Summoner Name or @} {ha or sr, leave blank for all} - Get recent matches"}}
        print(message.content)
        cmd_split = message.content.split("rg:")
        space_split = cmd_split[1].split(" ")
        if space_split[0].lower() == "help":
            help_str = ""
            for cmd in commands:
                help_str += commands[cmd]["help"] + "\n"
            await message.channel.send(content=help_str)
        elif space_split[0] in commands:
            await commands[space_split[0]]["func"](message)
        else:
            await message.channel.send(content="Command not found")
