from enum import IntEnum


class Pieces(IntEnum):
    B_KING = -2,
    B_MAN = -1,
    EMPTY = 0,
    W_MAN = 1,
    W_KING = 2


class Direction(IntEnum):
    UP_LEFT = 0,
    UP_RIGHT = 1,
    DOWN_LEFT = 2,
    DOWN_RIGHT = 3


class Edge(IntEnum):
    LEFT_EDGE = 0,
    BOTTOM_EDGE = 1,
    RIGHT_EDGE = 2,
    TOP_EDGE = 3


class Side(IntEnum):
    BLACK = -1,
    WHITE = 1


class MoveParams(IntEnum):
    FROM = 0,
    DIRECTION = 1,
    LENGTH = 2,


class GameParams(IntEnum):
    ACTIVE_PIECE = -3
    ACTIVE_SIDE = -2
    LAST_TAKE = -1


def opposed_direction(direction):
    return abs(direction - 3)


def is_up(direction):
    return direction == Direction.UP_LEFT or direction == Direction.UP_RIGHT


def is_left(direction):
    return direction == Direction.UP_LEFT or direction == Direction.DOWN_LEFT


def is_man(piece):
    return piece == Pieces.B_MAN or piece == Pieces.W_MAN


def side(piece):
    return 0 if piece == Pieces.EMPTY else 1 - 2 * int(piece < 0)
