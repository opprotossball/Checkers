import math
from queue import LifoQueue

import numpy as np
from Moves import Moves
from board import get_neigh, on_edge
from info import GameParams, Side, side, is_man, is_up

possible_moves = Moves()


class Game:

    def __init__(self, size=8):
        if size != 8:
            raise Exception("Only board of size 8 supported now!")
        self.done = False
        self.max_moves_without_taking = 39
        self.size = size
        self.half = int(size / 2)
        self.n_tiles = 32
        self.starting_rows = 3
        self.game_state = np.zeros((int(math.pow(size, 2) / 2) + len(GameParams),))
        n_pieces = self.half * self.starting_rows
        self.game_state[:n_pieces] = -1
        self.game_state[-n_pieces - len(GameParams):] = 1
        self.game_state[-3] = -1
        self.game_state[-1] = 0
        self.game_state[-2] = Side.WHITE
        self.winner_side = 0
        self.pieces_left = {Side.WHITE: n_pieces, Side.BLACK: n_pieces}
        self.taken_history = LifoQueue()
        self.move_history = LifoQueue()
        possible_moves.update_if_needed(self.size)

        self.legal_mask = None
        self.legal_moves = None
        self.legal_updated = False
        self.takes = None

        self.__update_legal()

    def perform_move(self, move):
        if self.done or self.check_game_end():
            return False
        previous_taken = self.game_state[-1]
        previous_active = self.game_state[-3]
        move_id = possible_moves.move_id.get(move)
        if move_id is None or not self.legal_mask[move_id]:
            return False
        piece = self.game_state[move[0]]
        self.game_state[move[0]] = 0
        target = possible_moves.target(move_id)
        self.game_state[target] = piece
        enemy_tile = self.takes[move_id]
        if enemy_tile == -1:
            self.taken_history.put(None)
        else:
            self.take_piece(self.takes[move_id])
        self.game_state[-3] = target
        if not self.take_possible_for_tile(target) or enemy_tile == -1:
            self.end_turn()
            turn_ended = True
        else:
            turn_ended = False
            self.game_state[-3] = target
            self.__update_legal()
        promoted = self.promotion(target)
        self.move_history.put((move, promoted, turn_ended, previous_active, previous_taken))

    def check_game_end(self):
        if len(self.legal_moves) == 0:
            self.done = True
            self.winner_side = -self.game_state[-2]
            return True
        if self.game_state[-1] > self.max_moves_without_taking:
            self.done = True
            return True
        return False

    def check_move(self, move):
        source = move[0]
        piece = self.game_state[source]
        direction = move[1]
        length = move[2]
        my_side = side(piece)
        if is_man(piece):
            if length > 2:  # Move invalid: Move too long for man
                return False
            elif length == 1 and (my_side == 1) ^ is_up(direction):  # Move invalid: Invalid direction for man
                return False
        target = source
        enemy_tile = None
        for _ in range(length):
            target = get_neigh(self.size, target, direction)
            if target is None or side(self.game_state[target]) == my_side:  # Move invalid: Invalid target or occupied friendly piece in path
                return False
            if self.game_state[target] != 0:
                if enemy_tile is not None:  # Move invalid: More than 1 enemy in path
                    return False
                enemy_tile = target
        if self.game_state[target] != 0:  # Move invalid: Target not empty
            return False
        if is_man(piece) and length == 2 and enemy_tile is None:  # Move invalid: Man cannot jump over empty
            return False
        if self.game_state[-3] != -1 and enemy_tile is None:  # Move invalid: Cannot move after taking
            return False
        return True, enemy_tile

    def __update_legal(self):
        no_take_mask = np.zeros((possible_moves.n_moves, ), dtype=bool)
        take_mask = np.zeros((possible_moves.n_moves, ), dtype=bool)
        self.takes = np.full((possible_moves.n_moves,), -1, dtype=int)
        legal_no_take = []
        legal_take = []
        take_possible = False
        for tile in range(self.n_tiles):
            piece = self.game_state[tile]
            if side(piece) != self.game_state[-2]:
                continue
            if self.game_state[-3] != -1 and self.game_state[-3] != tile:
                continue
            for move in possible_moves.moves(tile, man=is_man(piece)):
                valid = self.check_move(move)
                if not valid:
                    continue
                take = valid[1]
                if take_possible and take is None:
                    continue
                move_id = possible_moves.move_id.get(move)
                if take is not None:
                    take_possible = True
                    take_mask[move_id] = True
                    self.takes[move_id] = take
                    legal_take.append(move)
                else:
                    legal_no_take.append(move)
                    no_take_mask[move_id] = True
        if take_possible:
            self.legal_moves = legal_take
            self.legal_mask = take_mask
        else:
            self.legal_moves = legal_no_take
            self.legal_mask = no_take_mask
        self.legal_updated = True

    def take_possible_for_tile(self, tile):
        for move in possible_moves.moves(tile, man=is_man(self.game_state[tile])):
            valid = self.check_move(move)
            if not valid:
                continue
            take = valid[1]
            if take:
                return True
        return False

    def take_piece(self, tile):
        piece_side = side(self.game_state[tile])
        if piece_side == 0:
            return False
        self.taken_history.put((tile, self.game_state[tile]))
        self.game_state[tile] = 0
        self.game_state[-1] = 0
        pieces_left = self.pieces_left[piece_side]
        pieces_left -= 1
        if pieces_left < 1:
            self.winner_side = -piece_side
            self.done = True
        self.pieces_left[piece_side] = pieces_left
        return True

    def undo_move(self):
        if self.move_history.empty():
            return
        move_data = self.move_history.get()
        move = move_data[0]
        source = move[0]
        target = source
        for _ in range(move[2]):
            target = get_neigh(self.size, target, move[1])
        self.game_state[source] = self.game_state[target]
        self.game_state[target] = 0
        taken = self.taken_history.get()
        if taken is not None:
            self.game_state[taken[0]] = taken[1]
            self.pieces_left[side(taken[1])] += 1
        if move_data[1]:  # undo promotion
            self.depromote(source)
        if move_data[2]:  # undo turn end
            self.end_turn()
        self.game_state[-3] = move_data[3]
        self.game_state[-1] = move_data[4]
        self.done = False
        self.__update_legal()

    def promotion(self, tile):
        if self.game_state[tile] == 1 and on_edge(self.size, tile, 3):
            self.game_state[tile] = 2
            return True
        elif self.game_state[tile] == -1 and on_edge(self.size, tile, 1):
            self.game_state[tile] = -2
            return True
        else:
            return False

    def depromote(self, tile):
        if self.game_state[tile] == -2:
            self.game_state[tile] = -1
        elif self.game_state[tile] == 2:
            self.game_state[tile] = 1

    def end_turn(self):
        self.game_state[-2] *= -1
        self.game_state[-3] = -1
        self.__update_legal()
        if len(self.legal_moves) == 0:
            self.winner_side = -self.game_state[-2]
            self.done = True

    def active_piece(self):
        return self.game_state[-3]

    def active_side(self):
        return self.game_state[-2]

    def last_take(self):
        return self.game_state[-1]
