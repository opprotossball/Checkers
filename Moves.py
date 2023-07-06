import math
import info
import board


class Moves:

    def __init__(self):
        self.size = -1
        self.man_moves = []
        self.all_moves = []
        self.n_moves = -1
        self.move_id = {}
        self.id_move = {}
        self.targets = []

    def update_if_needed(self, size):
        if self.size == size:
            return
        self.size = size
        n_tiles = int(math.pow(size, 2) / 2)
        i = 0
        for tile in range(n_tiles):
            self.man_moves.append([])
            self.all_moves.append([])
            for direction in info.Direction:
                neigh = tile
                length = 0
                while True:
                    neigh = board.get_neigh(size, neigh, direction)
                    length += 1
                    if neigh is None:
                        break
                    move = (tile, direction, length)
                    if length <= 2:
                        self.man_moves[-1].append(move)
                    self.all_moves[-1].append(move)
                    self.move_id[move] = i
                    self.id_move[i] = move
                    self.targets.append(neigh)
                    i += 1
        self.n_moves = i

    def moves(self, tile, man=False):
        return self.man_moves[tile] if man else self.all_moves[tile]

    def move(self, move_id):
        return self.id_move.get(move_id)

    def target(self, move_id):
        return self.targets[move_id]

    def move_id(self, move):
        return self.move_id.get(move)

    def __iter__(self):
        for tile in self.all_moves:
            for move in tile:
                yield move
