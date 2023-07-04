import math
import info
import board


class PossibleMoves:

    def __init__(self):
        self.size = -1
        self.possible_moves = []
        self.targets = []
        self.n_moves = -1
        self.moves_dict = {}

    def update_if_needed(self, size):
        if self.size == size:
            return
        self.size = size
        n_tiles = int(math.pow(size, 2) / 2)
        i = 0
        for tile in range(n_tiles):
            for direction in info.Direction:
                neigh = tile
                length = 0
                while True:
                    neigh = board.get_neigh(size, neigh, direction)
                    length += 1
                    if neigh is None:
                        break
                    else:
                        self.possible_moves.append((tile, direction, length))
                        self.targets.append(neigh)
                        self.moves_dict[(tile, direction, length)] = i
                        i += 1
        self.n_moves = len(self.possible_moves)

    def moves(self, tile):
        return self.possible_moves[tile]

    def move(self, move_id):
        return self.possible_moves[self.move_id(move_id)]

    def target(self, move_id):
        return self.targets[move_id]

    def move_id(self, move):
        return self.moves_dict.get(move)

    def __iter__(self):
        for m in self.possible_moves:
            yield m
