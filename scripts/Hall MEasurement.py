# -*- coding: utf-8 -*-
"""
Created on Sat Sep  7 13:06:02 2019

@author: phygbu
"""

from pyscpi.measurements.K6221_K2182 import Measurement

try:
    M = Measurement(
        mock=False, amplitude=1e-5, repeats=200, debug=True, delay=0.02
    )  # Mock mode stops us talking epics
    M.main_loop()
except KeyboardInterrupt:
    M.k6221.sour.cle.imm
    M.k6221.reset()
    M.k6221.close()  # Make sure we kill that telnet connection
    print("Finished Measuring")
