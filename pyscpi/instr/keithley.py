#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Keithley Instrument Drivers

Created on Thu Aug 29 23:05:22 2019

@author: phygbu
"""

from ..base import SCPI_Instrument_Mixin,SCPI_Path_Dict,Param

class K6221(SCPI_Instrument_Mixin,GPIBInstrument):

    """Will handle a K6221/K2182A combo.

    This is a simple instrument since we just talk directly to it via GPIB."""

    commands=SCPI_Path_Dict({"ABORT":Param(),
              "FORMAT":{
                        },
              "SOUR":{"DELT":{"NVPR":Param(bool,None),
                              "HIGH":Param(float,float),
                              "LOW":Param(float,float),
                              "DELAY":Param(float,float),
                              "COUN":Param(int,int),
                              "CAB":Param(bool,bool),
                              "CSW":Param(bool,bool),
                              "ARM":Param(None,None),
                               },
                      "SWE":{"RANG": Param(str,str),
                             "SPAC":Param(str,str),
                             "COUN": Param(int,int),
                             "CAB": Param(bool,bool),
                             "ARM": Param(None,None),
                             },
                      "LIST":{"CURR":Param(None,np.zeros(100)),
                              "DELAY":Param(None,np.zeros(100)),
                              "COMP":Param(None,np.zeros(100)),
                              },
                      "WAVE": {"EXTR":{"ILIN": Param(int,int),
                                      },
                               "PMAR":{"OLIN":Param(int,int),
                                      },
                               },
                      "CLE": {"IMM":Param(None,None),},
                  },
              "INIT": { "IMM": Param(None,None),
                      },
              "OUTP":{"STAT": Param(bool,bool),
                      "LTE": Param(bool,bool),
                      "ISH": Param(str,str),
                    },
              "STAT":{"OPER":{"ENAB": Param(int,int),
                              "EVEN": Param(int,None),
                              "COND": Param(int,None),
                             },
                    "MEAS":{"ENAB": Param(int,int),
                              "EVEN": Param(int,None),
                              "COND": Param(int,None),
                             },
                    },
              "SYST": {"SER": {"SEND": Param(None,str),
                               "ENT":Param(str,None),
                              },
                      "ERR":{"_":Param(str,None),
                             "CLE":Param(None,None),
                                        },
                      },
              "TRIG": {"SOUR":{"_":Param(str,str),
                              "DIR": Param(str,str),},
                       "TCON":{"DIR":Param(str,str),
                               "ASYN": {"OUTP":Param(str,str),
                                        "ILIN": Param(int,int),
                                        "OLIN":Param(int,int),

                                       },
                               },
                      },
              "TRAC":{"CLE":Param(None,None),
                      "POIN":Param(int,int),
                      "FEED":{"_":Param(str,str),
                              "CONT":Param(str,str),
                             },
                      "DATA":Param(np.ndarray([]),None),
                      "FREE":Param(int,None)
                      },

            })

    pass

class K2182A(SCPI_Instrument_Mixin,GPIBInstrument):

    """Will handle a K2182A optionally using a K6221 instance to talk through"""

    def __init__(self,*args,**kargs):
        """Grab a via_6221 karg before calling super.

        Keyword Arguments:
            via_6221 (K6221, or False): A K6221 instance to talk throigh.
        """
        self._6221=kargs.pop("via_6221",K6221())
        super(K2182A,self).__init__(*args,**kargs)

    def write(self,command,close=True):
        """Wrap command if calling through a 6221."""
        if self._6221: #pass comms to 6221 instance
            command='SYST:COMM:SER:SEND "{}"'.format(command)
            return self._6221.write(command,close=close)
        return super(K2182A,self).write(command,close=close)

    def _read(self):
        self._6221.write("SYST:COMM:SER:ENT?",close=False)
        return self._6221.read(close=False).strip()

    def read(self,close=True):
        """If using a 6221, send the 6221 serial comms command to get data and then listen."""
        if self._6221: #Patching comms through the 6221 instance
            buf=self._read()
            while buf=="":
                buf=self._read()
            overall_buf=buf
            buf=self._read()
            while buf!="":
                overall_buf+=buf
                buf=self._read()
            if close:
                self._6221.close()
            return overall_buf.strip()
        else:
            return super(K2182A,self).read(close=close)

    commands=SCPI_Path_Dict({"SENS":{"VOLT":{"CHAN1":{"REF":{"_":Param(float,float),
                                                      "STAT":Param(bool,bool),
                                                     },
                                                      "RANG":{"AUTO":Param(bool,bool),
                                                              "UPP":Param(float,float)
                                                    },
                                                       "LPAS":{"STAT":Param(bool,bool),},
                                                       "DFIL":{"STAT":Param(bool,bool),
                                                               "WIND":Param(float,float),
                                                               "TCON":Param(str,str),
                                                               "COUN":Param(int,int),
                                                              },
                                      },
                              "DIG":Param(int,int),
                              "NPLC":Param(float,float),

                             },
                      "HOLD":{"STAT":Param(bool,bool),
                              "WIND":Param(float,float),
                              "COUN":Param(int,int),
                             },
                    },
              "FORM":{"DATA":Param(str,str),
                      "BORD":Param(str,str),
                      "ELEM":Param(str,str),
                      },
              "SYST":{"LSYN":{"STAT":Param(bool,bool),},
                      "FAZ":{"STAT":Param(bool,bool),},
                      "AZER":{"STAT":Param(bool,bool),},
                      "ERR":{"_":Param(str,None),
                             "CLE":Param(None,None),
                              },
                     },
              "TRIG":{"SOUR":Param(str,str),
                      "COUN":Param(str,str),#Allow INF
                      "DELAY":{"_":Param(float,float),
                             "AUTO":Param(bool,bool),
                            },
                      "TIM":Param(float,float),
                      },
              "TRAC":{"CLE":Param(None,None),
                      "POIN":Param(int,int),
                      "FEED":{"_":Param(str,str),
                              "CONT":Param(str,str),
                             },
                      "DATA":Param(np.ndarray([]),None),
                      "FREE":Param(int,None)
                      },
                "INIT":{"IMM":Param(None,None),
                        "CONT":Param(bool,bool),
                    },
                "ABORT":Param(None,None),
            })
