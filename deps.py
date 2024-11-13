from collections import Counter, defaultdict
from collections.abc import Collection, Iterable, Mapping
import types


_EMPTYMAP = types.MappingProxyType({})
_TOP_VALUE = 256
MAX_BYTE = _TOP_VALUE - 1
MAGIC_MIDDLE = _TOP_VALUE // 2
BYTES_MAGIC_MIDDLE = bytes((MAGIC_MIDDLE,))
BYTES_ZERO = bytes((0,))

def common_prefix(s1: bytes, s2: bytes) -> bytes:
    """
    Requires s1 and s2 to be ordered, in that order.
    """
    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1

def generate_codes_v3(
        ncodes: int,
        code_start: bytes,
        code_end: bytes|None,
        prefixe: bytes,
        ) -> Iterable[bytes]:
    if not ncodes:
        return

    start_digit_1 = code_start[0] if code_start else 0
    end_digit_1 = code_end[0] if code_end else MAX_BYTE

    # there are going to be direct codes (form prefixe + x)
    # and longer codes (form prefixe + xy)

    # range of possible direct digits : [[start_digit_1 + 1, end_digit_1]]
    n_direct_candidates = end_digit_1 - (start_digit_1 + 1) + 1
    direct: Collection[int]
    longer: Mapping[int, int]

    if n_direct_candidates >= ncodes:
        # everything can go in direct codes

        if n_direct_candidates == ncodes:
            # no need to arrange
            direct = range(start_digit_1 + 1, end_digit_1 + 1)
        else:
            direct = frozenset(_simple_distribute_indices(ncodes, start_digit_1+1, end_digit_1))

        longer = _EMPTYMAP

    else:
        # there are too many codes to be generated for direct codes to suffice
        # we take all available direct codes
        direct = range(start_digit_1 + 1, end_digit_1 + 1)

        # distributing longer codes among the digits by which they will begin
        # interval those starting digits : [[start_digit_1, end_digit_1]]
        longer_ponderation = defaultdict[int, float](lambda: 1)

        # if we have a starting boundary and it has a second digit,
        # the first digit's ponderation is the distance
        # between that second digit (excluded) and _TOP_VALUE (included)
        if len(code_start) > 1:
            longer_ponderation[end_digit_1] = (_TOP_VALUE - code_start[1]) / _TOP_VALUE
        # otherwise that digit has no particular ponderation
        # in any case, start_digit_1 is valid as a start for longer codes

        longer_max_boundary: int # inclusive
        if code_end:
            # if there is an end boundary,
            if len(code_end) > 1:
                # if it has a second digit,
                # the first digit's ponderation is the distance
                # between 0 (included) and that second digit (excluded)
                longer_ponderation[end_digit_1] = (code_end[1] - 0) / _TOP_VALUE
                longer_max_boundary = end_digit_1
            else:
                longer_max_boundary = end_digit_1 - 1
        else:
            longer_max_boundary = end_digit_1

        longer = _ponderated_distribute_indices(
            ncodes - n_direct_candidates,
            start_digit_1, longer_max_boundary,
            longer_ponderation)

    assert sum(longer.values()) + len(direct) == ncodes

    for c in range(start_digit_1, end_digit_1 + 1):
        pre = prefixe + bytes((c,))

        if c in direct:
            yield pre

        nrecurs = longer.get(c, 0)
        if nrecurs:
            yield from generate_codes_v3(
                nrecurs,
                code_start[1:] if code_start and c == start_digit_1 else b"",
                code_end[1:] if code_end and c == end_digit_1 else None,
                pre)

def _ponderated_distribute_indices(
        ncodes: int,
        mn: int, mx: int,
        ponderation: Mapping[int, float],
        ) -> Mapping[int, int]:
    assert 0 <= mn
    assert mn < mx
    assert mx < _TOP_VALUE

    nchars = mx - mn + 1
    attrib = Counter()
    restant = ncodes

    if ncodes > nchars:
        total = sum(ponderation[c] for c in range(mn, mx + 1))
        for c in range(mn, mx + 1):
            val = int(ncodes * ponderation[c] / total)
            attrib[c] = val
            restant -= val

    for c in _simple_distribute_indices(restant, mn, mx):
        attrib[c] += 1

    return attrib

def _simple_distribute_indices(ncodes: int, mn: int, mx: int) -> Iterable[int]:
    if ncodes <= 0:
        return ()

    nchars = mx - mn + 1

    assert ncodes <= nchars

    if ncodes == 2:
        yield mn + (nchars - 1)//3
        yield mn + (2*nchars - 1)//3
        return

    # midpoint
    pivot = mn + nchars//2

    if ncodes == 1:
        yield pivot
    else:
        # numbers of code to put on the right
        # (must be lower or equal to those on the left because of how the pivot is computed,
        # which favors the fact that appending is more frequent than prepending,
        # so if we must choose best leave more room after rather than before)
        right = (ncodes-1) // 2

        yield from _simple_distribute_indices(ncodes-1-right, mn, pivot-1)
        yield pivot
        yield from _simple_distribute_indices(right, pivot+1, mx)
