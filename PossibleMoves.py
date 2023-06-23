import math
import info
import board


class PossibleMoves:

    def __init__(self):
        self.size = -1
        self.possible_moves = []

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

    def moves(self, tile):
        return self.possible_moves[tile]
