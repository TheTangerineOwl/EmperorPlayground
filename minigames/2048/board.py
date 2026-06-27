from enum import Enum
import numpy as np


class Move(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    RIGHT = (1, 0)
    LEFT = (-1, 0)


class Transform:

    _MAP = {
        (Move.LEFT, Move.DOWN): lambda arr: np.flipud(arr).T,
        (Move.LEFT, Move.RIGHT): lambda arr: np.fliplr(arr),
        (Move.LEFT, Move.UP): lambda arr: np.rot90(arr),
        (Move.UP, Move.LEFT): lambda arr: np.flipud(arr).T,
        (Move.UP, Move.DOWN): lambda arr: np.flipud(arr),
        (Move.UP, Move.RIGHT): lambda arr: np.rot90(arr),
        (Move.RIGHT, Move.DOWN): lambda arr: np.flipud(arr).T,
        (Move.RIGHT, Move.LEFT): lambda arr: np.fliplr(arr),
        (Move.RIGHT, Move.UP): lambda arr: np.rot90(arr),
        (Move.DOWN, Move.RIGHT): lambda arr: np.flipud(arr).T,
        (Move.DOWN, Move.UP): lambda arr: np.flipud(arr),
        (Move.DOWN, Move.LEFT): lambda arr: np.rot90(arr)
    }

    @staticmethod
    def make(
        arr: np.ndarray,
        fr: Move = Move.LEFT,
        to: Move = Move.LEFT
    ) -> np.ndarray:
        pair = (fr, to)
        return Transform._MAP.get(pair, lambda arr: arr)(arr)


class Board:
    ALLOWED_VALUES = [0, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048]

    def __init__(
        self,
        size: tuple[int, int] = (4, 4),
        fill_tiles: int = 2,
        fill_vals: list[int] = [2, 4],
        p: list[float] = [0.9, 0.1],
        merge_2048: bool = True
    ):
        self.state: np.ndarray = np.zeros(size, dtype=int)

        self.turn: int = 0
        self.score: int = 0
        self.win: bool = False
        self.lose: bool = False

        self._rng: np.random.Generator = np.random.Generator(np.random.PCG64())
        self.fill_tiles: int = min(fill_tiles, self.tilecount)
        self.fill_vals: list[int] = fill_vals
        valcount = len(fill_vals)
        if len(p) != valcount:
            p = [1 / valcount] * valcount
        self.weights: list[float] = p

        self._emperor_rules = merge_2048

    @property
    def width(self) -> int:
        return self.state.shape[1]

    @property
    def height(self) -> int:
        return self.state.shape[0]

    @property
    def tilecount(self) -> int:
        return self.width * self.height

    @property
    def indices(self) -> np.ndarray[tuple[int, int], np.dtype[np.int_]]:
        return np.indices(self.state.shape).T.reshape(-1, 2)

    @property
    def ravel(self) -> np.ndarray:
        return self.state.flatten()

    @property
    def empty_tiles(self) -> list[tuple[int, int]]:
        return [tuple(i) for i in self.indices if self.state[i[0]][i[1]] == 0]

    def clear(self) -> None:
        self.turn = 0
        self.score = 0
        self.win = False
        self.lose = False
        self.state = np.zeros((self.width, self.height), np.int16)

    def create(self) -> None:
        self.clear()
        fills = self._rng.choice(
            self.indices,
            size=self.fill_tiles,
            replace=False
        )
        for tile in fills:
            ch = np.random.choice(
                self.fill_vals, p=self.weights
            )
            self.state[tile[0], tile[1]] = ch
            self.score += ch

    def print_board(self) -> None:
        print(f'Turn: {self.turn}')
        print(self.state)

    def _check_move(self, tiles: np.ndarray) -> bool:
        if self.tilecount == 1:
            return tiles[0][0] == 0
        for h in range(tiles.shape[0]):  # row
            row = np.trim_zeros(tiles[h], 'b')
            for w in range(len(row)):  # val
                if row[w] == 0 or (
                    w > 0 and row[w] == row[w - 1]
                ):
                    return True
        return False

    def _check_move_er(self, tiles: np.ndarray) -> bool:
        if self.tilecount == 1:
            return tiles[0][0] == 0
        for h in range(tiles.shape[0]):  # row
            row = np.trim_zeros(tiles[h], 'b')
            for w in range(len(row)):  # val
                if row[w] == 0 or (
                    w > 0 and row[w] == row[w - 1] and row[w] < 2048
                ):
                    return True
        return False

    def can_move(self, move: Move) -> bool:
        tiles = self.state.copy()
        tiles = Transform.make(tiles, to=move)
        if self._emperor_rules:
            res = self._check_move_er(tiles)
        res = self._check_move(tiles)
        return res

    def has_moves(self) -> bool:
        rav = self.ravel
        for i, val in enumerate(rav):
            if (
                val == 0
                or (i < self.tilecount - 1 and val == rav[i + 1])
                or (
                    i < self.tilecount - self.width
                    and val == rav[i + self.width]
                )
            ):
                return True
        self.lose = True
        return False

    def has_moves_er(self) -> bool:
        rav = self.ravel
        for i, val in enumerate(rav):
            if (
                val == 0
                or (i < self.tilecount - 1 and val == rav[i + 1])
                or (
                    i < self.tilecount - self.width
                    and val == rav[i + self.width]
                    and val < 2048
                )
            ):
                return True
        self.lose = True
        return False

    def _basic_move_er(self, state: np.ndarray) -> np.ndarray:
        for i, row in enumerate(state):  # 1d
            merge = -1
            for j, val in enumerate(row):  # 0d
                for k in range(j - 1, merge, -1):
                    if row[k] == 0:
                        state[i, j], state[i, k] = state[i, k], state[i, j]
                        j -= 1
                        continue
                    elif val == row[k] and val < 2048:
                        state[i, j] = 0
                        state[i, k] *= 2
                        if state[i, k] == 2048:
                            self.win = True
                        merge = k
                    break
        return state

    def _basic_move(self, state: np.ndarray) -> np.ndarray:
        for i, row in enumerate(state):  # 1d
            merge = -1
            for j, val in enumerate(row):  # 0d
                for k in range(j - 1, merge, -1):
                    if row[k] == 0:
                        state[i, j], state[i, k] = state[i, k], state[i, j]
                        j -= 1
                        continue
                    elif val == row[k]:
                        state[i, j] = 0
                        state[i, k] *= 2
                        if state[i, k] == 2048:
                            self.win = True
                        merge = k
                    break
        return state

    def move(self, direction: Move) -> None:
        trans = Transform.make(self.state.copy(), to=direction)
        if self._emperor_rules:
            trans = self._basic_move_er(trans)
        else:
            trans = self._basic_move(trans)
        self.state = Transform.make(trans.copy(), fr=direction)

    def tick(self, direction: Move) -> None:
        if not self.can_move(direction):
            if self._emperor_rules and not self.has_moves_er():
                self.lose = True
            elif not self.has_moves():
                self.lose = True
            return
        self.move(direction)
        self.turn += 1
        if len(self.empty_tiles):
            rd = self._rng.choice(self.empty_tiles, size=1)[0]
            new_tile = self._rng.choice(self.fill_vals, p=self.weights)
            self.state[rd[0], rd[1]] = new_tile
            self.score += new_tile
        if self._emperor_rules and not self.has_moves_er():
            self.lose = True
        elif not self.has_moves():
            self.lose = True
        print(f'Score: {self.score}, win?: {self.win} lose?: {self.lose}')
