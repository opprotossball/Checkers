import math
import random

import numpy as np
import pygame

import board
from Game import Game, possible_moves
from info import Direction, side, Pieces, is_man, Side


class GameMaster:
    def __init__(self):
        self.white_piece_color = (248, 248, 248)
        self.black_piece_color = (84, 84, 84)
        self.selected_color = (244, 62, 65)
        self.white_tile_color = (238, 238, 210)
        self.black_tile_color = (118, 150, 86)
        pygame.init()
        self.screen = pygame.display.set_mode([900, 900])
        self.top_left = 50, 50
        self.tile_size = 100
        self.piece_radius = 33
        self.king_radius = 15
        self.selection_thickness = 4
        self.buttons = []
        self.game = None
        self.last_clicked = None

    def init_buttons(self):
        x = self.top_left[0]
        y = self.top_left[1] - self.tile_size
        last_empty = True
        for i in range(int(math.pow(self.game.size, 2))):
            if i % self.game.size == 0:
                y += self.tile_size
                x = 50
                last_empty = not last_empty
            if last_empty:
                self.buttons.append(pygame.Rect(x, y, self.tile_size, self.tile_size))
                last_empty = False
            else:
                last_empty = True
            x += self.tile_size

    def new_game(self):
        self.game = Game()
        self.init_buttons()
        running = True
        clock = pygame.time.Clock()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.on_click()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.game.undo_move()
            self.screen.fill((255, 255, 255))
            self.draw_board()
            pygame.display.flip()
            clock.tick(40)
        pygame.quit()

    def on_click(self):
        print(np.count_nonzero(self.game.legal_mask))
        pos = pygame.mouse.get_pos()
        for i, button in enumerate(self.buttons):
            if button.collidepoint(pos):
                if self.last_clicked is not None:
                    self.perform_move(self.last_clicked, i)
                    self.reset_clicked()
                else:
                    self.last_clicked = i
                return
        self.reset_clicked()

    def get_direction_length(self, source, target):
        for direction in Direction:
            neigh = source
            length = 0
            while neigh is not None:
                neigh = board.get_neigh(self.game.size, neigh, direction)
                length += 1
                if neigh == target:
                    return direction, length
        return None

    def perform_move(self, source, target):
        params = self.get_direction_length(source, target)
        if params is None:
            print("Whatcha doin'?")
            self.reset_clicked()
            return
        self.game.perform_move((source, params[0], params[1]))

    def reset_clicked(self):
        self.last_clicked = None

    def draw_board(self):
        x = self.top_left[0]
        y = self.top_left[1] - self.tile_size
        last_empty = True
        for i in range(int(math.pow(self.game.size, 2))):
            if i % self.game.size == 0:
                y += self.tile_size
                x = 50
                last_empty = not last_empty
            if last_empty:
                color = self.selected_color if self.last_clicked == int(i / 2) else self.black_tile_color
                pygame.draw.rect(self.screen, color, pygame.Rect(x, y, self.tile_size, self.tile_size))
                piece_x = x + int(self.tile_size / 2)
                piece_y = y + int(self.tile_size / 2)
                piece = self.game.game_state[int(i / 2)]
                self.draw_piece(piece, piece_x, piece_y)
                last_empty = False
            else:
                pygame.draw.rect(self.screen, self.white_tile_color, pygame.Rect(x, y, self.tile_size, self.tile_size))
                last_empty = True
            x += self.tile_size

    def draw_piece(self, piece, x, y):
        if piece == Pieces.EMPTY:
            return 
        color = self.white_piece_color if side(piece) == Side.WHITE else self.black_piece_color
        if is_man(piece):
            pygame.draw.circle(self.screen, color, [x, y], self.piece_radius)
        else:
            pygame.draw.circle(self.screen, color, [x, y], self.piece_radius, self.king_radius)
