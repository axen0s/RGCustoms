from PIL import Image, ImageDraw, ImageFont
import json


class ImageGen:
    def __init__(self):
        with open("data/runesReforged.json", "r") as f:
            self.rune_data = json.load(f)
        self.current_image = None
        self.draw = None
        self.current_pixel = (0, 0)
        self.large_font = ImageFont.truetype("arial.ttf", 24)
        self.normal_font = ImageFont.truetype("arial.ttf", 16)

    def text(self, text, font=None, fill="white", x=60, y=30):
        if font is None:
            font = self.normal_font
        self.draw.text((self.current_pixel[0], self.current_pixel[1] + (y/3)), text, fill=fill, font=font)
        self.current_pixel = (self.current_pixel[0] + x, self.current_pixel[1])

    def resize_paste(self, img, size, center=False):
        if img is None:  # when does this happen ?
            pass
        else:
            centered_coords = (self.current_pixel[0], self.current_pixel[1] + int(size[1]/2))
            if center:
                self.current_image.paste(img.resize(size), centered_coords)
            else:
                self.current_image.paste(img.resize(size), self.current_pixel)
            self.current_pixel = (self.current_pixel[0] + size[0] + 10, self.current_pixel[1])

    def get_rune_img(self, rune_id, slot):
        for style in self.rune_data:
            for runes in style["slots"][slot]["runes"]:
                if str(runes["id"]) == str(rune_id):
                    return Image.open("img/" + runes["icon"])

    def get_style_img(self, style_id):
        for style in self.rune_data:
            if str(style["id"]) == str(style_id):
                return Image.open("img/" + style["icon"])

    def get_champ_icon(self, champ):
        return Image.open(f"img/champion/{champ}.png")

    def get_item_icon(self, item):
        if str(item) == "0":  # empty item slot, make empty item slot img to take up space
            return Image.new('RGBA', (30, 30))
        else:
            return Image.open(f"img/item/{item}.png")

    def generate_player_imgs(self, player):
        self.resize_paste(self.get_rune_img(player[0], 0), (40, 40))
        self.resize_paste(self.get_style_img(player[1]), (20, 20), center=True)
        self.resize_paste(self.get_champ_icon(player[2]), (40, 40))
        self.text(text=player[3], x=150)
        self.text(text=player[4], x=75)
        self.text(text=player[5], x=30)
        for item in player[6]:
            self.resize_paste(self.get_item_icon(item), (30, 30))
        gold_with_comma = str(player[7][0:-3]) + "," + str(player[7][-3:])
        self.text(text=gold_with_comma, x=75)
        self.current_pixel = (0, self.current_pixel[1] + 60)

    def generate_game_img(self, player_list):
        # [[winner kda, loser kda], Winners, Losers, map, timestamp]
        # in each team will be a list of players, containing [KEYSTONE_ID, PERK_SUB_STYLE, champ, name, KDA, minions_killed, [items], gold_earned]
        additional_pixels = (len(player_list[1]) + len(player_list[2])) * 65  # add another 70 pixels for each player
        self.current_image = Image.new('RGBA', (740, 100+additional_pixels))
        self.draw = ImageDraw.Draw(self.current_image)
        self.current_pixel = (0, 0)
        self.text(text=f"{player_list[3]} ({player_list[4]})")
        self.current_pixel = (0, self.current_pixel[1] + 10)
        self.text(text=f"Winners ({player_list[0][0]})", font=self.large_font, y=60)
        self.current_pixel = (0, self.current_pixel[1] + 60)
        for winner in player_list[1]:
            self.generate_player_imgs(winner)
        self.text(text=f"Losers ({player_list[0][1]})", font=self.large_font, y=60)
        self.current_pixel = (0, self.current_pixel[1] + 60)
        for loser in player_list[2]:
            self.generate_player_imgs(loser)
        self.current_image.save("temp.png")
