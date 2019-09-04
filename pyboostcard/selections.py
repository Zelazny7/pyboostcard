from __future__ import annotations
from typing import Dict, Type, Tuple, Union, Callable
from collections import namedtuple
from abc import ABC, abstractmethod
import numpy as np

## set width constants for printing
SELECTION_WIDTH = 19
ORDER_WIDTH = 5
MONO_WIDTH = 5

class Selection(ABC):
    def __init__(self, order: int = 0):
        self.order = order

    @abstractmethod
    def in_selection(self, x: np.ndarray) -> np.ndarray:
        pass

    def __repr__(self) -> str:
        return f"{self.order:^{ORDER_WIDTH}}|"


Bounds = namedtuple("Bounds", ["left", "right"])


class Interval(Selection):

    charmap: Dict[Tuple[bool, bool], str] = {
        (False, False): "({}, {})",
        (False, True): "({}, {}]",
        (True, False): "[{}, {})",
        (True, True): "[{}, {}]",
    }

    testmap: Dict[Tuple[bool, bool], Callable[[np.ndarray, Tuple[float, float]], np.ndarray]] = {
        (False, False): lambda x, b: (x > b[0]) & (x < b[1]),
        (False, True): lambda x, b: (x > b[0]) & (x <= b[1]),
        (True, False): lambda x, b: (x >= b[0]) & (x < b[1]),
        (True, True): lambda x, b: (x >= b[0]) & (x <= b[1]),
    }

    def __init__(self, values: Tuple[float, float], bounds: Tuple[bool, bool], order: int = 0, mono: int = 0):
        """Bounds are tuple of bools where each indicates closed boundary"""
        super().__init__(order)
        self.values = values
        self.bounds = Bounds(*bounds)
        self.mono = mono
        self._repr = self.charmap[bounds]

    def __repr__(self) -> str:
        return f"{self._repr.format(*self.values):<{SELECTION_WIDTH}}|" + \
            super().__repr__() + \
                f"{self.mono:^{MONO_WIDTH}}"

    @property
    def mono(self) -> int:
        return self._mono

    @mono.setter
    def mono(self, value: int) -> None:
        if value not in [-1, 0, 1]:
            raise ValueError("Invalid monotonicity.")
        else:
            self._mono = value

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        test = self.testmap[self.bounds]
        return test(x, self.values)


class Exception(Selection):
    def __init__(self, value: Union[str, float, int], order: int = 0):
        super().__init__(order)
        self.value = value

    def __repr__(self) -> str:
        return f"{self.value:<{SELECTION_WIDTH}}|" + super().__repr__() + " "*MONO_WIDTH

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        return (x == self.value) & ~np.isnan(x)


class Missing(Selection):
    def __init__(self, order: int = 0):
        super().__init__(order)

    def __repr__(self) -> str:
        return f"{'Missing':<{SELECTION_WIDTH}}|" + super().__repr__() + " "*MONO_WIDTH

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        return np.isnan(x)


if __name__ == "__main__":
    print(Interval((10.0, 20.0), (False, False)))
    print(Exception(-1))
    print(Missing())

    i = Interval((5.0, 7.0), (False, False))
    x = np.array(list(range(10)))
    print(i.in_selection(x))
