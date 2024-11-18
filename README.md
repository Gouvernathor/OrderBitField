This is a Python module to manage containers and sets of objects which can be arbitrarily reordered without having a sequence structure (that is, a n°1, 2, 5 or 10) usually represented by lists or arrays.

Elements are indexed by binary codes, which are likely to be the simplest data structure and the fastest to compare/sort, across virtually any platform or language.

The deps.py file (for "dependencies") contains the core algorithm to create binary codes in a way that optimizes code length through arbitrary insertions and reorderings.

The orderbitfield.py file contains a subclass of bytes (the Python builtin class for binary sequences, similar to byte[] in Java or BINARY in SQL) that represents the binary code, with utility methods to manipulate it, relying on the functions defined in deps.

The container.py file contains a Collection-like container, similar in interface to an ordered set, that uses the OrderBitField class under the hood to manage the ordering of elements. Again, its interface includes a number of utility methods to manipulate the order of elements in the container. The idea is that it can be used without any knowledge of, or access to, the underlying binary fields system.
