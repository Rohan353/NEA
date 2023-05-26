import os
import math
import json
import pygame
from pygame.locals import (
    RLEACCEL,
    K_UP,
    K_DOWN,
    K_LEFT,
    K_RIGHT,
    K_ESCAPE,
    KEYDOWN,
    KEYUP,
    K_0,
    K_9,
    K_SPACE,
    K_RETURN,
    QUIT,
    MOUSEBUTTONUP
)
from pygame.math import Vector2
from terrain import Terrain
from utils import *
import time


class Spacecraft(pygame.sprite.Sprite):
    '''Controls spacecraft'''

    def __init__(self, craft_folder: str, sound_folder: str, start_velocity: tuple = (0, 0.05), pos=(200, 50)):

        super().__init__()

        self.craft_folder = craft_folder
        self.sound_folder = sound_folder

        self.craft_name = ""

        self.start_velocity = start_velocity
        self.start_pos = pos

        self.velocity_vector = Vector2(start_velocity)
        self.thrust_vector = Vector2()
        self.acceleration_vector = Vector2()
        self.gravity_vector = Vector2(0, 0.0004)

        # define spacecraft constants
        self.thrust = 0
        self.change_angle = 0
        self.fuel = 0
        self.fuel_rate = 0

        # animation variables
        self.is_flickering = False
        self.current_sprite = 0
        self.engine = False

        # initial setup
        self.angle = 0
        self.craft_name = "eagle"  # set starter spacecraft
        self.set_craft(self.craft_name)

        pygame.mixer.music.load(self.sound_folder + "\\engine_sound.wav")
        pygame.mixer.music.play(-1)
        pygame.mixer.music.pause()

    def reset_pos(self):

        self.velocity_vector = Vector2(self.start_velocity)
        self.angle = 0
        self.fuel = self.total_fuel
        self.already_landed = []
        self.score = 0

        self.pos = Vector2(self.start_pos)

    def set_craft(self, craft_name, pos=(200, 50)):
        '''Loads spacecraft from folder'''
        # global craft_img_folder
        # global craft_data_folder

        self.craft_name = craft_name
        self.craft_data_path = os.path.join(craft_data_folder, self.craft_name)

        with open(self.craft_data_path+r'\{}.json'.format(craft_name), 'r') as f:
            data = json.load(f)

            self.change_angle = float(data['turn_rate'])
            self.thrust = float(data["thrust"])
            self.resize = data["resize"]
            self.fuel = data["fuel"]
            self.total_fuel = data["fuel"]
            self.fuel_rate = data["fuel_rate"]
            self.pad_height = data["pad_height"]

            self.craft_base = pygame.image.load(
                self.craft_data_path + '\\' + data["craft"])
            self.craft_base = resize_image(
                self.craft_base, self.resize)

            self.craft_base.set_colorkey((255, 255, 255))

            self.warm = []  # for throttling up or down
            self.flicker = []  # for constant power flicker

        for image in data["warm_up"]:
            self.warm.append(
                resize_image(
                    pygame.image.load(self.craft_data_path +
                                      '\\' + image), self.resize)
            )

        for image in data["flicker"]:
            self.flicker.append(
                resize_image(pygame.image.load(
                    self.craft_data_path + '\\' + image), self.resize)
            )

        self.craft = self.craft_base
        self.image = self.craft
        self.rect = self.image.get_rect()
        self.pos = Vector2(pos)

    def get_craft(self) -> str:
        '''Returns currently loaded craft'''
        return self.craft

    def control(self, key):
        "handle player input"

        self.thrust_vector = Vector2(0, 0)  # reset thrust vector each loop
        self.engine = False  # flag for animation

        if key[K_UP]:

            if self.fuel >= 0:

                horizontal_acc = - \
                    (math.sin(math.radians(self.angle))*self.thrust)
                vertical_acc = - \
                    (math.cos(math.radians(self.angle))*self.thrust)

                self.thrust_vector = Vector2(horizontal_acc,
                                             vertical_acc)
                self.engine = True

                self.fuel += -self.fuel_rate

        if key[K_LEFT]:
            self.angle += self.change_angle

        if key[K_RIGHT]:
            self.angle += -self.change_angle

        return self.velocity_vector, int(self.fuel), self.pos[1]

    def update(self):
        "update sprite location"

        self.rot_update()

        self.pos += self.velocity_vector
        self.acceleration_vector = self.gravity_vector + self.thrust_vector
        self.velocity_vector += self.acceleration_vector
        self.rect.center = self.pos  # air resistance

        self.animate_engine()

    def rot_update(self):
        "rotate the sprite about it's center, updates image attribute to currently selected craft"
        self.image = pygame.transform.rotozoom(self.craft, self.angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

        if self.angle >= 360:
            self.angle = 0

        if self.angle < 0:
            self.angle = 360

    def animate_engine(self):
        "animates engine if engine variable is true"
        if self.engine == True:

            pygame.mixer.music.unpause()

            if self.is_flickering == True:
                if self.current_sprite >= len(self.flicker):
                    self.current_sprite = 0

                self.craft = self.flicker[int(self.current_sprite)]
                self.current_sprite += 0.1

            elif self.is_flickering == False:

                if self.current_sprite >= len(self.warm):
                    self.current_sprite = 0
                    self.is_flickering = True

                else:
                    self.craft = self.warm[int(self.current_sprite)]
                    self.current_sprite += 0.2

        else:
            self.current_sprite = 0
            self.is_flickering = False
            self.craft = self.craft_base

            pygame.mixer.music.pause()

    def get_image_size(self):
        return self.rect.width, self.rect.height

    def collision_detection(self):

        mask = pygame.mask.from_surface(self.image)
        center = self.rect.topleft

        outline = [(p[0] + center[0], p[1] + center[1])
                   for p in mask.outline(every=5)]

        lowest_coord = [0, 0]

        for coord in outline:
            if coord[1] > lowest_coord[1]:
                lowest_coord = coord

        terrain_y = int(terrain.get_terrain_y(
            lowest_coord[0], game_state.screen_l_x))

        # pygame.draw.lines(screen, (255, 0, 255), False, outline, 5)
        # pygame.draw.line(screen, (255, 0, 255), [0, lowest_coord[1]], [
        #   1000, lowest_coord[1]], 2)
        # pygame.draw.line(screen, (255, 0, 255), [0, terrain_y], [
        # 1000, terrain_y], 2)

        if lowest_coord[1] >= terrain_y:
            pad = terrain.get_pad_number(
                lowest_coord[0], game_state.screen_l_x)
            if pad == False:
                # crashed
                print("crashed")
                game_state.state = "crashed"

            if pad != False:

                if self.velocity_vector[1] < 100000:
                    coords = terrain.pad_position(
                        pad, game_state.screen_l_x)

                    self.pos = Vector2(
                        coords[0], coords[1] - spacecraft.pad_height)
                    self.velocity_vector = Vector2(0, 0)
                    self.angle = 0

                    if pad not in self.already_landed:
                        self.already_landed.append(pad)
                        self.fuel += 100
                        self.score += 10

                else:
                    game_state.state = "crashed"


class User:

    def __init__(self, user_folder):

        self.user_folder = user_folder

        self.username = "guest"
        self.highScore = 0
        self.totalScore = 0
        self.credits = 0
        self.crafts = ["eagle"]

    def load(self, username):

        path = self.user_folder + f"\\{username}" + ".json"

        spacecraft.set_craft("eagle")

        if username == "guest":
            self.__init__(self.user_folder)

            return f"                         Guest Player Loaded"

        if os.path.isfile(path):  # if player with username exists

            with open(path, 'r') as f:
                data = json.load(f)

                self.username = data["username"]
                self.highScore = data["highScore"]
                self.totalScore = data["totalScore"]
                self.credits = data["credits"]
                self.crafts = data["crafts"]

            return f"                    Player {username} found, data loaded"

        else:

            self.username = username
            self.highScore = 0
            self.totalScore = 0
            self.credits = 0
            self.crafts = ["eagle"]

            data = {
                "username": username,
                "highScore": 0,
                "totalScore": 0,
                "credits": 0,
                "crafts": ["eagle"]
            }
            with open(path, "w+") as f:
                json.dump(data, f)

            return f"Existing player was not found - Created new player {username}"

    def save(self):

        if self.username != "guest":
            path = self.user_folder + f"\\{self.username}" + ".json"

            data = {
                "username": self.username,
                "highScore": self.highScore,
                "totalScore": self.totalScore,
                "credits": self.credits,
                "crafts": self.crafts
            }

            with open(path, 'w') as f:

                json.dump(data, f)

    def get_stats(self):

        str_crafts = ''
        for craft in self.crafts:
            str_crafts = str_crafts + craft + ' '

        stats = [
            f"Username : {self.username}",
            f"High Score : {self.highScore}",
            f"Total Score : {self.totalScore}",
            f"Credits Available: {self.credits}",
            f"Crafts : {str_crafts}"
        ]

        return stats


class Menu:
    '''Manages main menu, pause menu'''

    def __init__(self, button_path, spacecraft_path, surface):

        self.path = button_path
        self.spacecraft_path = spacecraft_path
        self.surf = surface

        self.play = Button(200, 150, self.path +
                           "\\play.png", self.path + "\\play_hover.png", 0.5)
        self.quit_game = Button(400, 450, self.path +
                                "\\quit.png", self.path + "\\quit_hover.png", 0.5)
        self.shop = Button(600, 150, self.path+"\\shop.png",
                           self.path+"\\shop_hover.png", 0.5)
        self.stats = Button(200, 300, self.path +
                            "\\stats.png", self.path+"\\stats_hover.png", 0.5)
        self.login = Button(600, 300, self.path +
                            "\\login.png", self.path+"\\login_hover.png", 0.5)

        self.login_input = InputBox(375, 200, 140, 32)

        self.resume = Button(400, 100, self.path +
                             "\\resume.png", self.path + "\\resume_hover.png", 0.5)
        self.quit_to_menu = Button(
            400, 500, self.path + "\\menu.png", self.path + "\\menu_hover.png", 0.5)

        self.help_b = Button(700, 600, self.path + "\\help.png",
                             self.path + "\\help_hover.png", 0.5)

        self.ready_to_click = True

        self.login_output_text = ""

        # shop buttons

        self.eagle_icon = Button(
            200, 100, self.spacecraft_path + "\\eagle\\eagle.png", self.spacecraft_path + "\\eagle\\eagle_thrust2.png", 3)

        self.defiant_icon = Button(
            510, 80, self.spacecraft_path + "\\defiant\\defiant.png", self.spacecraft_path + "\\defiant\\defiant_warming2.png", 0.3)

    def pause(self):

        self.resume.draw(self.surf)
        self.quit_to_menu.draw(self.surf)

        if self.ready_to_click:

            if self.resume.clicked == True:
                self.ready_to_click = False
                game_state.state = "main_game"

            if self.quit_to_menu.clicked:
                self.ready_to_click = False
                game_state.state = 'base_menu'

    def base_menu(self):

        info_text1 = f"Current Player: {user.username}"
        info_text2 = f"Money Available: {user.credits} credits"
        title_text = f"Welcome to Lunar Lander, by Rohan"

        info1 = font.render(info_text1, True, (255, 255, 255))
        info2 = font.render(info_text2, True, (255, 255, 255))
        title = title_font.render(title_text, True, (255, 255, 255))

        screen.blit(info1, [600, 240])
        screen.blit(info2, [600, 260])
        screen.blit(title, [200, 20])

        self.play.draw(self.surf)
        self.quit_game.draw(self.surf)
        self.shop.draw(self.surf)
        self.stats.draw(self.surf)
        self.login.draw(self.surf)
        self.help_b.draw(self.surf)

        if self.ready_to_click:

            if self.play.clicked:
                self.ready_to_click = False
                game_state.state = "main_game"
                game_state.seed = terrain.set_seed()
                game_state.screen_l_x = 0

                spacecraft.reset_pos()

            if self.quit_game.clicked:
                self.ready_to_click = False
                game_state.state = "QUIT"

            if self.login.clicked:
                self.ready_to_click = False
                game_state.state = "login_menu"

            if self.stats.clicked:
                self.ready_to_click = False
                self.user_stats = user.get_stats()
                game_state.state = "stats_menu"

            if self.shop.clicked:
                self.ready_to_click = False
                game_state.state = "shop_menu"

            if self.help_b.clicked:
                self.ready_to_click = False
                game_state.state = "help_menu"

    def login_menu(self):
        text = False

        output = font.render(self.login_output_text, True, (255, 255, 255))
        self.quit_to_menu.draw(self.surf)

        for event in events:
            text = self.login_input.handle_event(event)

        if text:  # when enter has been pressed

            # validation

            valid = True
            error = ""

            if len(text) > 10:
                valid = False
                error += "Username is too long - maximum allowed is 10 characters"

            if any(c in special_chars for c in text):
                valid = False
                error += "  Special characters are not allowed"

            if any(c == " " for c in text):
                valid = False
                error += "  Spaces are not allowed"

            if valid:

                self.login_output_text = user.load(text)
            else:
                self.login_output_text = f"Input Invalid : {error}"

        if self.quit_to_menu.clicked == True:
            self.ready_to_click = False
            game_state.state = "base_menu"

        screen.blit(output, [250, 300])
        self.login_input.update()
        self.login_input.draw(self.surf)

    def stats_menu(self):

        x = 250
        y = 100

        self.quit_to_menu.draw(self.surf)

        for stat in self.user_stats:
            output = font.render(stat, True, (255, 255, 255))
            screen.blit(output, [x, y])

            y += 30

        if self.quit_to_menu.clicked == True:
            self.ready_to_click = False
            game_state.state = "base_menu"

    def help_menu(self):
        self.quit_to_menu.draw(self.surf)

        x = 250
        y = 100

        for line in helpText:
            output = font.render(line, True, (255, 255, 255))
            screen.blit(output, [x, y])
            y += 40

        if self.quit_to_menu.clicked == True:
            self.ready_to_click = False
            game_state.state = "base_menu"

    def crash_menu(self):

        self.quit_to_menu.draw(self.surf)

        text = f"You crashed, your total score was {spacecraft.score}"
        text_display = font.render(text, True, (255, 255, 255))

        screen.blit(text_display, [395, 400])

        if self.quit_to_menu.clicked == True:
            self.ready_to_click = False
            game_state.state = "base_menu"

    def shop_menu(self):

        self.quit_to_menu.draw(self.surf)
        self.eagle_icon.draw(self.surf)
        self.defiant_icon.draw(self.surf)

        money_text = f"Credits Available : {user.credits}"
        money_display = font.render(money_text, True, (255, 255, 255))

        for craft in craft_list:
            outputText = ''

            craftname = craft[0]

            if craftname == spacecraft.craft_name:
                outputText = "Active"
            elif craftname in user.crafts:
                outputText = "Ready to use"

            else:
                outputText = f"Cost : {craft[1]} Credits"

            output = font.render(outputText, True, (255, 255, 255))
            screen.blit(output, craft[2])

        screen.blit(money_display, [395, 400])

        if self.eagle_icon.clicked == True:
            self.purchase_or_equip("eagle")

        if self.defiant_icon.clicked == True:
            self.purchase_or_equip("defiant")

        if self.quit_to_menu.clicked == True:
            self.ready_to_click = False
            game_state.state = "base_menu"

    def purchase_or_equip(self, craftname):

        if craftname in user.crafts:
            spacecraft.set_craft(craftname)

        else:

            price = get_price(craft_list, craftname)
            if user.credits >= price:

                user.crafts.append(craftname)
                user.credits += -price

        user.save()

    def set_ready_to_click(self):
        self.ready_to_click = True


def game_readout(data, seed, numChunks, coord):

    vertical_speed = int(data[0][1]*100)
    if vertical_speed >= 0:
        vertical_text = f"{abs(vertical_speed)} v"
    else:
        vertical_text = f"{abs(vertical_speed)} ^"

    horizontal_speed = int(data[0][0]*100)
    if horizontal_speed >= 0:
        horizontal_text = f"{abs(horizontal_speed)} -->"
    else:
        horizontal_text = f"{abs(horizontal_speed)} <--"

    vertical_readout = font.render(
        vertical_text, True, (255, 255, 255))

    horizontal_redout = font.render(
        horizontal_text, True, (255, 255, 255))

    fuel = font.render(
        f"Fuel {int(data[1])}", True, (255, 255, 255)
    )

    alt = font.render(
        f"Altitude {int(data[2])}", True, (255, 255, 255)
    )

    # dev tools

    seed = font.render(
        f"Seed {seed}", True, (255, 255, 255)
    )

    chunks = font.render(
        f"Chunks Loaded {numChunks}", True, (255, 255, 255)
    )

    x_cord = font.render(
        f"Screen X coord {int(round(coord,-1))}", True, (255, 255, 255)
    )

    score = font.render(
        f"Score {int(spacecraft.score)}", True, (255, 255, 255)
    )

    screen.blit(vertical_readout, [20, 20])
    screen.blit(horizontal_redout, [20, 50])
    screen.blit(alt, [20, 80])
    screen.blit(fuel, [20, 110])
    screen.blit(score, [20, 140])

    if dev_tools:
        screen.blit(seed, [20, 140])
        screen.blit(chunks, [20, 170])
        screen.blit(x_cord, [20, 200])


class GameState():
    '''Controls what part of game is run (menu/running game)'''

    def __init__(self):
        self.state = "base_menu"
        self.dev_tool_last_pressed = 0
        self.screen_l_x = 0

        self.counter = 1

    def login_menu(self):
        menu.login_menu()

    def base_menu(self):

        menu.base_menu()

    def pause_menu(self):

        menu.pause()

    def stats_menu(self):

        menu.stats_menu()

    def shop_menu(self):

        menu.shop_menu()

    def help_menu(self):

        menu.help_menu()

    def crashed(self):

        menu.crash_menu()

    def main_game(self):
        global all_sprites
        global font
        global dev_tools

        key = pygame.key.get_pressed()

        now = time.time()

        if dev_tools:

            if key[K_SPACE]:
                self.seed = terrain.set_seed()

        if key[K_0]:
            if now - self.dev_tool_last_pressed > 0.01:

                dev_tools = not dev_tools

            self.dev_tool_last_pressed = now

        if key[K_ESCAPE]:
            self.state = "pause_menu"

        spacecraft_data = spacecraft.control(key)

        if spacecraft.pos[0] <= 200:
            self.screen_l_x += spacecraft.velocity_vector[0]
            spacecraft.pos = Vector2(200, spacecraft.pos[1])

        elif spacecraft.pos[0] >= 1000-200:
            self.screen_l_x += spacecraft.velocity_vector[0]
            spacecraft.pos = Vector2(1000-200, spacecraft.pos[1])

        game_readout(spacecraft_data, self.seed, len(
            terrain.chunkList), self.screen_l_x)

        # collision detection

        if self.counter % 3 == 0:
            spacecraft.collision_detection()

        self.counter += 1
        if self.counter == 100:
            self.counter == 0

        spacecraft.update()
        terrain.update(self.screen_l_x)

        all_sprites.draw(screen)
        terrain.draw_chunks(screen, self.screen_l_x)

    def get_state(self) -> str:
        return self.state

    def state_manager(self):
        global events

        events = pygame.event.get()

        for event in events:

            if event.type == QUIT:
                self.state = 'QUIT'

            if event.type == MOUSEBUTTONUP:
                menu.set_ready_to_click()

        if self.state == 'base_menu':
            self.base_menu()

        elif self.state == 'main_game':
            self.main_game()

        elif self.state == 'pause_menu':
            self.pause_menu()

        elif self.state == "login_menu":
            self.login_menu()

        elif self.state == "stats_menu":
            self.stats_menu()

        elif self.state == "shop_menu":
            self.shop_menu()

        elif self.state == "help_menu":
            self.help_menu()

        elif self.state == "crashed":
            self.crashed()


# folders

craft_data_folder = os.path.join('data', 'spacecraft')
map_data_folder = os.path.join("data", "maps")
button_data_folder = os.path.join("data", "buttons")
sound_data_folder = os.path.join("data", "sounds")
user_data_folder = os.path.join("data", "users")

# general setup
pygame.init()
pygame.mixer.init()
clock = pygame.time.Clock()
game_state = GameState()

# game screen setup
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Lunar Lander")


# instance creation

spacecraft = Spacecraft(craft_data_folder, sound_data_folder)
terrain = Terrain(map_data_folder)
menu = Menu(button_data_folder, craft_data_folder, screen)
user = User(user_data_folder)
font = pygame.font.Font(None, 25)
title_font = pygame.font.Font(None, 50)


# pygame sprite management

all_sprites = pygame.sprite.Group()
all_sprites.add(spacecraft)

global dev_tools
global craft_list
dev_tools = False

craft_list = [["eagle", 100, [200, 200]], ["defiant", 10, [500, 200]]]
helpText = ["Welcome to Lunar Lander", "A game developed by Rohan", "Use A and D to rotate",
            "W to thrust", "Land on pads to get refueled and earn points", "Try not to crash!"]


special_chars = "!@#$%^&*()-+?_=,<>/'\""


# game loop
running = True

while running:
    screen.fill((0, 0, 0))

    game_state.state_manager()

    if game_state.get_state() == 'QUIT':
        running = False

    clock.tick(200)
    pygame.display.flip()

pygame.quit()
