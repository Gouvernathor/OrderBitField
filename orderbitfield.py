from collections.abc import Iterable
import math
from typing import ClassVar, Self
import warnings


_MAX_BYTE = 127  # maximum value of a byte
_MAGIC_MIDDLE = _MAX_BYTE // 2
_BYTES_MAGIC_MIDDLE = bytes((_MAGIC_MIDDLE,))
_BYTES_ZERO = bytes((0,))

class ZeroOrderBitFieldWarning(Warning):
    """
    Warning emitted when a value of 0 is used as an OrderBitField.
    Such a value is invalid, as it's impossible to place a value before it.
    """

class OrderBitField(bytes):
    """
    Represents the ordering index of a value with respect to other similarly indexed values.

    Constructors should be used with this order of preference:
    - `OrderBitField.n_between` (when implemented, until then use `OrderBitField.between`)
      when you need to insert a value between two existing values.
    - `OrderBitField.before` and `OrderBitField.after`
      when you need to insert a value before or after an existing value.
    - `OrderBitField.n_initial` (when implemented)
      when you create the initial values of a sequence.
    Only class and static methods should be used to create instances of this class.

    The instances are immutable.
    The only operations that should be done between instances are comparisons and equality checks.
    """
    __slots__ = ()

    def __new__(cls, val):
        val = bytes(val).rstrip(_BYTES_ZERO)
        if not val:
            warnings.warn(f"Value {val!r} resolves to 0 or empty bytes, which results in an invalid OrderBitField.", ZeroOrderBitFieldWarning)

        return super().__new__(cls, val)

    @property
    def val(self):
        return bytes(self)

    def __repr__(self):
        return f"{type(self)}(({', '.join(map(str, self))}))"

    @classmethod
    def between(cls, start: "OrderBitField", end: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is between the two given OrderBitFields.
        Use the `n_between` method in preference to this one.
        """
        for i, (a, b) in enumerate(zip(start, end)):
            if a != b:
                post = (a + b) // 2
                posts = bytearray((post,))
                if post in (a, b):
                    posts.append(_MAGIC_MIDDLE)
                return cls(start[:i] + bytes(posts))

        mx = max(start, end, key=len)
        post = mx[i+1] // 2 # type: ignore
        posts = bytearray((post,))
        if post == 0:
            posts.append(_MAGIC_MIDDLE)
        return cls(start[:i] + bytes(posts)) # type: ignore

    @classmethod
    def before(cls, other: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is before the given OrderBitField.
        Returns the shortest value possible,
        and then such that it's closest to half of the given OrderBitField.
        """
        for i, b in enumerate(other):
            if b > 0:
                post = b // 2
                posts = bytearray((post,))
                if post == 0:
                    posts.append(_MAGIC_MIDDLE)
                return cls(other[:i] + posts)
        raise ValueError("Cannot create a value before 0.")

    @classmethod
    def after(cls, other: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is after the given OrderBitField.
        """
        for i, b in enumerate(other):
            if b < _MAX_BYTE:
                post = b + math.ceil((_MAX_BYTE - b) / 2)
                posts = bytearray((post,))
                if post == b:
                    posts.append(_MAGIC_MIDDLE)
                return cls(other[:i] + posts)
        return cls(other[:] + _BYTES_MAGIC_MIDDLE)

    @classmethod
    def n_between(cls, n: int, start: "OrderBitField", end: "OrderBitField|None") -> Iterable[Self]:
        """
        Constructor, yields OrderBitFields that are between the two given OrderBitFields.
        Returns the shortest values possible,
        and then as evenly spaced between the two boundaries as possible.
        """
        # TODO should implement the full algorithm,
        # start should be exceptionnaly emptyable but not nullable
        # end should be nullable but not emptyable
        raise NotImplementedError

    @classmethod
    def n_initial(cls, n: int = 1) -> "Iterable[Self]":
        """
        Constructor, yields OrderBitFields.
        Returns the shortest values possible,
        and then as evenly spaced as possible.
        """
        with warnings.catch_warnings(action="ignore", category=ZeroOrderBitFieldWarning):
            start = cls(_BYTES_ZERO)
        return cls.n_between(n, start, None)

    # TODO test this for internal failures
    __add__ = __radd__ = lambda self, other: NotImplemented


# Bound OrderBitFields

class BoundOrderBitFieldMaxSizeException(ValueError):
    """
    Exception raised when trying to create a too-large BoundOrderBitField.
    """

class BoundOrderBitField(OrderBitField):
    """
    Abstract base class for bound OrderBitFields.

    Pass max_size=n to the subclass definition (either as a class field or as kwargs) to create a BoundOrderBitField type of size n.
    Nothing else needs to be added to the subclass definition (other than a recommended `__slots__=()`).

    BoundOrderBitField instances have a maximum size,
    so depending on constraints, some of the classmethod constructors may raise a BoundOrderBitFieldMaxSizeException.
    The counterpart is that BoundOrderBitField instances can be concatenated to the right with other OrderBitFields.
    """
    __slots__ = ()
    max_size: ClassVar[int]

    def __new__(cls, val):
        val = bytes(val)
        if len(val) > cls.max_size:
            raise BoundOrderBitFieldMaxSizeException(f"Value {val!r} is too long for a BoundOrderBitField of size {cls.max_size}.")
        return super().__new__(cls, val)

    def __add__(self, other: OrderBitField):
        """
        The self instance is right-padded with 0 bytes.
        If the other instance is bound, the new instance is bound to the sum of the sizes.
        Otherwise, the new instance is an unbound OrderBitField.
        """
        if isinstance(other, BoundOrderBitField):
            class NewBoundOrderBitField(BoundOrderBitField, max_size=self.max_size + other.max_size):
                __slots__ = ()
            new_type = NewBoundOrderBitField
        else:
            new_type = OrderBitField
        return new_type(bytes.__add__(self.ljust(self.max_size, _BYTES_ZERO), other))

    def __init_subclass__(cls, *, max_size=None) -> None:
        if max_size is not None:
            cls.max_size = max_size
        return super().__init_subclass__()
