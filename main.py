import sys
from engine import Engine, Screen
from tetris import Tetris


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 engine.py game.")
        exit(1)

    game_class = None
    if sys.argv[1] == 'tetris': 
        game_class = Tetris
    
    if game_class is None:
        print("Game not implemented.")
        exit(1)

    screen = Screen(16, 25)
    engine = Engine(screen)
    engine.start(game_class(screen))
