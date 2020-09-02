import json
import os
import time


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
        self.game_time = self.infer_game_time()  # (Seconds)
        self.game_time_str = time.strftime("%M:%S", time.gmtime(self.game_time))
        actual_filename = filename.split("/")[-1]
        self.match_id = actual_filename.split("-")[-1][0:-5]

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

    def infer_game_time(
            self):  # How long the game lasted is also not given, so we check how long the players were there
        record_time_played = 0
        for player_stats in self.stats:
            if int(player_stats["TIME_PLAYED"]) > record_time_played:
                record_time_played = int(player_stats["TIME_PLAYED"])
        return record_time_played

    def results(self):  # Returns a list of winners & losers
        winners = []
        losers = []
        for player_stats in self.stats:
            if player_stats["WIN"] == "Win":
                winners.append(player_stats["NAME"])
            elif player_stats["WIN"] == "Fail":
                losers.append(player_stats["NAME"])
        return winners, losers

    def get_player_stats(self):
        players_dict = {}
        for players in self.stats:
            players_dict[players["NAME"]] = {}
            players_dict[players["NAME"]][
                "kda"] = f"{players['CHAMPIONS_KILLED']}/{players['NUM_DEATHS']}/{players['ASSISTS']}"
            players_dict[players["NAME"]]["champion"] = players["SKIN"]
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
