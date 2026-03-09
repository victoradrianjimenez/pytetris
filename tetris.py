import time
from random import randint
from enum import Enum
from engine import Game, Screen


class CollisionType(Enum):
    NONE = 0
    FLOOR = 1
    WALL = 2
    BRICK = 3


class Figure:

    _block_color = 255

    def __init__(self, data: list[list[int]]):
        self.height = len(data)
        self.data = list([None] * self.height)
        self.data_prev = list([None] * self.height)
        for y, row in enumerate(data):
            self.width = len(row)
            if self.width != self.height:
                raise Exception('Figure must have a square data matrix.')
            self.data[y] = [self._block_color if val else 0 for val in row]
            self.data_prev[y] = list(self.data[y])
        self.x_prev = self.y_prev = 0
        self.x = self.y = 0

    def rotate_left(self):
        self.rotate_undo()
        # rotate in buffer
        for y, row in enumerate(self.data_prev):
            for x, val in enumerate(row):
                self.data[x][self.height-1-y] = val
        
    def rotate_right(self):
        self.rotate_undo()
        # rotate in buffer
        for y, row in enumerate(self.data_prev):
            for x, val in enumerate(row):
                self.data[self.height-1-x][y] = val

    def rotate_undo(self):
        # swap lists
        aux = self.data_prev
        self.data_prev = self.data
        self.data = aux
        
    def move(self, x: int, y: int):
        self.x_prev = self.x
        self.y_prev = self.y
        self.x = x
        self.y = y

    def move_undo(self):
        self.x = self.x_prev
        self.y = self.y_prev


class Board:

    _block_color = 128

    def __init__(self, width: int, height: int):
        self.data = [list([0] * width) for _ in range(height)]
        self.width = width
        self.height = height

    def clear(self):
        for y in range(self.height):
            for x in range(self.width):
                self.data[y][x] = 0

    def set_figure(self, figure: Figure):
        for dy, row in enumerate(figure.data):
            y = figure.y + dy
            if 0 <= y < len(self.data):
                for dx, val in enumerate(row):
                    if val > 0:
                        x = figure.x + dx
                        if 0 <= x < len(self.data[y]):
                            self.data[y][x] = self._block_color

    def detect_collision(self, figure: Figure) -> CollisionType:
        for dy, row in enumerate(figure.data):
            for dx, val in enumerate(row):
                if val > 0:
                    y = figure.y + dy
                    if 0 <= y < len(self.data):
                        x = figure.x + dx
                        if 0 <= x < len(self.data[y]):
                            if self.data[y][x] > 0:
                                return CollisionType.BRICK
                        else:
                            return CollisionType.WALL
                    else:
                        return CollisionType.FLOOR
        return CollisionType.NONE

    def detect_complete_rows(self) -> dict[int]:
        counters = {}
        y = c = 0
        while y < len(self.data):
            row = self.data[y]
            # check if all blocks are present in row
            if all(val > 0 for val in row):
                # increment consecutive full rows counter
                c += 1
                # clear the row
                for x, _ in enumerate(row):
                    self.data[y][x] = 0
                # move the empty row to the end of the list
                self.data.insert(-1, self.data.pop(y))
                continue
            # if there are previous full rows
            if c > 0:
                # increment counter
                counters[c] = counters.get(c, 0) + 1
                c = 0
            # increment the loop variable
            y += 1
        # if there are previous full rows
        if c > 0:
            counters[c] = counters.get(c, 0) + 1
        # dict with the number of occurrences for 1, 2, 3, or 4 full rows
        return counters


class Tetris(Game):

    _figures = [
        (
            (1, 0, 0), 
            (1, 1, 0), 
            (0, 1, 0)),  # S
        (
            (0, 1, 0), 
            (1, 1, 0), 
            (1, 0, 0)),  # Z
        (
            (0, 1, 0, 0), 
            (0, 1, 0, 0), 
            (0, 1, 0, 0), 
            (0, 1, 0, 0)),  # I
        (
            (1, 1), 
            (1, 1)),  # O
        (
            (0, 1, 0), 
            (0, 1, 1), 
            (0, 1, 0)),  # T
        (
            (1, 0, 0), 
            (1, 0, 0), 
            (1, 1, 0)),  # L
        (
            (0, 1, 0), 
            (0, 1, 0), 
            (1, 1, 0)),  # L2
    ]

    _score_map = {
        1: 100,
        2: 300,
        3: 500,
        4: 800
    }

    _initial_time_period = 1000
    _time_period_step = 1  # gravity reduction for each complete line
    
    def __init__(self, screen: Screen):
        self._time_counter = 0
        self._time_next = 0
        self._time_period = 0
        self._score = 0
        self._lines = 0
        self._is_gaming = False
        self._screen = screen
        # set up the tetris board
        self._board = Board(10, 20)
        self.figure = None
        self.next_figure = None

    def start(self):
        # set initial values
        self._board.clear()
        self._score = 0
        self._lines = 0
        self._time_period = Tetris._initial_time_period
        self._is_gaming = True
        # set board fixed texts
        self._screen.remove_text('game_over')
        self._screen.add_text(12, 21, 'score_tag', 'Score:')
        self._screen.add_text(12, 20, 'score_val', str(self._score))
        self._screen.add_text(12, 18, 'lines_tag', 'Lines:')
        self._screen.add_text(12, 17, 'lines_val', str(self._lines))
        self._screen.add_text(12, 15, 'next_tag', 'Next:')
        # create the first figure and display
        self._generate_figure()
        self._new_figure()
        self._refresh_background()
        self._refresh_sprites()

    def loop(self):
        if self._is_gaming:
            # update the time value
            self._time_counter += 1
            # check time period
            if self._time_counter - self._time_next >= self._time_period:
                self._time_next += self._time_period
                # move the current figure
                self._move(0, -1)
                self._refresh_sprites()

    def _refresh_background(self):
        self._screen.draw_empty(layer=0)
        # draw borders
        self._screen.draw_fx(lambda x: 0 if 0 <= x <= 11 else -1, 64, layer=0)
        self._screen.draw_fy(lambda y: 0 if 0 <= y <= 21 else -1, 64, layer=0)
        self._screen.draw_fy(lambda y: 11 if 0 <= y <= 21 else -1, 64, layer=0)
        # draw board
        self._screen.draw_pixels(1, 1, self._board.data, layer=0)

    def _refresh_sprites(self):
        self._screen.draw_empty()
        # draw figure
        self._screen.draw_pixels(
            self.figure.x + 1,
            self.figure.y + 1, 
            self.figure.data)
        # draw next figure
        self._screen.draw_pixels(12, 11, self.next_figure.data)

    def _game_over(self):
        self._is_gaming = False
        self._screen.add_text(
            self._board.width // 2 - 1, 
            self._board.height // 2, 
            'game_over', 
            'GAME  OVER')

    def _generate_figure(self):
        # generate next figure
        self.next_figure = Figure(Tetris._figures[randint(0, len(Tetris._figures)-1)])
        # random rotation
        for _ in range(randint(0, 3)):
            self.next_figure.rotate_left()

    def _new_figure(self):
        # random figure
        self.figure = self.next_figure
        self._generate_figure()
        # fixed position
        self.figure.move(
            (self._board.width - self.figure.width) // 2,
            self._board.height - self.figure.height + 1)
        # check if the figure collides with any brick
        collision_type = self._board.detect_collision(self.figure)
        if collision_type == CollisionType.BRICK:
            self._on_collision()
            self._game_over()

    def _on_collision(self):
        # freezes figure
        self._board.set_figure(self.figure)
        # detect full rows
        lines_count = self._board.detect_complete_rows()
        # calculate new score
        lines = sum(p * n for p, n in lines_count.items())
        self._lines += lines
        self._score += sum((Tetris._score_map.get(p, 0) * n for p, n in lines_count.items()))
        # update speed
        self._time_period = max(Tetris._initial_time_period - self._lines * Tetris._time_period_step, 1)
        # refresh
        if lines > 0:
            # score label
            self._screen.edit_text('score_val', str(self._score))
            self._screen.edit_text('lines_val', str(self._lines))
        self._refresh_background()

    def _rotate(self, direction: int):
        if direction > 0:
            self.figure.rotate_right()
        else:
            self.figure.rotate_left()
        collision_type = self._board.detect_collision(self.figure)
        if collision_type != CollisionType.NONE:
            self.figure.rotate_undo()

    def _move(self, dx: int, dy: int):
        self.figure.move(self.figure.x + dx, self.figure.y + dy)
        collision_type = self._board.detect_collision(self.figure)
        if collision_type != CollisionType.NONE:
            self.figure.move_undo()
            if dy != 0:
                self._on_collision()
                self._new_figure()

    def input_callback(self, key: str):
        # react to keyboard events only if the game is active
        if self._is_gaming:
            # call function for every key pressed
            callback = dict(
                down=lambda: self._move(0, -1),
                right=lambda: self._move(1, 0),
                left=lambda: self._move(-1, 0),
                a=lambda: self._rotate(-1),
                z=lambda: self._rotate(1)).get(key)
            if callback is not None:
                callback()
                self._refresh_sprites()

        elif key in ('a', 'z'):
            self.start()
