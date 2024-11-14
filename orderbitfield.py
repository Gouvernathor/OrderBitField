from collections.abc import Iterable
import math
from typing import ClassVar, Self
import warnings

from deps import (
    common_prefix as _common_prefix,
    generate_codes as _generate_codes,
    simple_between as _simple_between,
    simple_before as _simple_before,
    simple_after as _simple_after,
    BYTES_ZERO as _BYTES_ZERO,
)


class ZeroOrderBitFieldWarning(Warning):
    """
    Warning emitted when a value of 0 is used as an OrderBitField.
    Such a value is invalid, as it's impossible to place a value before it.
    """

class BoundOrderBitFieldMaxSizeException(ValueError):
    """
    Exception raised when trying to create a too-large BoundOrderBitField.
    """

class OrderBitField(bytes):
    """
    Represents the ordering index of a value with respect to other similarly indexed values.

    Constructors should be used with this order of preference:
    - `OrderBitField.n_between` (when implemented, until then use `OrderBitField.between`)
      when you need to insert a value between two existing values.
    - `OrderBitField.before` and `OrderBitField.after`
      when you need to insert a value before or after an existing value.
    - `OrderBitField.initial` (when implemented)
      when you create the initial values of a sequence.
    Only class and static methods should be used to create instances of this class.

    The instances are immutable.
    The only operations that should be done between instances are comparisons and equality checks.

    Subclasses may set the `max_size` class field to limit the size of the OrderBitField (in bytes),
    which in return allows it to support concatenation to the right with other OrderBitFields.
    """
    __slots__ = ()

    max_size: ClassVar[int|None] = None

    def __new__(cls, val):
        val = bytes(val)

        if (cls.max_size is not None) and (len(val) > cls.max_size):
            raise BoundOrderBitFieldMaxSizeException(f"Value {val!r} is too long for a BoundOrderBitField of size {cls.max_size}.")

        val = val.rstrip(_BYTES_ZERO)
        if not val:
            warnings.warn(f"Value {val!r} resolves to 0 or empty bytes, which results in an invalid OrderBitField.", ZeroOrderBitFieldWarning)

        return super().__new__(cls, val)

    def __bytes__(self):
        return self[:]

    def __repr__(self):
        return f"{self.__class__.__name__}(({', '.join(map(str, self))}))"

    @classmethod
    def between(cls, start: "OrderBitField", end: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is between the two given OrderBitFields.
        Use the `n_between` method in preference to this one.
        """
        return cls(_simple_between(start[:], end[:]))

    @classmethod
    def before(cls, other: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is before the given OrderBitField.
        Returns the shortest value possible,
        and then such that it's closest to half of the given OrderBitField.
        """
        return cls(_simple_before(other[:]))

    @classmethod
    def after(cls, other: "OrderBitField") -> Self:
        """
        Constructor, returns a new OrderBitField that is after the given OrderBitField.
        """
        return cls(_simple_after(other[:]))

    @classmethod
    def n_between(cls, n: int, start: "OrderBitField|None", end: "OrderBitField|None") -> Iterable[Self]:
        """
        Constructor, yields OrderBitFields that are between the two given OrderBitFields.
        Returns the shortest values possible,
        and then as evenly spaced between the two boundaries as possible.
        """
        if start and end:
            prefixe = _common_prefix(start, end)
            if prefixe:
                start = start[len(prefixe):] # type: ignore
                end = end[len(prefixe):] # type: ignore
        else:
            prefixe = b""
        return map(cls, _generate_codes(n, start or b"", end or None, prefixe))

    @classmethod
    def initial(cls, n: int = 1) -> Iterable[Self]:
        """
        Constructor, yields OrderBitFields.
        Returns the shortest values possible,
        and then as evenly spaced as possible.
        """
        return map(cls, _generate_codes(n, b"", None, b""))

    def __add__(self, other) -> "OrderBitField":
        """
        This only works when the left instance is bound.
        The left instance is right-padded with 0 bytes until that max size.
        If the other instance is bound, the new instance is of an ad-hoc type,
        bound to the sum of the sizes.
        Otherwise, the new instance is not bound and is of type OrderBitField.
        """
        if (self.max_size is not None) and isinstance(other, OrderBitField):
            b = bytes.__add__(self.ljust(self.max_size, _BYTES_ZERO), other)
            if other.max_size is not None:
                class BoundOrderBitField(OrderBitField):
                    __slots__ = ()
                    max_size = self.max_size + other.max_size
                ty = BoundOrderBitField
            else:
                ty = OrderBitField
            return ty(b)
        return NotImplemented
