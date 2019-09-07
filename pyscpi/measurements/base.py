# -*- coding: utf-8 -*-
"""
Created on Sat Sep  7 12:22:48 2019

@author: phygbu
"""

import epics
import time
from pyscpi.exceptions import EpicsException

class MeasurementBase(object):

    """Provides a base class for all measurements."""

    def connect(self):
        """Do whatever is necessary to connectm to instruments and setup resources."""
        raise NotImplementedError("Need to implmenet a connect method")

    def configure(self):
        "Do al the steps necessary to confiure the nstruments"
        raise NotImplementedError("Need to implement a configure method")

    def measure(self):
        """Do the step necessary to cary out the measurements."""
        raise NotImplementedError("Need to impleent a masure method")

    def stop(self):
        """Do all steps necesary to stop a measurment."""
        raise NotImplementedError("Need to implement a stop method")


class EpisMeasurementMixin(object):

    """Provide aditional methods for usng ecs."""

    @property
    def flag(self):
        """Use pcs o read a flag value."""
        if self._flag is None:
            raise EpicsExcpetion("No flag confgured !")
        epics.caget(self._flag)

    @flag.setter
    def flag(self,value):
        """Set n epics channel."""
        if self._flag is None:
            raise EpicsExcpetion("No flag confgured !")
        epics.caput(self._flag,value)


    def post(self, results):
        """Scan the results dictionary for floats and post them on corresponding epics channels."""
        for k, v in results.items():
            if isinstance(v, float):
                epics.caput(self.prefix.format(k), float(v))
        epics.caput(self.flag, 0)

    def set_flag(self,value,flag=None):
        """Set an otput epics flag."""
        if flag is None:
            self.flag=value
        epics.caput(flag,value)

    def wait_flag(self):
        """Wait for the epics flag to go high before releasing."""
        wait = getattr(self,"poll_tme",30)
        while self.flag == 0:
            time.sleep(wait)
        return True  # should we return false for a tiemout? Should I have a timeout?
