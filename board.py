import math

from info import Edge, Direction

edges_to_check = [
    [Edge.TOP_EDGE, Edge.LEFT_EDGE],
    [Edge.TOP_EDGE, Edge.RIGHT_EDGE],
    [Edge.BOTTOM_EDGE, Edge.LEFT_EDGE],
    [Edge.BOTTOM_EDGE, Edge.RIGHT_EDGE]
]


def on_edge(size, tile, edge):
    half = int(size / 2)
    match edge:
        case Edge.LEFT_EDGE:
            return tile % size == half
        case Edge.BOTTOM_EDGE:
            return tile >= (math.pow(size, 2) - size) / 2
        case Edge.RIGHT_EDGE:
            return tile % size == half - 1
        case Edge.TOP_EDGE:
            return tile < half
        case _:
            raise Exception("Wrong edge given!")
    
    
def get_neigh(size, tile, direction):
    half = int(size / 2)
    for edge in edges_to_check[direction]:
        if on_edge(size, tile, edge):
            return None
    odd_row = int(tile % size >= half)
    match direction:
        case Direction.UP_LEFT:
            return tile - half - odd_row
        case Direction.UP_RIGHT:
            return tile - half + 1 - odd_row
        case Direction.DOWN_LEFT:
            return tile + half - odd_row
        case Direction.DOWN_RIGHT:
            return tile + half + 1 - odd_row
        case _:
            raise Exception("Wrong direction given!")
