from math import log2

import pygame as pg
import pyautogui
import numpy as np

from board import Board, Move
from state_testing import StateTesting


BOARD_W_PX = 640
BOARD_H_PX = 640
OFFSET = 10
BOARD_SIZE_W = 4
BOARD_SIZE_H = 4
TILE_W_PX = (BOARD_W_PX - (BOARD_SIZE_W + 1) * OFFSET) / BOARD_SIZE_W
TILE_H_PX = (BOARD_H_PX - (BOARD_SIZE_H + 1) * OFFSET) / BOARD_SIZE_H
FONTSIZE = int(min(TILE_H_PX - 2 * OFFSET, TILE_W_PX / 4 + 5 * OFFSET))
FONTCOLOR = pg.Color(255, 255, 255)
BGCOLOR = pg.Color(100, 100, 100)
LOAD_READY = False
EMPEROR_RULES = False

ind1, ind2 = np.meshgrid(
    np.arange(OFFSET, BOARD_W_PX, TILE_W_PX + OFFSET),
    np.arange(OFFSET, BOARD_H_PX, TILE_H_PX + OFFSET),
    sparse=True
)
COORDS_X = ind1[0]
COORDS_Y = ind2

COLOR_MAP = {
    v: pg.Color(255, 13 + int(log2(v) - 1) * 22, 0, 0)
    if v > 0 else pg.Color(127, 127, 127, 0)
    for v in Board.ALLOWED_VALUES
}


def draw_tile(scr: pg.Surface, x: float, y: float, value: int = 0) -> None:
    if EMPEROR_RULES and value not in Board.ALLOWED_VALUES:
        raise ValueError(f'Value {value} is not allowed')
    rect = pg.Rect(x, y, TILE_W_PX, TILE_H_PX)
    pg.draw.rect(
        surface=scr,
        color=COLOR_MAP.get(value, pg.Color(255, 255, 0, 0)),
        rect=rect
    )
    font = pg.font.Font(None, FONTSIZE)
    text = font.render(f'{value}', True, FONTCOLOR)
    place = text.get_rect(center=(rect.center))
    scr.blit(text, place)


def draw_board(
    screen: pg.Surface,
    board: Board
) -> None:
    for j, y in enumerate(COORDS_Y):
        for i, x in enumerate(COORDS_X):
            draw_tile(
                scr=screen,
                x=x, y=y[0],
                value=board.state[j, i]
            )


def main() -> None:
    board = Board(
        size=(BOARD_SIZE_H, BOARD_SIZE_W),
        fill_tiles=2,
        fill_vals=[2, 4],
        p=[0.9, 0.1],
        merge_2048=EMPEROR_RULES
    )

    # 2fill, values, simpletest, mergebug, movebug, ezwin
    if LOAD_READY:
        board = StateTesting.load_board('values')
        board._emperor_rules = EMPEROR_RULES
    else:
        board.create()

    pg.init()
    screen = pg.display.set_mode((BOARD_W_PX, BOARD_H_PX), pg.SRCALPHA)
    done = False
    pause = False
    clock = pg.time.Clock()
    frames = 60

    screen.fill(BGCOLOR)
    move: Move | None = None
    winlose_flag = False
    while not done:
        if board.win:
            print(
                f'You win in {board.turn} turns'
                f' with the score of {board.score}!'
            )
            pyautogui.alert(  # type: ignore[attr-defined]
                f'You win in {board.turn} turns'
                f' with the score of {board.score}!',
                'Victory!'
            )
            winlose_flag = True
        elif board.lose:
            print(
                f'You lost in {board.turn} turns'
                f' with the score of {board.score}!'
            )
            pyautogui.alert(  # type: ignore[attr-defined]
                f'You lost in {board.turn} turns'
                f' with the score of {board.score}!',
                'Fail!'
            )
            winlose_flag = True
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
                break
            pressed = pg.key.get_pressed()
            if pressed[pg.K_ESCAPE]:
                pause = not pause
            if not pause:
                if pressed[pg.K_SPACE] or winlose_flag:
                    winlose_flag = False
                    if LOAD_READY:
                        board = StateTesting.load_board('ezwin')
                        board._emperor_rules = EMPEROR_RULES
                    else:
                        board.create()
                if pressed[pg.K_UP]:
                    move = Move.UP
                elif pressed[pg.K_RIGHT]:
                    move = Move.RIGHT
                elif pressed[pg.K_DOWN]:
                    move = Move.DOWN
                elif pressed[pg.K_LEFT]:
                    move = Move.LEFT
        if not pause and not winlose_flag:
            screen.fill(BGCOLOR)
            if move:
                board.tick(move)
            draw_board(screen, board)
        else:
            pause_rect = pg.Rect(0, 0, BOARD_W_PX, BOARD_H_PX)
            # pg.draw.rect(screen, pg.Color(127, 127, 127, 127), pause_rect)
            pause_scr = pg.Surface((BOARD_W_PX, BOARD_H_PX), pg.SRCALPHA)
            pg.draw.rect(pause_scr, pg.Color(127, 127, 127, 8), pause_rect)
            font = pg.font.Font(None, FONTSIZE)
            text = font.render('PAUSE', True, FONTCOLOR)
            place = text.get_rect(center=(pause_rect.center))
            # pause_scr.set_alpha(127)
            pause_scr.blit(text, place)
            screen.blit(pause_scr, (0, 0))
        move = None
        pg.display.flip()
        clock.tick(frames)


if __name__ == '__main__':
    main()
