"""ArgParseBuilder package."""

from functools import partial
from importlib.resources import read_text

from ._argparsebuilder import ArgParseBuilder

__version__ = read_text(__package__, 'VERSION').strip()

__all__ = ['ArgParseBuilder', 'named_partial']


def named_partial(name, func, /, doc=None, *args, **kwargs):
    """Return a named partial function.

    When an :class:`~argparse.ArgumentParser` creates an error message when
    the conversion of an argument failed, it uses the ``__name__`` attribute
    of the conversion function for the type name. A function created with
    :func:`~functools.partial` does not have such an attribute and in that case
    a (ugly looking) name is created by applying :func:`repr` to the function.

    This function is a convenient way to create a partial function and set its
    ``__name__`` and ``__doc__`` attributes.

    :param str name: the name of the partial function
    :param func: see :func:`functools.partial`
    :param str doc: documentation string for ``__doc__`` attribute
    :param args: see :func:`functools.partial`
    :param kwargs: see :func:`functools.partial`
    :return: partial function object with ``__name__`` attribute set to ``name``
    """
    if not callable(func):
        raise TypeError("the second argument must be callable")
    f = partial(func, *args, **kwargs)
    f.__name__ = name
    if doc is not None:
        f.__doc__ = doc
    return f
