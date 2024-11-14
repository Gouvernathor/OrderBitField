from abc import ABC, abstractmethod
from collections.abc import Callable, Collection, Iterator, Reversible
from typing import Protocol, TypeVar, override

from orderbitfield import OrderBitField


class SelfComparable(Protocol):
    """
    Protocol for types that can be compared to themselves.
    """
    def __lt__(self: "CV", other: "CV", /) -> bool: ...
CV = TypeVar("CV", bound=SelfComparable)

class ReorderableContainer[T](Collection[T], Reversible[T], ABC):
    __slots__ = ()

    @abstractmethod
    def put_between(self, start: T, end: T, *elements: T) -> None:
        """
        Put the elements between the start and end elements.
        """

    @abstractmethod
    def put_to_end(self, *elements: T, last=True) -> None:
        """
        Put the elements at one end of the container.
        """

    @abstractmethod
    def put_next_to(self, next_to: T, *elements: T, after=True) -> None:
        """
        Put the elements next to the next_to element.
        """

    @abstractmethod
    def recompute(self) -> None:
        """
        Recompute the order markers of the elements, without changing the ordering.
        """

    @abstractmethod
    def popitem(self, *, last=True) -> T:
        """
        Remove and return the last element in the container.
        """

    @abstractmethod
    def remove(self, *elements: T) -> None:
        """
        Remove the elements from the container, raises if any is not present.
        """

    @abstractmethod
    def discard(self, *elements: T) -> None:
        """
        Remove the elements from the container if present.
        """

    @abstractmethod
    def sort_key(self) -> Callable[[T], SelfComparable]:
        """
        Extracts a key function, to be used i.e in the sorted or list.sort methods.
        """

    @property
    @abstractmethod
    def elements(self) -> Collection[T]:
        """
        The elements of the container, in no particular order.
        May be a cheaper operation than iterating over the container in order.
        """

    # abstract :
    # __contains__
    # __iter__
    # __len__
    # __reversed__

class MappingBasedReorderableContainer[T](ReorderableContainer[T]):
    """
    Only supports hashable elements with no duplicate.
    """

    def __init__(self, *elements: T) -> None:
        self._store = dict(zip(elements, OrderBitField.initial(len(elements))))

    @property
    @override
    def elements(self) -> Collection[T]:
        return self._store.keys()

    @override
    def __contains__(self, x: object) -> bool:
        return x in self._store

    @override
    def __iter__(self) -> Iterator[T]:
        return iter(sorted(self._store, key=self._store.__getitem__))

    @override
    def __len__(self) -> int:
        return len(self._store)

    @override
    def __reversed__(self) -> Iterator[T]:
        return iter(sorted(self._store, key=self._store.__getitem__, reverse=True))

    def _put_between_orderfields(self, elements: Collection[T], start: OrderBitField|None, end: OrderBitField|None):
        newos = OrderBitField.n_between(len(elements), start, end)
        for element, newo in zip(elements, newos):
            self._store[element] = newo

    @override
    def put_between(self, start: T, end: T, *elements: T) -> None:
        if start == end:
            raise ValueError("The start and end elements are the same")
        self._put_between_orderfields(elements, self._store[start], self._store[end])

    @override
    def put_to_end(self, *elements: T, last=True) -> None:
        if last:
            start = max(self._store.values(), default=None)
            end = None
        else:
            start = None
            end = min(self._store.values(), default=None)

        self._put_between_orderfields(elements, start, end)

    @override
    def put_next_to(self, next_to: T, *elements: T, after=True) -> None:
        nto = self._store[next_to]
        if after:
            start = nto
            end = min(filter(lambda o: o > nto, self._store.values()), default=None)
        else:
            start = max(filter(lambda o: o < nto, self._store.values()), default=None)
            end = nto

        self._put_between_orderfields(elements, start, end)

    @override
    def recompute(self) -> None:
        self._store = dict(zip(self, OrderBitField.initial(len(self))))

    @override
    def popitem(self, *, last=True) -> T:
        if last:
            element = max(self._store, key=self._store.__getitem__)
        else:
            element = min(self._store, key=self._store.__getitem__)
        del self._store[element]
        return element

    @override
    def remove(self, *elements: T) -> None:
        for element in elements:
            del self._store[element]

    @override
    def discard(self, *elements: T) -> None:
        for element in elements:
            self._store.pop(element, None)

    @override
    def sort_key(self) -> Callable[[T], SelfComparable]:
        return self._store.__getitem__
