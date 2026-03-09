from abc import ABC, abstractmethod
from typing import Callable
import threading
import click
from time import time_ns, sleep

class Screen:

    _color_map = {
        0: u" ",
        1: u"\u2591",
        2: u"\u2592",
        3: u"\u2593",
        4: u"\u2588"
    }

    def __init__(self, width: int, height: int, char_width: int = 2):
        # size of the screen
        self._width = width
        self._height = height
        # pixel width
        self._char_width = char_width
        # buffer for text labels
        self._labels = dict()
        # buffer for background and sprites layers
        self._data_background = [[0] * width for _ in range(height)]
        self._data_sprites = [[0] * width for _ in range(height)]
        self._data_buffer = [[0] * width for _ in range(height)]

    def draw_empty(self, layer: int = 1):
        # select background or sprite layer
        data = self._data_sprites if layer > 0 else self._data_background
        # set black pixels
        for y, row in enumerate(data):
            for x, _ in enumerate(row):
                data[y][x] = 0

    def draw_pixels(self, pos_x: int, pos_y: int, sprite: list[list[int]], layer: int = 1):
        # select background or sprite layer
        data = self._data_sprites if layer > 0 else self._data_background
        # for each pixel of the sprite
        for y, row in enumerate(sprite):
            # calculate the absolute position based on the relative position
            ny = pos_y + y
            if 0 <= ny < self._height:
                for x, val in enumerate(row):
                    nx = pos_x + x
                    if 0 <= nx < self._width and val > 0:
                        data[ny][nx] = val

    def draw_fx(self, fx: Callable, colour: int, layer: int = 1):
        # select background or sprite layer
        data = self._data_sprites if layer > 0 else self._data_background
        # for each x position
        for x in range(self._width):
            # calculate the y position using the fx function
            y = int(fx(x))
            # set the pixel
            if 0 <= y < self._height:
                data[y][x] = colour

    def draw_fy(self, fy: Callable, colour: int, layer: int = 1):
        # select background or sprite layer
        data = self._data_sprites if layer > 0 else self._data_background
        # for each y position
        for y in range(self._height):
            # calculate the x position using the fy function
            x = int(fy(y))
            # set the pixel
            if 0 <= x < self._width:
                data[y][x] = colour

    def draw_fxy(self, fxy: Callable, colour: int, layer: int = 1):
        # select background or sprite layer
        data = self._data_sprites if layer > 0 else self._data_background
        # for each pixel
        for x in range(self._width):
            for y in range(self._height):
                # call function and draw the pixel if the result is true
                if fxy(x, y):
                    data[y][x] = colour

    def add_text(self, pos_x: int, pos_y: int, key: str, text: str):
        # set: x, y, text
        self._labels[key] = [pos_x * self._char_width, self._height - pos_y - 1, text]

    def edit_text(self, key: str, text: str):
        if key in self._labels:
            self._labels[key][-1] = text

    def remove_text(self, key: str):
        if key in self._labels:
            self._labels.pop(key)

    def _render_line(self, y: int, arr: list[int]) -> str:
        # generate a string with gray block characters
        s = u"".join([Screen._color_map.get((x+1) // 64, Screen._color_map[0]) * self._char_width 
            for x in arr])
        # add text on the line
        for lx, ly, text in self._labels.values():
            if ly == y:
                s = s[:lx] + text + s[lx+len(text):]
        # truncate the string
        return s[:len(arr) * self._char_width]

    def render(self):
        # clear
        print("\033[2J\033[1;1H", end='') # clc
        # combine background and sprites
        for x in range(self._width):
            for y in range(self._height):
                self._data_buffer[y][x] = max(self._data_background[y][x], self._data_sprites[y][x])
        # draw pixels (characters)
        print(u"\r\n".join(self._render_line(y, arr) 
            for y, arr in enumerate(reversed(self._data_buffer))), end='')


class Game(ABC):
    @abstractmethod
    def __init__(self, screen: Screen):
        self._screen = screen
    
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def loop(self):
        pass

    @abstractmethod
    def input_callback(self, key: str):
        pass


class Engine:

    _key_map = {
        '\x1b[A': 'up',
        '\x1b[B': 'down',
        '\x1b[C': 'right',
        '\x1b[D': 'left'
    }

    _logic_period_ns = 1000000  # game timer period = 1 millisecond
    
    def __init__(self, screen: Screen):
        # screen instance
        self._screen = screen
        # running flag
        self._running_event = threading.Event()
        # initialize the keyboard handler
        self._thread = threading.Thread(target=self._input_thread)
        # game instance
        self._game = None

    def start(self, game: Game):
        # if the engine is already started, return
        if self._running_event.is_set():
            return
        
        # start the game
        self._running_event.set()
        self._thread.start()
        self._game = game
        self._game.start()

        # run the game loop
        timer_ts = time_ns()
        while self._running_event.is_set():
            # calculate the time for the next iteration
            ts = time_ns()
            if ts - timer_ts < Engine._logic_period_ns:
                # sleep until the next step
                sleep((Engine._logic_period_ns - ts + timer_ts) / 1000000000)
            
            # update the timer value
            timer_ts += Engine._logic_period_ns
            # process game logic
            self._game.loop()
            # refresh the screen
            self._screen.render()
            continue

        # stop the engine
        print('Press any key to finalize...')
        self._thread.join()

    def _input_thread(self):
        while self._running_event.is_set():
            c = click.getchar()
            key = self._key_map.get(c, c)
            if key == 'x':
                self._running_event.clear()
            # send the key event to the game
            if self._game is not None:
                self._game.input_callback(key)
                # refresh the screen
                self._screen.render()

    def stop(self):
        self._running_event.clear()

