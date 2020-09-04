import yaml
import os
from src import replay_reader


def simplify(num):
    if num % 1 == 0:
        return int(num)
    else:
        return num


class SummonerData:
    def __init__(self):
        if os.path.exists("../data/summoner_to_id.yaml"):
            with open("../data/summoner_to_id.yaml", "r") as f:
                self.sum2id = yaml.load(f, Loader=yaml.FullLoader)
        else:
            with open("../data/summoner_to_id.yaml", "w") as f:
                self.sum2id = {}

    def link(self, summoner_name, discord_id):
        summoner_names = self.sum2id.get(discord_id, [])
        taken_summoner_names = []
        for discord_ids in self.sum2id:
            for taken_summoner_name in self.sum2id[discord_ids]:
                taken_summoner_names.append(taken_summoner_name)
        if summoner_name in summoner_names:
            return "Summoner already linked"
        elif summoner_name in taken_summoner_names:
            return "Someone else already has this summoner name"
        else:
            summoner_names.append(summoner_name)
            self.sum2id[discord_id] = summoner_names
            self.save()
            return "Summoner successfully linked"

    def unlink(self, summoner_name, discord_id):
        summoner_names = self.sum2id.get(discord_id, [])
        if summoner_name in summoner_names:
            summoner_names.remove(summoner_name)
            self.sum2id[discord_id] = summoner_names
            self.save()
            return "Summoner unlinked"
        else:
            return "Summoner was not linked"

    def log(self, replay_id):  # Summoner name (file) -> map (1 of 2 lists) -> [Champion, game result, KDA]
        replay = replay_reader.ReplayReader(replay_id)
        winners, losers = replay.results()  # Winners: [winners] Losers: [losers]
        pstats = replay.get_player_stats()  # {"NAME":"kda","champion"}
        game_map = replay.infer_map()
        for player in (winners + losers):
            kda = pstats[player]['kda']
            champion = pstats[player]['champion']
            csm = pstats[player]['csm']
            result = 'Win' if player in winners else 'Loss'
            if os.path.exists(f'data/players/{player}.yaml'):
                with open(f"data/players/{player}.yaml", "r") as f:
                    pyaml = yaml.load(f, Loader=yaml.FullLoader)
            else:
                pyaml = {}
            with open(f"data/players/{player}.yaml", "w") as f:
                yaml_map = pyaml.get(game_map, [])
                yaml_map.append(f"{champion}|{result}|{kda}|{replay_id}|{csm}")
                pyaml[game_map] = yaml_map
                yaml.dump(pyaml, f)

    def history(self, discord_id=None, summoner_name=None, mode="all"):
        names = []
        if discord_id is not None:
            for summoner_names in self.sum2id[str(discord_id)]:
                names.append(summoner_names)
        elif summoner_name is not None:
            names.append(summoner_name)
        matches = []
        for name in names:
            try:
                with open(f"data/players/{name}.yaml", "r") as f:
                    match_history = yaml.load(f, Loader=yaml.FullLoader)
            except FileNotFoundError:
                return [f"Summoner name {name} not found"]
            sr_matches = match_history.get("Summoner's Rift", [])
            ha_matches = match_history.get("Howling Abyss", [])
            if mode.lower() == "all":
                matches += sr_matches
                matches += ha_matches
            elif mode.lower() == "ha" or mode.lower().replace(" ", "") == "howlingabyss":
                matches += ha_matches
            elif mode.lower() == "sr" or mode.lower().replace(" ", "").replace("'", "") == "summonersrift":
                matches += sr_matches
        return matches

    def profile(self, matches):
        games = 0
        wins = 0
        champ_data = {}
        print(matches)
        if len(matches) == 0:
            return "No matches found on that map"
        if "Summoner name " in matches[0] and " not found" in matches[0]:
            return matches[0]
        for match in matches:
            champ, result, kda, game_id, csm = match.split("|")
            current_champ_data = champ_data.get(champ, [0, 0, 0, 0, 0, 0])  # {Champ: [W, L, K, D, A, CS/M]}
            if result == "Win":
                current_champ_data[0] += 1
                wins += 1
            elif result == "Loss":
                current_champ_data[1] += 1
            games += 1
            kills, deaths, assists = kda.split("/")
            current_champ_data[2] += int(kills)
            current_champ_data[3] += int(deaths)
            current_champ_data[4] += int(assists)
            current_champ_data[5] += float(csm)
            champ_data[champ] = current_champ_data
        profile_str = f"{wins}W {games-wins}L ({simplify(wins/games)*100}% WR)\nChamp - Winrate - KDA - CS/min\n"
        for champ in champ_data:
            total_games = champ_data[champ][0] + champ_data[champ][1]
            winrate = simplify((champ_data[champ][0] / total_games) * 100)
            average_k = simplify((champ_data[champ][2] / total_games))
            average_d = simplify((champ_data[champ][3] / total_games))
            average_a = simplify((champ_data[champ][4] / total_games))
            average_csm = simplify(round(champ_data[champ][5] / total_games, 1))
            profile_str += f"{champ} - {winrate}% - {average_k}/{average_d}/{average_a} - {average_csm}\n"
        return profile_str

    def save(self):  # Saves all yaml files
        with open("../data/summoner_to_id.yaml", "w") as f:
            yaml.dump(self.sum2id, f)