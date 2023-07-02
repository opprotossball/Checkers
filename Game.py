import math
from queue import Queue, LifoQueue

import numpy as np

import info
from PossibleMoves import PossibleMoves
from board import get_neigh, on_edge
from info import GameParams, Pieces, Side, MoveParams, side, is_man, is_up, Edge

possible_moves = PossibleMoves()


class Game:

    def __init__(self, size=8):
        self.done = False
        self.max_moves_without_taking = 39
        self.size = size
        self.half = int(size / 2)
        self.starting_rows = 3
        if size % 2 == 1:
            raise Exception("Odd board sizes not supported!")
        self.game_state = np.zeros((int(math.pow(size, 2) / 2) + len(GameParams),))
        n_pieces = self.half * self.starting_rows
        self.game_state[:n_pieces] = Pieces.B_MAN
        self.game_state[-n_pieces - len(GameParams):] = Pieces.W_MAN
        self.game_state[GameParams.ACTIVE_PIECE] = -1
        self.game_state[GameParams.LAST_TAKE] = 0
        self.game_state[GameParams.ACTIVE_SIDE] = Side.WHITE
        self.winner_side = 0
        self.pieces_left = {Side.WHITE: n_pieces, Side.BLACK: n_pieces}
        self.taken_history = LifoQueue()
        self.move_history = LifoQueue()
        self.take_possibility = False
        possible_moves.update_if_needed(self.size)

    def perform_move(self, move, debug=False, testing_moves=False):
        if self.done:
            if debug:
                print("Move invalid: Game ended!")
            return False
        source = move[MoveParams.FROM]
        if self.game_state[GameParams.ACTIVE_PIECE] not in (-1, source):
            if debug:
                print("Move invalid! Another piece has to move!")
            return False
        piece = self.game_state[source]
        if info.side(piece) != self.game_state[GameParams.ACTIVE_SIDE]:
            if debug:
                print("Move invalid: Side inactive!")
            return False
        direction = move[MoveParams.DIRECTION]
        length = move[MoveParams.LENGTH]
        my_side = side(piece)
        target = source
        enemy_tile = None
        previous_taken = self.game_state[GameParams.LAST_TAKE]
        for _ in range(length):
            target = get_neigh(self.size, target, direction)
            if target is None or side(self.game_state[target]) == my_side:
                if debug:
                    print("Move invalid: Invalid target or occupied friendly piece in path!")
                return False
            if self.game_state[target] != Pieces.EMPTY:
                if enemy_tile is not None:
                    if debug:
                        print("Move invalid: More than 1 enemy in path!")
                    return False
                enemy_tile = target
        if self.game_state[target] != Pieces.EMPTY:
            if debug:
                print("Move invalid: Target not empty!")
            return False
        if is_man(piece):
            if length > 2:
                if debug:
                    print("Move invalid: Move too long for man!")
                return False
            elif length == 2 and enemy_tile is None:
                if debug:
                    print("Move invalid: Man cannot jump over empty!")
                return False
            elif length == 1 and (my_side == Side.WHITE) ^ is_up(direction):
                if debug:
                    print("Move invalid: Invalid direction for man!")
                return False
        if enemy_tile is not None:
            self.take_piece(enemy_tile, testing_moves)
        else:
            if self.take_possible():
                if debug:
                    print("Move invalid: Taking is compulsory!")
                return False
            self.taken_history.put(None)
            self.game_state[GameParams.LAST_TAKE] += 1
        previous_active = self.game_state[GameParams.ACTIVE_PIECE]
        self.game_state[GameParams.ACTIVE_PIECE] = target
        self.game_state[target] = piece
        self.game_state[source] = Pieces.EMPTY
        promoted = self.promotion(target)
        turn_ended = False
        if not self.take_possible_for_tile(target) or enemy_tile is None:
            self.end_turn()
            turn_ended = True
        self.move_history.put((move, promoted, turn_ended, previous_active, previous_taken))
        if self.game_state[GameParams.LAST_TAKE] >= self.max_moves_without_taking:
            self.done = True
        return True

    def test_if_takes(self, move):
        source = move[MoveParams.FROM]
        piece = self.game_state[source]
        direction = move[MoveParams.DIRECTION]
        length = move[MoveParams.LENGTH]
        my_side = side(piece)
        target = source
        enemy_tile = None
        for _ in range(length):
            target = get_neigh(self.size, target, direction)
            if target is None or side(self.game_state[target]) == my_side:
                return False
            if self.game_state[target] != Pieces.EMPTY:
                if enemy_tile is not None:
                    return False
                enemy_tile = target
        if self.game_state[target] != Pieces.EMPTY:
            return False
        if is_man(piece):
            if length > 2:
                return False
        if enemy_tile is not None:
            return True
        return False

    def take_piece(self, tile, testing_takes=False):
        piece_side = side(self.game_state[tile])
        if piece_side == 0:
            return False
        self.taken_history.put((tile, self.game_state[tile]))
        self.game_state[tile] = Pieces.EMPTY
        if not testing_takes:
            self.game_state[GameParams.LAST_TAKE] = 0
            pieces_left = self.pieces_left[piece_side]
            pieces_left -= 1
            if pieces_left < 1:
                self.winner_side = -piece_side
                self.done = True
                # print(f"{Side(self.winner_side).name} WON!")
            self.pieces_left[piece_side] = pieces_left
        return True

    def undo_move(self):
        if self.move_history.empty():
            return
        move_data = self.move_history.get()
        move = move_data[0]
        source = move[MoveParams.FROM]
        target = source
        for _ in range(move[MoveParams.LENGTH]):
            target = get_neigh(self.size, target, move[MoveParams.DIRECTION])
        self.game_state[source] = self.game_state[target]
        self.game_state[target] = Pieces.EMPTY
        taken = self.taken_history.get()
        if taken is not None:
            self.game_state[taken[0]] = taken[1]
            self.pieces_left[side(taken[1])] += 1
        if move_data[1]:  # undo promotion
            self.depromote(source)
        if move_data[2]:  # undo turn end
            self.end_turn()
        self.game_state[GameParams.ACTIVE_PIECE] = move_data[3]
        self.game_state[GameParams.LAST_TAKE] = move_data[4]
        self.done = False

    def promotion(self, tile):
        if self.game_state[tile] == Pieces.W_MAN and on_edge(self.size, tile, Edge.TOP_EDGE):
            self.game_state[tile] = Pieces.W_KING
            return True
        elif self.game_state[tile] == Pieces.B_MAN and on_edge(self.size, tile, Edge.BOTTOM_EDGE):
            self.game_state[tile] = Pieces.B_KING
            return True
        else:
            return False

    def depromote(self, tile):
        if self.game_state[tile] == Pieces.B_KING:
            self.game_state[tile] = Pieces.B_MAN
        elif self.game_state[tile] == Pieces.W_KING:
            self.game_state[tile] = Pieces.W_MAN

    def end_turn(self):
        self.game_state[GameParams.ACTIVE_SIDE] *= -1
        self.game_state[GameParams.ACTIVE_PIECE] = -1

    def take_possible_for_tile(self, tile):
        if side(self.game_state[tile]) != self.game_state[GameParams.ACTIVE_SIDE]:
            return False
        for move in possible_moves.moves(tile):
            if self.test_if_takes(move):
                return True
        return False

    def take_possible(self):
        for tile in range(len(self.game_state) - len(GameParams)):
            if self.take_possible_for_tile(tile):
                return True
        return False

    def legal_moves_mask(self):
        mask = np.zeros((possible_moves.n_moves, ), dtype=bool)
        for i, move in enumerate(possible_moves):
            valid = self.perform_move(move, testing_moves=True)
            mask[i] = valid
            if valid:
                self.undo_move()
        return mask
