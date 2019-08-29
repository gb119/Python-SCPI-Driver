#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core base classes for the pyscipi package.

Created on Thu Aug 29 22:21:11 2019

@author: phygbu
"""
__all__ = ["SCPI_Path_Dict", "Param", "SCPI_Instrument_Mixin"]

from collections import MutableMapping, OrderedDict

from ..exceptions import CommandError


class SCPI_Path_Dict(MutableMapping):

    """Add extra logic to getitem to allow keys to partially match.

    This class uses the abstract base class for a MutableMapping, passing through
    the required abstract methods to an underlying OrderedDict store.

    All name lookups are passed through a functional that understands the partial matching rules of SCPI"""

    def __init__(sellf, *args, **kargs):
        """Create the actual dictionary store we use and then init it."""

        self._store = OrderedDict(*args)

    def __delitem__(name):
        """Delete an item from the dictionary."""
        name = self.canonical(name)
        del self._store[name]

    def __setitem__(name, value):
        """Set an item into the dictionary."""
        try:
            name = self.canonical(name)
        except Keyr:
            name = name.upper()  # Force upper case names
        self._store[name] = value

    def __getitem__(self, name):
        """Get an item from the dictionary."""
        name = self.canonical(name)
        return self._store[name]

    def __iter__(self):
        """Just iterate over our own keys."""
        return self._store.keys()

    def __len__(self):
        """Our length."""
        return len(self._store)

    def __contains__(self, name):
        """Shortcut the constains to just check with our fuzzy match function."""
        try:
            self.canonical(name)
        except KeyError:
            return False
        return True

    def canonical(self, name):
        name = name.upper()
        if super(SCPI_Path_Dict, self).__contains__(name):
            return name
        for n in self.keys():
            if name.startswith(n):
                return n
        else:
            raise KeyError("Cannot make {} into a canonical name:".format(name))


class Param(object):

    """Container to hold expected send and return types for SCPI commands."""

    def __init__(self, read=None, write=None):
        self.read = read
        self.write = write

    def __repr__(self):
        return "R:{}, W:{}".format(self.read, self.write)

    def format_write(self, tree, value):
        """Use Parameter info to check and format a string to send."""
        if isinstance(self.write, type):
            write = self.write(1)
        else:
            write = self.write
        if self.write is None:
            raise CommandError(
                "Read only parameter {} trying to be written with {}".format(
                    tree, value
                )
            )
        if isinstance(write, str):
            return "{} {}".format(tree, value)
        elif isinstance(write, bool):
            value = "ON" if value else "OFF"
            return "{} {}".format(tree, value)
        elif isinstance(write, int):
            value = int(value)
            return "{} {}".format(tree, value)
        elif isinstance(write, float):
            value = float(value)
            return "{} {}".format(tree, value)
        elif isinstance(write, np.ndarray):
            if not isinstance(value, Iterable):
                raise ValueError(
                    "{} expects an iterable value not a {}".format(tree, type(value))
                )
            value = np.array(value).astype(self.write.dtype)
            length = self.write.size
            ret = []
            for ix in range(value.size // length + 1):
                ret.append(
                    "{} {}".format(
                        tree,
                        ",".join(value[ix * length : (ix + 1) * length].astype(str)),
                    )
                )
            return "\n".join(ret)
        else:
            return "{} {}".format(tree, value)

    def do_read(self, tree, instr):
        """Use Parameter info to check and format a string to send."""
        if self.read is None:
            instr.write(tree)
            return None
        else:
            return self.format_read(instr.trans(tree + "?"))

    def format_read(self, value):
        """Use self.read to convert the return type to something sensible for Python."""
        if not isinstance(self.read, type):
            read = self.read.__class__
        else:
            read = self.read
        if self.read is bool:
            return value.upper().strip() in ["1", "ON", "YES", "TRUE"]
        if issubclass(read, np.ndarray):
            value = [float(x) for x in value.split(",")]
            return np.array(value)
        else:
            return read(value)


class SCPI_Instrument_Mixin(object):

    """A Mixin for adding IEEE4888.2 Standard Commands.

    This Mixin class needs to be used in conjunction with a InstrumentComms subclass
    to provide the methods to actualy communicate with the instrument via the selected
    interface.
    """

    @property
    def idn(self):
        return self.trans("*IDN?")

    @property
    def opc(self):
        ret = int(self.trans("*OPC?"))
        return ret == 1

    @property
    def sre(self):
        return int(self.trans("*SRE?"))

    @sre.setter
    def sre(self, value):
        value = int(value) % 256  # sanitise sre
        self.write("*SRE {}".format(value))

    @property
    def stb(self):
        return int(self.trans("*STB?"))

    def _get_path(self, name):
        """Locate the current path in the command dictionary."""
        full_path = name
        tree = full_path.replace(path.sep, ":")
        canonical = []
        cmd_dict = self.commands
        for part in tree.split(":"):
            if part not in cmd_dict:
                raise AttributeError(
                    "{} not recognised by driver as a SCPI command!".format(tree)
                )
            else:
                part = cmd_dict.canonical(part)
                canonical.append(part)
                cmd_dict = cmd_dict[part]
                if isinstance(cmd_dict, Mapping):
                    cmd_dict = SCPI_Path_Dict(cmd_dict)
        tree = ":".join(canonical)
        if part == "_":
            tree = ":".join(tree.split(":")[:-1])

        tree = tree.strip(":")
        return cmd_dict, tree, full_path

    def __getattr__(self, name):
        """See if we need to construct as sub-path or whether we have a terminal attribute."""
        try:
            return getattr(super(SCPI_Instrument_Mixin, self), name)
        except AttributeError as err:
            pass
        cmd_dict, tree, full_path = self._get_path(name)
        if isinstance(
            cmd_dict, Mapping
        ):  # Sub path returned so we're constructing an instance of ourselves from here.
            return _proxy(instr=self, path=full_path)
        if not isinstance(cmd_dict, Param):
            raise CommandError("Unrecognised command {}".format(tree))
        return cmd_dict.do_read(tree, self)

    def reset(self):
        """*RST"""
        self.write("*RST")

    def clear(self):
        """*CLS"""
        self.write("*CLS")

    def id_query(self):
        """Do a *IDN? and if self.id_pattern check if it matches."""
        ret = -self.IDN
        if hasattr(self, "id_pattern"):
            if re.compile(self.id_pattern).match(ret):
                return True
            else:
                return False
        else:
            return ret


class _proxy(object):

    """Proxy attribute access to build SCPI commands."""

    def __init__(self, instr=None, path=""):
        """Make sure I know what instrument I am and what my root is"""
        self._instr = instr
        self._path = path

    def _get_path(self, name):
        """Locate the current path in the command dictionary."""
        full_path = path.join(self._path, name)
        tree = full_path.replace(path.sep, ":")
        cmd_dict = self._instr.commands
        canonical = []
        for part in tree.split(":"):
            if part not in cmd_dict:
                raise AttributeError(
                    "{} not recognised by driver as a SCPI command!".format(tree)
                )
            else:
                part = cmd_dict.canonical(part)
                canonical.append(part)
                cmd_dict = cmd_dict[part]
                if isinstance(cmd_dict, Mapping):
                    cmd_dict = SCPI_Path_Dict(cmd_dict)
        tree = ":".join(canonical)
        if part == "_":
            tree = ":".join(tree.split(":")[:-1])
        tree = tree.strip(":")
        return cmd_dict, tree, full_path

    def __getattr__(self, name):
        """See if we need to construct as sub-path or whether we have a terminal attribute."""
        try:
            return super(_proxy, self).__getattr__(name)
        except AttributeError:
            pass
        cmd_dict, tree, full_path = self._get_path(name)
        if isinstance(
            cmd_dict, Mapping
        ):  # Sub path returned so we're constructing an instance of ourselves from here.
            return _proxy(instr=self._instr, path=full_path)
        if not isinstance(cmd_dict, Param):
            raise CommandError("Unrecognised command {}".format(tree))
        return cmd_dict.do_read(tree, self._instr)

    def __setattr__(self, name, value):
        """Set a SCIPI Command."""
        if name.startswith("_") and name != "_":
            super(_proxy, self).__setattr__(name, value)
            return None
        try:
            val = super(_proxy, self).__getattr__(name)
            super(_proxy, self).__setattr__(name, value)
            return None
        except AttributeError:
            pass
        name = name.upper()
        cmd_dict, tree, full_path = self._get_path(name)
        if not isinstance(cmd_dict, Param):
            raise CommandError(
                "Non terminal SCPI command path {} trying to be set a value of {}!".format(
                    tree, value
                )
            )
        self._instr.write(cmd_dict.format_write(tree, value))
