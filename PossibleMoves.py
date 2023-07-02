import math
import info
import board


class PossibleMoves:

    def __init__(self):
        self.size = -1
        self.possible_moves = []
        self.n_moves = -1

    def update_if_needed(self, size):
        if self.size == size:
            return
        self.size = size
        n_tiles = int(math.pow(size, 2) / 2)
        for tile in range(n_tiles):
            self.possible_moves.append([])
            for direction in info.Direction:
                neigh = tile
                length = 0
                while True:
                    neigh = board.get_neigh(size, neigh, direction)
                    length += 1
                    if neigh is None:
                        break
                    else:
                        self.possible_moves[tile].append((tile, direction, length))
        self.n_moves = sum(len(t) for t in self.possible_moves)

    def moves(self, tile):
        return self.possible_moves[tile]

    def move(self, move_id):
        i = 0
        while move_id >= len(self.possible_moves[i]):
            move_id -= len(self.possible_moves[i])
            i += 1
        return self.possible_moves[i][move_id]

    def __iter__(self):
        for t in self.possible_moves:
            for m in t:
                yield m
