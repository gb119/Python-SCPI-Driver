#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Exception classes for the pyscpi package

Created on Thu Aug 29 22:02:27 2019

@author: phygbu
"""

__all__ = ["CommandError", "MeasurementError"]


class CommandError(AttributeError):

    """Raised when there is a SCPI command error."""

    pass


class MeasurementError(RuntimeError):

    """Something bad happened!"""

    pass
