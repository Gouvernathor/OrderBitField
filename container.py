from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Hashable, Iterator, Reversible

from orderbitfield import OrderBitField


class ReorderableContainer[V](Collection[V], Reversible[V], ABC):
    __slots__ = ()

    @abstractmethod
    def move_next_to(self, next_to: V, *elements: V, after=True) -> None:
        """
        Move the element next to the next_to element.
        """

    @abstractmethod
    def add_next_to(self, next_to: V, *elements: V, after=True) -> None:
        """
        Add the element next to the next_to element.
        """

    @abstractmethod
    def add(self, *elements: V, last=True) -> None:
        """
        Add the element at the end of the container.
        """

    @abstractmethod
    def popitem(self, *, last=True) -> V:
        """
        Remove and return the last element in the container.
        """

    @abstractmethod
    def move_to_end(self, *elements: V, last=True) -> None:
        """
        Move the element to the end of the container.
        """

    @abstractmethod
    def remove(self, *elements: V) -> None:
        """
        Remove the elements from the container, raises if any is not present.
        """

    @abstractmethod
    def discard(self, *elements: V) -> None:
        """
        Remove the elements from the container if present.
        """

    # abstract :
    # __contains__
    # __iter__
    # __len__
    # __reversed__

class MappingBasedReorderableContainer[V](ReorderableContainer[V]):
    """
    Only supports hashable elements with no duplicate.
    """

    def __init__(self, *elements: V) -> None:
        self._store = dict(zip(elements, OrderBitField.initial(len(elements))))

    def __contains__(self, x: object) -> bool:
        return x in self._store

    def __iter__(self) -> Iterator[V]:
        return iter(sorted(self._store, key=self._store.__getitem__))

    def __len__(self) -> int:
        return len(self._store)

    def __reversed__(self) -> Iterator[V]:
        return iter(sorted(self._store, key=self._store.__getitem__, reverse=True))

    def move_next_to(self, next_to: V, *elements: V, after=True) -> None:
        if next_to not in self._store:
            raise KeyError(next_to)
        if not elements:
            return
        # if not (self._store.keys() > set(elements)): # TODO: check
        #     raise KeyError("Duplicate elements")

        nto = self._store[next_to]
        if after:
            nxto = min(filter(lambda o: o > nto, self._store.values()), default=None)
            newos = OrderBitField.n_between(len(elements), nto, nxto)
        else:
            nxto = max(filter(lambda o: o < nto, self._store.values()), default=None)
            newos = OrderBitField.n_between(len(elements), nxto, nto)
        for element, newo in zip(elements, newos):
            self._store[element] = newo

    def add_next_to(self, next_to: V, *elements: V, after=True) -> None:
        if next_to not in self._store:
            raise KeyError(next_to)
        if not elements:
            return
        if self._store.keys() & set(elements):
            raise KeyError("Duplicate elements")

        nto = self._store[next_to]
        if after:
            start = nto
            end = min(filter(lambda o: o > nto, self._store.values()), default=None)
        else:
            start = max(filter(lambda o: o < nto, self._store.values()), default=None)
            end = nto
        newos = OrderBitField.n_between(len(elements), start, end)
        for element, newo in zip(elements, newos):
            self._store[element] = newo

    def add(self, *elements: V, last=True) -> None:
        if last:
            start = max(self._store.values(), default=None)
            end = None
        else:
            start = None
            end = min(self._store.values(), default=None)

        newos = OrderBitField.n_between(len(elements), start, end)
        for element, newo in zip(elements, newos):
            self._store[element] = newo

    def popitem(self, *, last=True) -> V:
        if last:
            element = max(self._store, key=self._store.__getitem__)
        else:
            element = min(self._store, key=self._store.__getitem__)
        del self._store[element]
        return element

    def move_to_end(self, *elements: V, last=True) -> None:
        self.remove(*elements)
        self.add(*elements, last=last)

    def remove(self, *elements: V) -> None:
        for element in elements:
            del self._store[element]

    def discard(self, *elements: V) -> None:
        for element in elements:
            self._store.pop(element, None)
