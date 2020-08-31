import replay_reader
import discord


class RGCustoms(discord.Client):
    async def on_ready(self):
        print(f"Logged in as {self.user}, ID {self.user.id}")

    async def on_message(self, message):
        replay_id = None
        print(message.content)
        if message.author == self.user:
            return
        if message.content.startswith(f'<@!{self.user.id}>') or message.content.startswith('<@&749896640613056533'):
            space_split = message.content.split(" ")
            if space_split[1] == "id":
                replay_id = space_split[2]
                print(f"Detected replay ID command, ID {replay_id}")
            if space_split[1] == "test_embed":
                test_embed_data = {"title": "Test Embed", "type": "rich", "description": "Description",
                                   "fields": [{"name": "Field 1", "value": "Value of field1"}]}
                test_embed = discord.Embed.from_dict(test_embed_data)
                await message.channel.send(embed=test_embed)  # this doesnt work at all Lol
        attach = message.attachments  # Returns a list of attachments
        if len(attach) > 0:
            first_attachment = attach[0]
            if first_attachment.filename.endswith('.rofl'):
                print("Replay file detected")
                await first_attachment.save(f"replays/{first_attachment.filename}")
                print("Replay file saved")

                replay_id = first_attachment.filename[:-5]
        if replay_id:
            print(f"Bot will attempt to read replay {replay_id}")
            replay = replay_reader.ReplayReader(replay_id)
            winners, losers = replay.results()
            player_stats = replay.get_player_stats()
            embed_data = {"title": f"Game {replay_id}", "description": f"Map: {replay.map}", "fields": []}
            winner_embed_field = {"name": "Winning Team", "value": ""}
            for winner in winners:
                winner_embed_field["value"] += f"{winner} ({player_stats[winner]['champion']}) {player_stats[winner]['kda']}\n"
            embed_data["fields"].append(winner_embed_field)
            loser_embed_field = {"name": "Losing Team", "value": ""}
            for loser in losers:
                loser_embed_field["value"] += f"{loser} ({player_stats[loser]['champion']}) {player_stats[loser]['kda']}\n"
            embed_data["fields"].append(loser_embed_field)
            await message.channel.send(embed=discord.Embed.from_dict(embed_data))
