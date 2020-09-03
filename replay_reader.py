import json
import os
import time
import image_gen


class ReplayReader:
    def __init__(self, replay_id):
        if not os.path.exists('replays'):
            os.mkdir('replays')
        if os.path.exists(f'replays/{replay_id}.json'):
            filename = f"replays/{replay_id}.json"
        else:
            filename = f"replays/{replay_id}.rofl"
        if filename.endswith('.rofl'):
            with open(filename, 'r', encoding="utf8", errors="ignore") as f:
                read_data = f.read()
                start_json = read_data.find(r'{"gameLength"')
                read_data = read_data[start_json:]
                end_json = read_data.find(r'\"}]"}')
                read_data = read_data[:(end_json + 6)]
            with open(f"{filename[0:-5]}.json", "w") as f:
                json_from_rofl = json.loads(read_data)
                new_json_str = json.dumps(json_from_rofl, indent=2)
                f.write(new_json_str)
            os.remove(filename)  # Rofl files take up a lot of space. Convert them to their JSON and delete them
            filename = filename[0:-5] + ".json"
        with open(filename) as json_file:
            self.json = json.load(json_file)
        self.stats = json.loads(self.json['statsJson'])
        self.map = self.infer_map()
        self.game_time = (self.json['gameLength'] / 1000)  # (Milliseconds -> Seconds)
        self.game_time_str = time.strftime("%M:%S", time.gmtime(self.game_time))
        self.match_id = replay_id
        self.image_gen = image_gen.ImageGen()

    def infer_map(self):  # The map is not given to us, so we must infer.
        sr_trinkets = [3340, 3364, 3363, 3513]
        sr_stats = ["BARON_KILLS", "DRAGON_KILLS", "WARD_PLACED",
                    "NEUTRAL_MINIONS_KILLED"]  # If any of these stats are above 0, it is guaranteed to be Summoner's Rift.
        poro_snax = 2052
        is_aram = True
        for player_stats in self.stats:
            for sr_stat in sr_stats:
                if int(player_stats[sr_stat]) > 0:
                    is_aram = False
            for trinket in sr_trinkets:  # Check trinket to find wards (SR) or Poro-Snax (HA)
                if int(player_stats["ITEM6"]) == trinket:
                    is_aram = False
                elif int(player_stats["ITEM6"]) == poro_snax:
                    is_aram = True
        if is_aram:
            return "Howling Abyss"
        elif not is_aram:  # Sadly Twisted Treeline no longer exists
            return "Summoner's Rift"

    def results(self):  # Returns a list of winners & losers
        winners = []
        losers = []
        for player_stats in self.stats:
            if player_stats["WIN"] == "Win":
                winners.append(player_stats["NAME"])
            elif player_stats["WIN"] == "Fail":
                losers.append(player_stats["NAME"])
        return winners, losers

    def get_player_stats(self, summoner_name=None, champ=None):
        if summoner_name is None and champ is None:
            players_dict = {}
            for players in self.stats:
                players_dict[players["NAME"]] = {}
                players_dict[players["NAME"]][
                    "kda"] = f"{players['CHAMPIONS_KILLED']}/{players['NUM_DEATHS']}/{players['ASSISTS']}"
                players_dict[players["NAME"]]["champion"] = players["SKIN"]
                players_dict[players["NAME"]]["csm"] = int(players["MINIONS_KILLED"]) / (self.game_time/60)
                players_dict[players["NAME"]]["cs"] = players["MINIONS_KILLED"]
            return players_dict
        else:
            players_dict = {}
            for players in self.stats:
                items = []
                for i in range(6):
                    items.append(players[f"ITEM{i}"])
                if players["NAME"] == summoner_name:
                    players_dict["kda"] = f"{players['CHAMPIONS_KILLED']}/{players['NUM_DEATHS']}/{players['ASSISTS']}"
                    players_dict["champion"] = players["SKIN"]
                    players_dict["csm"] = int(players["MINIONS_KILLED"]) / (self.game_time/60)
                    players_dict["cs"] = players["MINIONS_KILLED"]
                elif players["SKIN"] == champ:
                    players_dict["kda"] = f"{players['CHAMPIONS_KILLED']}/{players['NUM_DEATHS']}/{players['ASSISTS']}"
                    players_dict["champion"] = players["SKIN"]
                    # players_dict["csm"] = int(players["MINIONS_KILLED"]) / (self.game_time/60)
                    players_dict["cs"] = players["MINIONS_KILLED"]
                    players_dict["keystone"] = players["KEYSTONE_ID"]
                    players_dict["subperk"] = players["PERK_SUB_STYLE"]
                    players_dict["gold"] = players["GOLD_EARNED"]
                    players_dict["items"] = items
            return players_dict

    def get_team_kdas(self):
        winner_kda = [0, 0, 0]
        loser_kda = [0, 0, 0]
        for player_stats in self.stats:
            if player_stats["WIN"] == "Win":
                kda = winner_kda
            elif player_stats["WIN"] == "Fail":
                kda = loser_kda
            kda[0] += int(player_stats["CHAMPIONS_KILLED"])
            kda[1] += int(player_stats["NUM_DEATHS"])
            kda[2] += int(player_stats["ASSISTS"])
        return f"{winner_kda[0]}/{winner_kda[1]}/{winner_kda[2]}", f"{loser_kda[0]}/{loser_kda[1]}/{loser_kda[2]}"

    def generate_game_img(self):
        winners = []  # [KEYSTONE_ID, PERK_SUB_STYLE, champ, name, KDA, [items]]
        losers = []
        for pstats in self.stats:
            if pstats["WIN"] == "Fail":
                list_to_mod = losers
            elif pstats["WIN"] == "Win":
                list_to_mod = winners
            items = []
            for i in range(6):
                items.append(pstats[f"ITEM{i}"])
            kda = f"{pstats['CHAMPIONS_KILLED']}/{pstats['NUM_DEATHS']}/{pstats['ASSISTS']}"
            list_to_mod.append([pstats["KEYSTONE_ID"], pstats["PERK_SUB_STYLE"], pstats["SKIN"], pstats["NAME"], kda, pstats["MINIONS_KILLED"], items, pstats["GOLD_EARNED"]])
        win_kda, lose_kda = self.get_team_kdas()
        self.image_gen.generate_game_img([[win_kda, lose_kda], winners, losers, self.map, self.game_time_str])
