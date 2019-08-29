"""SCPI over telnet driver Module

This module provides several classes to support doing SCPI over telnet interfaces. It was hacked together to support the use of
a Keithley 6221 and 2182A for A STXM run in November 2018.

Author: Gavin Burnell, University of Leeds, g.burnell@leeds.ac.uk.
"""
from __future__ import print_function

import epics
import time
import numpy as np

from ..instr.keithley import K2182A, K6221

class Measurement(object):

    """Setup a Resitance measurement."""

    def __init__(self,*args,**kargs):
        """Setup my 6221 and 2182 instances."""

        self.k6221=K6221(debug=False,slow=0.0)
        self.k2182=K2182A(via_6221=self.k6221,debug=False,slow=0.0)
        self.repeats=kargs.pop("repeats",4)
        self.amplitude=kargs.pop("amplitude",1E-7)
        self.delay=kargs.pop("delay",0.2)
        self.compliance=kargs.pop("compliance",0.1)
        self.flag='X07DA-XTR-LOCKIN:MEASFLAG'
        self.prefix=kargs.pop('prefix','X07DA-XTR-LOCKIN:{}')
        self.poll_time=kargs.pop('poll_time',1.0)
        self.mock=kargs.pop("mock",False)
        debug=kargs.pop("debug",False)
        self.k6221.debug=debug
        self.k2182.debug=debug

    def post(self,results):
        """Scan the results dictionary for floats and post them on corresponding epics channels."""
        for k,v in results.items():
            if isinstance(v,float):
                epics.caput(self.prefix.format(k),float(v))
        epics.caput(self.flag,0)

    def wait_flag(self):
        """Wait for the epics flag to go high before releasing."""
        while epics.caget(self.flag)==0:
            time.sleep(self.poll_time)
        return True #should we return false for a tiemout? Should I have a timeout?

    def main_loop(self):
        """Execute a connect, confogure and then enter a loop waiting to do measurements."""
        self.connect()
        self.configure_delta()
        time.sleep(1) # Give us a chance to catch our breaths...
        while True: #Measure for ever
            if self.mock:
                time.sleep(5.0)
            else:
                self.wait_flag()
            try:
                results=self.measure_delta()
            except visa.VisaIOError:
                epics.caput(self.flag,-1)
                print("Aborting measurement due to VISA errors")
                break
            print("Results\n*******")
            for k,v in results.items():
                print("\t{} : {}\n".format(k,v))
            if not self.mock:
                self.post(results)

    def waveform(self,key):
        basis=np.ones(self.repeats*2)
        amp=basis*self.amplitude
        amp[::2]=-amp[::2]
        delay=basis*self.delay
        comp=basis*self.compliance
        ret={"values":amp,"delay":delay,"compliance":comp}
        return ret[key]

    def connect(self):
        if "6221" not in self.k6221.idn:
            raise RuntimeError("No 6221 !")
        self.k6221.sre=4 #sre - set service request
        if not self.k6221.sour.delt.nvpr: #checks if nVmeter present
            raise RuntimeError("2182 Not attached to the 6221")
        if "2182" not in self.k2182.idn:
            raise RuntimeError("2182A not communicated with!")
        self.k2182.reset()
        self.k6221.reset()
        self.k6221.clear() #reset status info
        self.k2182.clear()
        self.k2182.sre=4
        self.k6221.abort #if waiting for something - stop waiting for it
        self.k6221.outp.stat=False #turn output off (eqv to pressing button on current source under blue light)

    def config_buffer(self):
        self.k2182.trac.cle
        time.sleep(1) # Clear takes some time
        self.k2182.trac.feed.cont="NEXT"

    def configure(self):
        #Configure 2182
        self.k2182.abort
        self.k2182.sens.volt.chan1.ref._=0.0
        self.k2182.sens.volt.chan1.ref.stat=False
        self.k2182.sens.volt.chan1.rang.auto=False
        self.k2182.sens.volt.chan1.rang.upp=0.1
        self.k2182.sens.volt.dig=8
        self.k2182.sens.volt.nplc=1.0
        self.k2182.sens.hold.stat=False
        self.k2182.syst.lsyn.stat=False
        self.k2182.syst.faz.stat=True
        self.k2182.syst.azer.stat=True
        self.k2182.sens.volt.chan1.lpas.stat=False
        self.k2182.sens.volt.chan1.dfil.stat=False
        self.k2182.form.data="ASC"
        self.k2182.trig.sour="EXT"
        self.k2182.trig.coun=2*self.repeats
        self.k2182.trig.delay.auto=True
        self.k2182.trac.poin=2*self.repeats
        self.k2182.trac.feed._="SENS"
        self.k2182.trac.feed.cont="NEXT"
        self.config_buffer()
        self.k2182.init.cont=False


        #Now the 6221
        self.k6221.outp.lte=False
        self.k6221.outp.ish="OLOW"
        self.k6221.sour.swe.rang="BEST"
        self.k6221.sour.swe.spac="LIST"
        self.k6221.sour.swe.coun=1
        self.k6221.sour.list.curr=self.waveform("values")
        self.k6221.sour.list.delay=self.waveform("delay")
        self.k6221.sour.list.comp=self.waveform("compliance")
        self.k6221.sour.swe.cab=False
        self.k6221.trig.sour._="TLIN"
        self.k6221.trig.tcon.dir="SOUR"
        self.k6221.trig.tcon.asyn.outp="DEL"
        self.k6221.trig.tcon.asyn.ilin=1
        self.k6221.trig.tcon.asyn.olin=2
        self.k6221.sour.swe.arm

    def configure_delta(self):

        self.k2182.abort
        self.k2182.sens.volt.chan1.ref._=0.0
        self.k2182.sens.volt.chan1.ref.stat=False
        self.k2182.sens.volt.chan1.rang.auto=False
        self.k2182.sens.volt.chan1.rang.upp=0.1
        self.k2182.sens.volt.dig=8
        self.k2182.sens.volt.nplc=1.0 #powerline cycles to average over
        self.k2182.sens.hold.stat=False
        self.k2182.syst.lsyn.stat=False
        self.k2182.syst.faz.stat=True
        self.k2182.syst.azer.stat=True
        self.k2182.sens.volt.chan1.lpas.stat=False #low pass analogue filter off
        self.k2182.sens.volt.chan1.dfil.stat=False #digital filter off

        """Configure delta mode."""
        self.k6221.sour.cle.imm
        self.k6221.reset()
        self.k6221.sour.delt.high=self.amplitude
        self.k6221.sour.delt.low=-self.amplitude
        self.k6221.sour.delt.delay=self.delay #how long current is up and down for, diag p 88 6221 manual
        self.k6221.sour.delt.coun=self.repeats
        self.k6221.sour.swe.coun=1 #number of times to do said repeats
        self.k6221.sour.delt.cab=False #continue measuring even if it goes into compliance
        self.k6221.trac.cle
        self.k6221.trac.poin=self.repeats
        self.k6221.trac.feed._="SENS"
        self.k6221.trac.feed.cont="NEXT"
        self.k6221.sour.delt.arm

    def measure_delta(self):
        self.k6221.init.imm
        meas_event=self.k6221.stat.meas.even
        while not meas_event&264:
            if meas_event&8:
                raise MeasurementError("6221 in Compliance!")
            time.sleep(1)
            meas_event=self.k6221.stat.meas.even
        data=self.k6221.trac.data
        data=np.reshape(data,(data.size/2,2))
        res={}
        res["R_data"]=data[:,0]/self.amplitude
        res["t-Data"]=data[:,1]
        means=np.mean(data,axis=0)
        stds=np.std(data,axis=0)
        res["R_XY"]=means[0]/self.amplitude
        res["DR_XY"]=stds[0]/self.amplitude
        res["I_AMP"]=self.amplitude
        res["SAMPLENO"]=float(self.repeats)

        self.k6221.trac.cle
        self.k6221.trac.feed.cont="NEXT"
        return res

    def measure(self):
        try:
            self.k6221.clear
            self.k2182.init.imm
            self.k6221.init.imm
            while self.k6221.stat.oper.even&2:
                time.sleep(1)
            data=self.k2182.trac.data
            curr=self.waveform("values")
            resistance=data/curr
            res_mean=np.mean(resistance)
            res_std=np.std(resistance)
            self.config_buffer()
            ret={"V_data":data,
                 "I_data":curr,
                 "R_data":resistance,
                 "R_xy":res_mean,
                 "dR_xy":res_std,
                 "repeats":float(self.repeats),
                 "I_measure":float(self.amplitude),
                 }
        except visa.VisaIOError as err:
            if self.k6221.debug:
                print("DEBUG: Measurement aborted!")
            raise err
        return ret

    def turn_off(self):
              k6221.outp.stat=False





if __name__=="__main__":
    try:
        M=Measurement(mock=False,amplitude=1E-5,repeats=200,debug=True,delay=0.02) #Mock mode stops us talking epics
        M.main_loop()
    except KeyboardInterrupt:
        M.k6221.sour.cle.imm
        M.k6221.reset()
        M.k6221.close() #Make sure we kill that telnet connection
        print("Finished Measuring")
