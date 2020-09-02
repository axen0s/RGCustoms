import replay_reader
from discord import Embed


class BotFunctions:
    async def id(self, message=None, ids=None):  # Get match from ID
        if ids is None:
            ids = message.content[6:].split(',')
        for replay_id in ids:
            print(f"Bot will attempt to read replay {replay_id}")
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

    async def handle_message(self, message):
        commands = {"id": self.id, "replay": self.replay}
        print(message.content)
        cmd_split = message.content.split("rg:")
        space_split = cmd_split[1].split(" ")
        if space_split[0] in commands:
            await commands[space_split[0]](message)
        else:
            await message.channel.send(content="Command not found")
