"""A builder class for :class:`argparse.ArgumentParser`."""

from argparse import ArgumentParser, BooleanOptionalAction

__all__ = ['ArgParseBuilder']

_subcommand_name = 'subcommand_name'  # attribute name in result
_subcommand_func = 'subcommand_func'  # attribute name in result


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
        if kwargs.get('fromfile_prefix_chars') is not None:
            self._parser.convert_arg_line_to_args = lambda line: line.split()
        self._short_prefix = self._parser.prefix_chars[0]
        self._long_prefix = self._parser.prefix_chars[0] * 2
        self._arg_group = None
        self._xcl_group = None
        self._subcommands_attrs = dict(title='subcommands',
                                       dest=_subcommand_name)
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

    def _add_argument(self, short=None, long=None, **kwargs):
        """Call :meth:`~argparse.ArgumentParser.add_argument`.

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
        self._add_argument(short, long, help=help, action='help')
        return self

    def add_version(self, short='V', long='version', *, version=None,
                    string=None, help='show version and exit'):
        """Add version.

        If ``string`` is set it will be printed, else if ``version`` is set the
        resulting string will be ``prog + ' ' + version``.

        :param str short: short option
        :param str long: long option
        :param version: version; if it is a :class:`tuple` it will be converted
                        to a string
        :type version: string or tuple
        :param string: version string
        :param str help: help text
        """
        if isinstance(version, tuple):
            version = '.'.join(map(str, version))
        if version and not string:
            string = f'{self._parser.prog} {version}'
        if string:
            self._add_argument(short, long, help=help, action='version',
                               version=string)
        return self

    def add_flag(self, short=None, long=None, *, count=False, dest=None,
                 const=None, help=None):
        """Add flag.

        :param str short: short option
        :param str long: long option
        :param bool count: if ``True`` count the number of times the flag occurs
        :param str dest: name of the list to which the values will be appended;
                         ignored if ``count`` is set
        :param const: only used if ``dest`` is set; defaults to the flag name
        :param str help: help text

        If ``long`` ends with ``|no``, a negative flag will be added, i.e.
        for a flag ``--foo`` there will be a flag ``--no-foo``. In this
        case ``count`` and ``dest`` will be ignored.
        """
        if long and long.endswith('|no'):
            self._add_argument(short, long[:-3],
                               action=BooleanOptionalAction, help=help)
        elif count:
            self._add_argument(short, long, action='count',
                               default=0, help=help)
        elif dest:
            if const is None:
                const = long or short
            self._add_argument(short, long, action='append_const', dest=dest,
                               const=const, help=help)
        else:
            self._add_argument(short, long, action='store_true', help=help)
        return self

    def add_opt(self, short=None, long=None, *, type=None, nargs=None,
                default=None, const=None, choices=None, required=False,
                multiple=False, metavar=None, help=None):
        """Add option.

        :param str short: short option
        :param str long: long option
        :param type: see :meth:`~argparse.ArgumentParser.add_argument`
        :param nargs: see :meth:`~argparse.ArgumentParser.add_argument`
        :param default: see :meth:`~argparse.ArgumentParser.add_argument`
        :param const: see :meth:`~argparse.ArgumentParser.add_argument`
        :param choices: see :meth:`~argparse.ArgumentParser.add_argument`
        :param required: see :meth:`~argparse.ArgumentParser.add_argument`
        :param bool multiple: if ``True`` this option can be used multiple times
                              and all values are appended to a list
        :param metavar: see :meth:`~argparse.ArgumentParser.add_argument`
        :param str help: help text
        """
        if const is not None and not nargs:
            nargs = '?'
            action = None
        elif multiple:
            action = 'append'
        else:
            action = 'store'
        self._add_argument(short, long, type=type, nargs=nargs, default=default,
                           const=const, choices=choices, metavar=metavar,
                           required=required, help=help, action=action)
        return self

    def add_pos(self, name, *, type=None, nargs=None, default=None,
                choices=None, metavar=None, help=None):
        """Add positional argument.

        :param str name: name of argument
        :param type: see :meth:`~argparse.ArgumentParser.add_argument`
        :param nargs: see :meth:`~argparse.ArgumentParser.add_argument`
        :param default: see :meth:`~argparse.ArgumentParser.add_argument`
        :param choices: see :meth:`~argparse.ArgumentParser.add_argument`
        :param metavar: see :meth:`~argparse.ArgumentParser.add_argument`
        :param str help: help text
        """
        self._add_argument(dest=name, type=type, nargs=nargs, default=default,
                           choices=choices, metavar=metavar, help=help)
        return self

    def add_mutually_exclusive_group(self, required=False):
        """Add mutually exclusive group.

        See: :meth:`argparse.ArgumentParser.add_mutually_exclusive_group`
        """
        if self._arg_group:
            self._xcl_group = self._arg_group.add_mutually_exclusive_group(
                required=required)
        elif self._subcommand:
            self._xcl_group = self._subcommand.add_mutually_exclusive_group(
                required=required)
        else:
            self._xcl_group = self._parser.add_mutually_exclusive_group(
                required=required)
        return self

    def finish_mutually_exclusive_group(self):
        """Finish mutually exclusive group.

        Adding a new mutually exclusive or argument group or a subcommand will
        finish a current mutually exclusive group implicitly.
        """
        self._xcl_group = None
        return self

    def add_argument_group(self, title=None, description=None):
        """Add argument group.

        See: :meth:`argparse.ArgumentParser.add_argument_group`
        """
        self._xcl_group = None
        if self._subcommand:
            self._arg_group = self._subcommand.add_argument_group(
                title, description)
        else:
            self._arg_group = self._parser.add_argument_group(
                title, description)
        return self

    def finish_argument_group(self):
        """Finish argument group.

        Adding a new argument group or a subcommand will finish a current
        argument group implicitly.
        """
        self._xcl_group = None
        self._arg_group = None
        return self

    def set_subcommands_attrs(self, **kwargs):
        """Set attributes for subcommands.

        If used at all, it must be called before first call to
        :meth:`add_subcommand`.

        :param kwargs: same arguments as for
                       :meth:`~argparse.ArgumentParser.add_subparsers`
        """
        self._subcommands_attrs.update(kwargs)
        return self

    def add_subcommand(self, name, *, func=None, **kwargs):
        """Add subcommand.

        :param str name: name of the subcommand; will be available in the result
                         after argument parsing under the name
                         ``subcommand_name``
        :param callable func: can be called when the subcommand is invoked;
                              will be available in the result
                              after argument parsing under the name
                              ``subcommand_func``
        :param kwargs: same arguments as for the method ``add_parser()`` which
                       is decribed in the documentation of
                       :meth:`~argparse.ArgumentParser.add_subparsers`
        """
        if not self._subparsers:
            self._subparsers = self._parser.add_subparsers(
                **self._subcommands_attrs)
        self._xcl_group = None
        self._arg_group = None
        if 'prefix_chars' not in kwargs:
            kwargs['prefix_chars'] = self._parser.prefix_chars
        kwargs['add_help'] = False
        self._subcommand = self._subparsers.add_parser(name, **kwargs)
        if func:
            self._subcommand.set_defaults(**{_subcommand_func: func})
        return self

    def finish_subcommand(self):
        """Finish subcommand.

        Adding a new subcommand will finish a current subcommand implicitly.
        """
        self._xcl_group = None
        self._arg_group = None
        self._subcommand = None
        return self

    def finish(self):
        """Finish the builder and return the argument parser."""
        self._xcl_group = None
        self._arg_group = None
        self._subcommand = None
        return self._parser
