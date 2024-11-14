from collections.abc import Iterable
import math
from typing import ClassVar, Self
import warnings

from deps import (
    common_prefix as _common_prefix,
    generate_codes_v3 as _generate_codes_v3,
    MAX_BYTE as _MAX_BYTE,
    MAGIC_MIDDLE as _MAGIC_MIDDLE,
    BYTES_MAGIC_MIDDLE as _BYTES_MAGIC_MIDDLE,
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

    max_size: int|None = None

    def __new__(cls, val):
        val = bytes(val)

        if (cls.max_size is not None) and (len(val) > cls.max_size):
            raise BoundOrderBitFieldMaxSizeException(f"Value {val!r} is too long for a BoundOrderBitField of size {cls.max_size}.")

        val = val.rstrip(_BYTES_ZERO)
        if not val:
            warnings.warn(f"Value {val!r} resolves to 0 or empty bytes, which results in an invalid OrderBitField.", ZeroOrderBitFieldWarning)

        return super().__new__(cls, val)

    @property
    def val(self):
        return bytes(self)

    def __repr__(self):
        return f"{self.__class__.__name__}(({', '.join(map(str, self))}))"

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
        return map(cls, _generate_codes_v3(n, start or b"", end or None, prefixe))

    @classmethod
    def initial(cls, n: int = 1) -> Iterable[Self]:
        """
        Constructor, yields OrderBitFields.
        Returns the shortest values possible,
        and then as evenly spaced as possible.
        """
        return map(cls, _generate_codes_v3(n, b"", None, b""))

    def __add__(self, other):
        """
        This only works when the left instance is bound.
        The self instance is right-padded with 0 bytes.
        If the other instance is bound, the new instance is bound to the sum of the sizes.
        Otherwise, the new instance is not bound.
        The return type is always the type of the left operand.
        """
        if (self.max_size is not None) and isinstance(other, OrderBitField):
            rv = type(self)(bytes.__add__(self.ljust(self.max_size, _BYTES_ZERO), other))
            if other.max_size is not None:
                rv.max_size = self.max_size + other.max_size
            return rv
        return NotImplemented
