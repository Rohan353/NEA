import matplotlib.pyplot as plt
import noise
import random
import pygame
import json
import os


class Terrain():

    def __init__(self, path):

        self.preChunk = []
        self.midChunk = []
        self.postChunk = []

        self.map_path = path

        self.set_map("moon")

    def set_map(self, new_map, seed=None):
        "loads map from json file"

        self.map = new_map
        self.chunkList = []

        map_path = self.map_path + "\\" + self.map
        with open(map_path+f"\\{self.map}.json", 'r') as f:
            data = json.load(f)

            self.octaves = data["octaves"]
            self.frequency = data["frequency"]
            self.exp = data["exp"]
            self.spacing = data["spacing"]
            self.offset = data["offset"]
            self.mult = data["mult"]

        self.set_seed(seed)

    def get_map(self) -> str:
        "returns current map name"
        return self.map

    def set_seed(self, seed=None):
        "sets map seed value (random if empty)"

        if seed == None:
            self.seed = random.randint(1, 1000000)
        else:
            self.seed = seed

        self.chunkList = []
        self.pads = []

        return self.seed

    def get_perlin(self, x) -> float:
        "returns perlin noise for x value"

        value = noise.pnoise1(x*self.frequency, self.octaves)
        y = (abs(value*self.mult)**self.exp)
        if value < 0:
            y = -y

        return y

    def gen_chunk(self, startx: int, endx: int) -> list:

        chunk = []  # list of (x,y) tuples

        y = 400

        remaining = 0

        startx, endx, = int(startx), int(endx)

        for i in range(startx, endx, self.spacing):

            straight = random.randint(1, 50)

            if remaining > 0:
                remaining += - 1

            elif straight == 1 and i > startx+50 and i < endx - 50:
                remaining = 5
                self.pads.append([i, i+self.spacing*5, y])

            else:
                y = int(self.get_perlin(i+self.seed))
                y += self.offset

                remaining = 0

            chunk.append((i, y))

        return chunk

    def get_pad_number(self, x, screen_l_x):

        x += screen_l_x
        pad_number = False

        x = int(x)

        for index, pad in enumerate(self.pads):
            if x in range(pad[0], pad[1]+1):
                pad_number = index
                break

        return pad_number

    def pad_position(self, pad_number, screen_l_x):

        pad = self.pads[pad_number]

        x = (pad[1]+pad[0])/2
        y = pad[2]

        return [int(x - screen_l_x), int(y)]

    def plot_chunk(self, chunk):
        "plots chunk using pyplot and prints raw values"
        x_list = [i[0] for i in chunk]
        y_list = [i[1] for i in chunk]

        print(chunk)

        plt.plot(x_list, y_list)
        plt.show()

    def display(self, surface, chunk):
        "displays chunk on screen"

        rect = pygame.draw.lines(surface, (255, 255, 255), False, chunk, 2)
        # use rect to check for collisions

    def update(self, screen_l_x):
        "manages what chunk to load and generate based on screen x coordinate"

        middle_chunk_pos = round(screen_l_x, -3)  # nearest chunk start

        self.preChunk = []
        self.midChunk = []
        self.postChunk = []

        for chunk in self.chunkList:

            if chunk[0][0] == middle_chunk_pos-1000:
                self.preChunk = chunk

            elif chunk[0][0] == middle_chunk_pos:
                self.midChunk = chunk

            elif chunk[0][0] == middle_chunk_pos+1000:
                self.postChunk = chunk

        if self.preChunk == []:
            self.preChunk = self.gen_chunk(
                middle_chunk_pos-1000, middle_chunk_pos+self.spacing)
            self.chunkList.append(self.preChunk)

        if self.midChunk == []:
            self.midChunk = self.gen_chunk(
                middle_chunk_pos, middle_chunk_pos+1000+self.spacing)
            self.chunkList.append(self.midChunk)

        if self.postChunk == []:
            self.postChunk = self.gen_chunk(
                middle_chunk_pos+1000, middle_chunk_pos+2000+self.spacing)
            self.chunkList.append(self.postChunk)

    def convert_chunks(self, screen_l_x):
        screen_l_x = int(screen_l_x)
        preChunk = [(i[0] - screen_l_x, i[1]) for i in self.preChunk]
        midChunk = [(i[0] - screen_l_x, i[1]) for i in self.midChunk]
        postChunk = [(i[0] - screen_l_x, i[1]) for i in self.postChunk]

        return preChunk, midChunk, postChunk

    def draw_chunks(self, surface, screen_l_x):
        "draw chunks on screen"

        preChunk, midChunk, postChunk = self.convert_chunks(screen_l_x)

        self.display(surface, preChunk)
        self.display(surface, midChunk)
        self.display(surface, postChunk)

    def get_terrain_y(self, x, screen_l_x):

        preChunk, midChunk, postChunk = self.convert_chunks(screen_l_x)

        y = 0

        # print(midChunk[0][0], midChunk[100][0], x)

        if x in range(int(preChunk[0][0]), int(preChunk[100][0])+1):
            y = self.interpolate_y(x, preChunk)

        if x in range(int(midChunk[0][0]), int(midChunk[100][0])+1):
            y = self.interpolate_y(x, midChunk)

        if x in range(int(postChunk[0][0]), int(postChunk[100][0])+1):
            y = self.interpolate_y(x, postChunk)

        return y

    def interpolate_y(self, x, chunk):
        x = int(x)
        for index, coord in enumerate(chunk):
            if chunk[index][0] <= x and chunk[index+1][0] >= x:
                sx = int(chunk[index][0])
                sy = int(chunk[index][1])
                ex = int(chunk[index+1][0])
                ey = int(chunk[index+1][1])
                y = sy + ((x-sx)/(ex-sx)) * (ey-sy)
                return y


# display chunk
if __name__ == "__main__":
    map_data_folder = os.path.join("data", "maps")

    t = Terrain(map_data_folder)
    t.set_seed(9007195)

    x = 0

    chunk = t.gen_chunk(x, x+1000)
    t.plot_chunk(chunk)
