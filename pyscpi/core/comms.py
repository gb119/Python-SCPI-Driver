#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Base classes that handle communications with instruments.

Created on Thu Aug 29 22:28:36 2019

@author: phygbu
"""
from __future__ import print_function

__all__=["GPIBInstrument","TelnetInstrument"]
import sys
import time


_global_rm = None #Store a global via resource manager

if sys.version_info[0]==3:
    raw_input=input #Hack to set up raw_input correctly


def initResourceManager():
	import visa
	rm = visa.ResourceManager()
	return rm

def initGPIBInstrument(rm, resource):
	# Initializes the VISA GPIB resource
	try:
			instr = rm.open_resource(resource)
	except:
			print("ERROR - Non existing resource >>> "+resource)
			return None

	return instr

class InstrumentComms(object):

    """Abstract base class for Instrument communications.

    This just defines the interface routines that all communications layers should support."""

    def __init__(*args,**kargs):

        self._wait=kargs.pop("wait",0.5)
        self.debug=kargs.pop("debug",False)
        self.slow=kargs.pop("slow",0.0)

    def close(self):
        """Close our connection."""
        raise NotImplementedError("Communications drivers need to specify a close method")

    def read(self,close=True):
        """Read a string back from the iinstrument."""
        raise NotImplementedError("Communications drivers need to specify a read method")

    def trans(self,command,close=True):
        """Do a Write-Read transaction"""
        raise NotImplementedError("Communications drivers need to specify a trans(action) method")

    def wait(self,wait=None):
        """Wait for a delay period.

        Keyword Args:
            wait (float, None): Ov erride the default delay.
        """
        if wait is None:
            wait=self._wait
        if self.slow:
            if isinstance(self.slow,bool):
                raw_input("Press Return to continue...")
            else:
                wait=wait*self.slow
        time.sleep(wait)

    def write(self,command,close=True):
        """Send a string to the instrument via network port."""
        raise NotImplementedError("Communications drivers need to specify a write method")


class GPIBInstrument(InstrumentComms):

    """Wrapper around visa for GPIB instrument."""

    def __init__(self,rm=None, instr='GPIB0::16::INSTR',**kargs):
        if rm is None:
            global _global_rm
            if _global_rm is Noine:
                _global_rm = initGPIBInstrument()
            rm = _global_rm

        self._instr = initGPIBInstrument(rm,instr)
        self.ip=instr
        self.port=""

        super(GPIBInstrument,self).__init__(**kargs)

    def __del__(self):
        """Make sure we close our telent connection."""
        self.close()

    def write(self,command,close=True):
        """Send a string to the instrument via network port."""
        if self.debug:
            print("DEBUG {}:{} Write :{}".format(self.ip,self.port,command))
        else:
            if self.slow:
                self.wait()
        command=command.strip()
        self._instr.write(command)
        if self.slow:
            self.wait()
        if close:
            self.close()

    def read(self,close=True):
        """Read a string back from the iinstrument."""
        buf=""
        while True:
            self.wait()
            buf+=self._instr.read()
            if len(buf)>0 and buf[-1]=="\n":
                break
        if self.debug:
            print("DEBUG {}:{} Read :{}".format(self.ip,self.port,buf))
        buf=buf.strip()
        if close:
            self.close()
        return buf

    def trans(self,command,close=True):
        """Do a Write-Read transaction"""
        self.write(command,close=False)
        return self.read(close=close)

    def close(self):
        """Close our connection."""
        if self.close:
            pass
        #self._connection=None #Fake close

class TelnetInstrument(InstrumentComms):

    def __init__(self, ip="129.129.113.82",port=1394,**kargs):
        """Open a TCPIP connection to an instrument.

        Args:
            ip (str): IP address
            port (int): TCPIP port

        Keyword Arguments:
            wait(float): Delay after sending a command for the instrument to respond
            debug(bool): Turn on debugging information
            slow(float): Multiplier for wait to make everything really slow down

        This will set the ip and port instance variables."""
        self.ip=ip
        self.port=int(port)
        self._connection=None
        self._wait=kargs.pop("wait",0.5)
        self.debug=kargs.pop("debug",False)
        self.slow=kargs.pop("slow",0.0)

    def __del__(self):
        """Make sure we close our telent connection."""
        self.close()

    @property
    def connection(self):
        """Maintain a connection to the IP/port"""
        if self._connection is None:
            self._connection=telnetlib.Telnet(self.ip,self.port)
        return self._connection

    def write(self,command,close=True):
        """Send a string to the instrument via network port."""
        if self.debug:
            print("DEBUG {}:{} Write :{}".format(self.ip,self.port,command))
        else:
            if self.slow:
                self.wait()
        if command[-1]!="\n":
            command+="\n"
        self.connection.write(command)
        if self.slow:
            self.wait()
        if close:
            self.close()

    def read(self,close=True):
        """Read a string back from the iinstrument."""
        buf=""
        try:
                while True:
                    self.wait()
                    buf+=self.connection.read_eager()
                    if len(buf)>0 and buf[-1]=="\n":
                        break
                if self.debug:
                    print("DEBUG {}:{} Read :{}".format(self.ip,self.port,buf))
        except visa.VisaIOError as err:
                if self.debug:
                    print("DEBUG: VISA IO Error! {}".format(err))
                raise err
        buf=buf.strip()
        if close:
            self.close()
        return buf

    def trans(self,command,close=True):
        """Do a Write-Read transaction"""
        self.write(command,close=False)
        return self.read(close=close)

    def close(self):
        """Close our connection."""
        if self._connection is not None:
            self.connection.close()
        self._connection=None
