from pathlib import Path
from typing import Any
import json

import numpy as np

from board import Board


class StateTesting:

    @staticmethod
    def load_board(
        name: str = '2fill',
        filename: str = 'state_testing.json'
    ) -> Board:
        file = Path(filename)
        if not file.exists() or not file.is_file():
            raise FileNotFoundError(f"File '{file.absolute()}' is not found")
        elif file.suffix != '.json':
            raise ValueError(f"Unsupported file type for '{filename}'")
        with open(filename, 'r', encoding='utf-8') as f:
            data: dict[str, Any] = json.load(f)
        states: list[dict[str, Any]] | None = data.get('states')
        if states is None or len(states) < 1:
            raise KeyError("Couldn't find any states")
        state: dict[str, Any] | None = None
        for s in states:
            sname = s.get('name')
            if sname and sname == name:
                state = s
                break
        if not state:
            raise KeyError(f"Couldn't find state with name '{name}'")
        turn: int = state.get('turn', 0)
        width: int | None = state.get('width')
        height: int | None = state.get('height')
        tiles: list[list[int]] | None = state.get('state')
        if not tiles or len(tiles) < 1 or len(tiles[0]) < 1:
            raise KeyError(f"State '{name}' is missing tile info")
        if not width:
            width = len(tiles[0])
        if not height:
            height = len(tiles)
        board = Board((width, height))
        board.turn = turn
        board.state = np.asarray(tiles)
        board.score = int(np.sum(board.state))
        return board
