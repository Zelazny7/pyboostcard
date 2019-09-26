from __future__ import annotations
from pyboostcard.constants import *

from typing import Dict, Type, Tuple, Union, Callable, Optional
from collections import namedtuple
from abc import ABC, abstractmethod, abstractproperty
import numpy as np
import operator as op


Comparator = Callable[[np.ndarray, float], np.ndarray]


class Selection(ABC):

    priority: int

    def __init__(self, order: int = 0):
        self.order = order
        self.value: Optional[float] = np.nan

    @abstractmethod
    def in_selection(self, x: np.ndarray) -> np.ndarray:
        pass

    @property
    def sort_value(self) -> Tuple[int, int, float]:
        return self.priority, self.order, -np.inf

    def __repr__(self) -> str:
        return f"{self.order:^{ORDER_WIDTH}}|"


Bounds = namedtuple("Bounds", ["left", "right"])


class FittedSelection:
    def __init__(self, selection: Selection, value: Optional[float] = None):
        self.selection = selection
        self.value = value

    def transform(self, x: np.ndarray, result: np.ndarray) -> np.ndarray:
        replace = x if self.value is None else self.value
        # make sure to only update output vector where filter is true AND result == np.nan
        f = self.selection.in_selection(x) & np.isnan(result)
        return np.where(f, replace, result)

    @property
    def sort_value(self) -> Tuple[int, int, float]:
        return self.selection.sort_value

    @property
    def fitted(self) -> bool:
        return self.value != np.nan


class Identity(Selection):
    """"Selection responsible for only passing through -- no constraint in other words"""

    priority = 100

    def __init__(self, order: int = 0):
        self.order = 0
        self.value: Optional[float] = None

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        """Always return true for identity selections"""
        return np.full_like(x, True, dtype="bool")

    def __repr__(self) -> str:
        return f"{self.order:^{ORDER_WIDTH}}|"


class Interval(Selection):

    priority = 0

    charmap: Dict[Tuple[bool, bool], str] = {
        (False, False): "({}, {})",
        (False, True): "({}, {}]",
        (True, False): "[{}, {})",
        (True, True): "[{}, {}]",
    }

    testmap: Dict[Tuple[bool, bool], Tuple[Comparator, Comparator]] = {
        (False, False): (op.gt, op.lt),
        (False, True): (op.gt, op.le),
        (True, False): (op.ge, op.lt),
        (True, True): (op.ge, op.le),
    }

    def __init__(self, values: Tuple[float, float], bounds: Tuple[bool, bool], order: int = 0, mono: int = 0):
        """Bounds are tuple of bools where each indicates closed boundary"""
        super().__init__(order)
        self.values = sorted(values)
        self.bounds = Bounds(*bounds)
        self.mono = mono
        self._repr = self.charmap[bounds]

    def __str__(self) -> str:
        return self._repr.format(*self.values)

    def __repr__(self) -> str:
        return (
            f"{self._repr.format(*self.values):<{SELECTION_WIDTH}}|" + super().__repr__() + f"{self.mono:^{MONO_WIDTH}}"
        )

    @property
    def sort_value(self) -> Tuple[int, int, float]:
        return self.priority, self.order, self.values[0]

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
        z = np.ma.masked_invalid(x)
        ltest, rtest = self.testmap[self.bounds]
        return ltest(z, self.values[0]) & rtest(z, self.values[1])


class Override(Selection):

    priority = 1

    def __init__(self, override: float, order: int = 0):
        super().__init__(order)
        self.override = override

    def __repr__(self) -> str:
        return f"{self.override:<{SELECTION_WIDTH}}|" + super().__repr__() + " " * MONO_WIDTH

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        return (x == self.override) & ~np.isnan(x)


class Missing(Selection):

    priority = 2

    def __init__(self, order: int = 0):
        super().__init__(order)

    def __repr__(self) -> str:
        return f"{'Missing':<{SELECTION_WIDTH}}|" + super().__repr__() + " " * MONO_WIDTH

    def in_selection(self, x: np.ndarray) -> np.ndarray:
        return np.isnan(x)


if __name__ == "__main__":
    print(Interval((10.0, 20.0), (False, False)))
    print(Override(-1))
    print(Missing())

    i = Interval((5.0, 7.0), (False, False))
    x = np.array(list(range(10)))
    print(i.in_selection(x))

