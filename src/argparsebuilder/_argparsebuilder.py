"""A builder class for :class:`argparse.ArgumentParser`."""

from argparse import ArgumentParser
from collections.abc import Iterable

__all__ = ['ArgParseBuilder']


class ArgParseBuilder:
    """Builder for an :class:`~argparse.ArgumentParser`.

    Takes the same ``kwargs`` as :class:`~argparse.ArgumentParser`, but
    ``allow_abbrev`` defaults to ``False``, ``add_help`` is ignored
    and always ``False``, and from ``prefix_chars`` the first character
    is used for all options/flags.

    All methods except :meth:`finish` return ``self``.

    :param parser_class: the argument parser class; defaults to
                         :class:`~argparse.ArgumentParser`
    :type parser_class: argparse.ArgumentParser
    :param kwargs: see :class:`~argparse.ArgumentParser`
    """

    subcommand_name = 'subcommand_name'  #: Attribute name in result.
    subcommand_func = 'subcommand_func'  #: Attribute name in result.

    def __init__(self, *, parser_class=None, **kwargs):
        if parser_class is not None and (
                not isinstance(parser_class, type) or
                not issubclass(parser_class, ArgumentParser)):
            raise TypeError("'parser_class' must be a subclass of"
                            " argparse.ArgumentParser")
        if 'allow_abbrev' not in kwargs:
            kwargs['allow_abbrev'] = False
        kwargs['add_help'] = False
        if parser_class:
            self._parser = parser_class(**kwargs)
        else:
            self._parser = ArgumentParser(**kwargs)
        self._short_prefix = self._parser.prefix_chars[0]
        self._long_prefix = self._parser.prefix_chars[0] * 2
        self._arg_group = None
        self._xcl_group = None
        self._subcommands_attrs = dict(title='subcommands', required=True,
                                       dest=self.__class__.subcommand_name)
        self._subparsers = None
        self._subcommand = None

    def set_description(self, descr):
        """Set the ``description`` attribute of the parser.

        :param str descr: description string
        """
        self._parser.description = descr
        return self

    def set_epilog(self, epilog):
        """Set the ``epilog`` attribute of the parser.

        :param str epilog: epilog string
        """
        self._parser.epilog = epilog
        return self

    def add_argument(self, short=None, long=None, **kwargs):  # TODO: private ???
        """Calls :meth:`~argparse.ArgumentParser.add_argument`.

        ``kwargs``: all arguments after ``name or flags...``
        (for positional arguments use ``dest`` for the name)
        """
        options_or_flags = []
        if short:
            options_or_flags.append(self._short_prefix + short)
        if long:
            options_or_flags.append(self._long_prefix + long)
        if self._xcl_group:
            self._xcl_group.add_argument(*options_or_flags, **kwargs)
        elif self._arg_group:
            self._arg_group.add_argument(*options_or_flags, **kwargs)
        elif self._subcommand:
            self._subcommand.add_argument(*options_or_flags, **kwargs)
        else:
            self._parser.add_argument(*options_or_flags, **kwargs)
        return self

    def add_help(self, short='h', long='help', *,
                 help='show this help message and exit'):
        """Add help.

        :param str short: short option
        :param str long: long option
        :param str help: help text
        """
        self.add_argument(short, long, help=help, action='help')
        return self

    def add_version(self, short='V', long='version', *, version=None,
                    string=None, help='show version and exit'):
        """Add version.

        If ``version`` is a :class:`tuple` it will be converted to a string
        with ``'.'.join(map(str, version))``.

        If ``string`` is set it will be printed, else if ``version`` is set the
        resulting string will be ``prog + ' ' + version``.

        :param str short: short option
        :param str long: long option
        :param version: version
        :type version: string or tuple
        :param string: version string
        :param str help: help text
        """
        if isinstance(version, Iterable):
            version = '.'.join(map(str, version))
        if version and not string:
            string = f'{self._parser.prog} {version}'
        self.add_argument(short, long, help=help, action='version',
                          version=string)
        return self

    def add_flag(self, short=None, long=None, *, count=False, help=None):
        """Add flag.

        :param str short: short option
        :param str long: long option
        :param bool count: if ``True`` count the number of times the flag occurs
        :param str help: help text
        """
        if count:
            self.add_argument(short, long, action='count', default=0, help=help)
        else:
            self.add_argument(short, long, action='store_true', help=help)
        return self

    def add_opt(self, short=None, long=None, *, type=None, nargs=None,
                default=None, const=None, choices=None, required=False,
                metavar=None, help=None):
        """Add option.

        :param str short: short option
        :param str long: long option
        :param str help: help text
        """
        if const is not None and not nargs:
            nargs = '?'
        self.add_argument(short, long, type=type, nargs=nargs, default=default,
                          const=const, choices=choices, metavar=metavar,
                          required=required, help=help)
        return self

    def add_pos(self, name, *, type=None, nargs=None, default=None,
                choices=None, metavar=None, help=None):
        """Add positional argument.

        :param str short: short option
        :param str long: long option
        :param str help: help text
        """
        self.add_argument(dest=name, type=type, nargs=nargs, default=default,
                          choices=choices, metavar=metavar, help=help)
        return self

    def add_mutually_exclusive_group(self, required=False):
        """Add mutually exclusive group.

        See: :meth:`argparse.ArgumentParser.add_mutually_exclusive_group`
        """
        if self._arg_group:
            self._xcl_group = self._arg_group.add_mutually_exclusive_group(required=required)
        elif self._subcommand:
            self._xcl_group = self._subcommand.add_mutually_exclusive_group(required=required)
        else:
            self._xcl_group = self._parser.add_mutually_exclusive_group(required=required)
        return self

    def finish_mutually_exclusive_group(self):
        """Finish mutually exclusive group."""
        self._xcl_group = None
        return self

    def add_argument_group(self, title=None, description=None):
        """Add argument group.

        See: :meth:`argparse.ArgumentParser.add_argument_group`
        """
        self._xcl_group = None
        if self._subcommand:
            self._arg_group = self._subcommand.add_argument_group(title, description)
        else:
            self._arg_group = self._parser.add_argument_group(title, description)
        return self

    def finish_argument_group(self):
        """Finish argument group."""
        self._xcl_group = None
        self._arg_group = None
        return self

    def set_subcommands_attrs(self, **kwargs):
        """Set attributes for subcommands.

        If used at all it must be called before first call to
        :meth:`add_subcommand`.

        :param kwargs: same arguments as for
                       :meth:`~argparse.ArgumentParser.add_subparsers`
        """
        self._subcommands_attrs.update(kwargs)
        return self

    def add_subcommand(self, name, *, func=None, **kwargs):
        """Add subcommand."""
        if not self._subparsers:
            self._subparsers = self._parser.add_subparsers(**self._subcommands_attrs)
        self._xcl_group = None
        self._arg_group = None
        if 'prefix_chars' not in kwargs:
            kwargs['prefix_chars'] = self._parser.prefix_chars
        kwargs['add_help'] = False
        self._subcommand = self._subparsers.add_parser(name, **kwargs)
        if func:
            self._subcommand.set_defaults(**{self.__class__.subcommand_func: func})
        return self

    def finish_subcommand(self):
        """Finish subcommand."""
        self._xcl_group = None
        self._arg_group = None
        self._subcommand = None
        return self

    def finish(self):
        """Finish the builder and return the parser."""
        self._xcl_group = None
        self._arg_group = None
        self._subcommand = None
        return self._parser
