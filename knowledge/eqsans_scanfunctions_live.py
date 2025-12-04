# Beamline-6 EQ-SANS C Do
from epics import caget, caput, PV, cainfo
from scan import *
import os
import sys
import time
import traceback
from datetime import datetime, timedelta
# from script.ScriptUtils.ScriptOperations import ScriptCommandSetScanTitle
# import savevalue
sys.path.append('/home/controls/share/master/python/Util')
from Autosave import Autosave

cmds = []
tot_cmds = []
#client = ScanClient('bl6-dassrv1.sns.gov')
client = ScanClient('10.111.12.130')
pctotal = 0.0
timetotal = 0
gsimulate = False
this_name= os.path.basename(sys.argv[0])

def getfuncname():
    stack = traceback.extract_stack()
    (filename, line, procname, text) =stack[-1]
    return procname
    
def beamstopX(pos):
    # this function move beamstop x-position. regardless of size of the beamstops.
    scantitle = 'beamstopX('+str(pos)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:beamstopX', pos, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def beamstopY30(pos):
    # this function move the 30mm beamstop y-position
    scantitle = 'beamstopY30('+str(pos)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:beamstopY30', pos, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def beamstopY60(pos):
    scantitle = 'beamstopY60('+str(pos)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:beamstopY60', pos, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def beamstopY90(pos):
    scantitle = 'beamstopY90('+str(pos)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:beamstopY90', pos, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def beamslit1(slitname):
    if slitname in ["d26_NoCd", "d25_Cd","d10_Cd", "d25mm", "d20mm", "d15mm", "d10mm", "d5mm"]:
        scantitle = 'beamslit1'+ slitname +')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Mot:beamslit1:Menu', slitname, completion = True))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()
    else:
        raise Exception("BL6-ScriptError: Cannot find the variable name : " + slitname)

def movebeamslit1(value):
    scantitle = 'movebeamslit1(' + str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:beamslit1', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
    
def beamslit2(slitname):
    if slitname in ["d25_NoCd", "d20_Cd", "d25mm", "d20mm", "d15mm", "d10mm", "d5mm"]:
        scantitle = 'beamslit2('+slitname+')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Mot:beamslit2:Menu', slitname, completion = True))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()
    else:
        raise Exception("BL6-ScriptError: Cannot find the variable name : " + slitname)

def beamslit3(slitname):
    if slitname in ["d25_NoCd", "d20_Cd", "d25mm", "d20mm", "d15mm", "d10mm", "d5mm"]:
        scantitle = 'beamslit3('+ slitname +')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Mot:beamslit3:Menu', slitname, completion = True))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()
    else:
        raise Exception("BL6-ScriptError: Cannot find the variable name : " + slitname)

def beamslit4(slitsize):
    scantitle = 'beamslit4('+str(slitsize)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:CS:beamslit4', slitsize))
    scantitle = 'beamslit4('+str(slitsize)+')'
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


def setWL(wl):
    # this function is used to change wavelength band. defined by the 
    # minimum wavelength of the band
    scantitle = 'setWL('+str(wl)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Chop:Skf14:InitWvlenReq', wl, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def closeShutter():
    #close secondary shutter. before changing sample, makesure this shutter is closed.
    scantitle = 'closeShutter()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:shutter:SFWMoveShutter', 'Closed', completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def openShutter():
    # open secondary shutter. allow neutron beam on sample
    scantitle = 'openShutter()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:shutter:SFWMoveShutter', 'Open', completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def movedetector(detz):
    # use this function to move detector to designated sample-to-detector distance.
    # value is in mm. for example 4m is 4000.
    scantitle = 'movedetector('+str(detz) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:detectorZ', detz, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def movemask(value):
    scantitle = 'movemask('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:mask', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
def chopperfreq(hz):
    # setting chotter  frequency either 30hz or 60hz. 
    # frame-skipping mode os 30hz. typical operation is 60hz
    scantitle = 'chopperfreq('+str(hz) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Chop:Skf14:SpeedReq', hz, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


def set_chopper_delay(chopper, value):
    #this command can be used to set chopper phase individually 
    # for custom defined wavelength band. or making monochromatic beam
    scantitle = 'set_chopper_delay('+str(chopper)+', '+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    if chopper ==1 :
        cmds.append(Set('BL6:Chop:Skf1:OpModeSet', 0, completion=True))
        cmds.append(Set('BL6:Chop:Skf1:PhaseTimeDelaySet', value, completion=True, readback=True, tolerance=10))
    elif chopper == 2: 
        cmds.append(Set('BL6:Chop:Skf2:OpModeSet', 0, completion=True))
        cmds.append(Set('BL6:Chop:Skf2:PhaseTimeDelaySet', value, completion=True, readback=True, tolerance=10))
    elif chopper ==3:
        cmds.append(Set('BL6:Chop:Skf3:OpModeSet', 0, completion=True))
        cmds.append(Set('BL6:Chop:Skf3:PhaseTimeDelaySet', value, completion=True, readback=True, tolerance=10))
    elif chopper ==4:
        cmds.append(Set('BL6:Chop:Skf4:OpModeSet', 0, completion=True))
        cmds.append(Set('BL6:Chop:Skf4:PhaseTimeDelaySet', value, completion=True, readback=True, tolerance=10))
    else:
        print("CHECK: which chopper phase ??? ")
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def set_choppers_auto():
    # if default values for chopper phase is needed, use this command
    scantitle = 'set_choppers_auto()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Chop:Skf1:OpModeSet', 1, completion=True))
    cmds.append(Set('BL6:Chop:Skf2:OpModeSet', 1, completion=True))
    cmds.append(Set('BL6:Chop:Skf3:OpModeSet', 1, completion=True))
    cmds.append(Set('BL6:Chop:Skf4:OpModeSet', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


###############
# Sample Environment
###############

def movetransx(value):
    scantitle = 'movetransx('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:transX', value, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
def movetransz(value):
    # move sample table transx motor
    scantitle = 'movetransz('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:transZ', value, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
        
def moveroth(value):
    # move rotation stage. hRotStage.
    scantitle = 'moveroth('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:hRotStage', value, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
def tumbler(args):
    # set tumbler on or off
    # the value is string on or off.
    if args.lower() == 'on' or args.lower() == 'start' :
        scantitle = 'tumbler('+ args + ')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Mot:tumblerRot:StartRot.PROC', 1, completion = False))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()        
    elif args.lower() == 'off' or args.lower() =='stop':
        scantitle = 'tumbler('+ args + ')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Mot:tumblerRot.STOP', 1, completion = False))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()
    else:
        raise Exception("BL6-ScriptError: unknown arguments. (start, stop, on, off)")

def sethaaketemp(value):
    scantitle = 'sethaaketemp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:HAAKE:WriteSetPointTemp', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def setpeltier1temp(value):
    # setting peltier 1 temperature. unit is C. for higher than 80C, it is more
    # efficient to set polysci temperature to be max. such as 60C
    scantitle = 'setpeltier1temp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:QNTC1:WriteTargetTemp', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def setpeltier2temp(value):
    scantitle = 'setpeltier2temp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:QNTC2:WriteTargetTemp', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
        
def settumblertemp(value):
    # tumbler temperature can be set using this command
    scantitle = 'settumblertemp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:TUMBLER:SP', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

# furnace temperature control
def setfurnacetemp(value):
    scantitle = 'setfurnacetemp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:FURNACE:SP', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

# high temperature furnace control
def sethtfurnacetemp(value):
    scantitle = 'sethtfurnacetemp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:NDBLS:Loop1:SPSet', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def rheotrigger():
    scantitle = 'rheotrigger()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:Rheometer:setRelay1BO', 1, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 

def set_tensileg_gap(value):
    # tensile stage command. but use with care. check with IS.
    # caput('BL6:SE:NEWMARK:GAP', gap_sp, wait=True)
    gap_sp = value * 400 # dist is mm, gap_sp is number of steps
    scantitle = 'set_tensileg_gap('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:NEWMARK:GAP', gap_sp, completion=True))
    cmds.append(Delay(1))
    cmds.append(Set('BL6:SE:NEWMARK:COMMANDS', 5, completion=False, readback=True))
    cmds.append(Delay(2))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def set_tensileg_move(value):
    # tensile stage command. but use with care. check with IS.
    # caput('BL6:SE:NEWMARK:GAP', gap_sp, wait=True)
    together_sp = value * 400 *2 # dist is mm, gap_sp is number of steps
    scantitle = 'set_tensileg_gap('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:NEWMARK:TogetherSP', together_sp, completion=True))
    cmds.append(Delay(1))
    cmds.append(Set('BL6:SE:NEWMARK:COMMANDS', 8, completion=False, readback=True))
    cmds.append(Delay(2))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()



def set_field(value):
    # you can deduce what this function does based on the code, function name, and the PV name.
    scantitle = 'set_field('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:MagH:SP', value, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
 
def set_field_wait(value):
    # you can deduce what this function does based on the code, function name, and the PV name.
    scantitle = 'set_field_wait('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:MagHCB:SPSet', value, completion=True, readback=True, tolerance=0.002 ))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
 
def set_freq_wait(value):
    # you can deduce what this function does based on the code, function name, and the PV name.
    scantitle = 'set_freq_wait('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SRSWG:FreqSP', value, completion=True, readback=True, tolerance=1000 ))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    

def set_amp_wait(value):
    # you can deduce what this function does based on the code, function name, and the PV name.
    scantitle = 'set_amp_wait('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SRSWG:AmplSP', value, completion=True, readback=True, tolerance=0.02 ))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


##################################
# Added 8/2/2023 - Gergely Nagy
# for IPTS-30410

def setteledynepressure(value):
    scantitle = 'setteledynepressure('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:TD1:PressSet', value, completion = True))
    
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 

def runteledynepump():
    scantitle = 'runteledynepump'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:TD1:Run', 1, completion=True)) 
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 

def stopteledynepump():
    scantitle = 'stopteledynepump'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:TD1:Stop', 1, completion=True)) 
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 


##################################
# Added 12/2/2019 - William Heller
# BL6:SE:Cryo:Temp:SETP_S2 is input B for ipts-25381
def set_cryostat_vti(value):
    # setting crystat temperature using the vti probe
    scantitle = 'set_cryostat_vti('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S1', value, completion=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def set_cryostat_vti_wait(value):
    # set temperature of cryostat and wait until it reaches the target
    scantitle = 'set_cryostat_vti('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    #cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S1', value, completion=True, readback=True, tolerance=0.10))
    cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S1', value, completion=True, readback=True, tolerance=1.00))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def set_cryostat_sample(value):
    # set cryostat temperature. use the sample temperature as set point.
    scantitle = 'set_cryostat_sample('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S2', value, completion=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def set_cryostat_sample_wait(value):
    # set cryostat temperature and wait until it reaches the temperature
    scantitle = 'set_cryostat_sample('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    #cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S2', value, completion=True, readback=True, tolerance=0.10))
    cmds.append(Set('BL6:SE:Cryo:Temp:SETP_S2', value, completion=True, readback=True, tolerance=1.00))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
##################################

##################################
# Added 12/18/2019 - C Do
# HOT-024 furnace control
def set_furnace_temp(value):
    scantitle = 'set_furnace_temp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:NDBLS:Loop1:SPSet', value, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
##################################

##################################
# Added 1/17/19 - W Heller
# Polyscience Chiller
def set_polysci_temp(value):
    scantitle = 'set_polysci_temp('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:PolyScience:SPWrite', value, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
##################################


###############################
# cryostat stick rotation stage
# Added 11/3/2020 - W. Heller
###############################
# the PV is BL6:Mot:Sample:Axis1
def rotate_cryob(value):
    scantitle = 'rotate_cryob('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:Mot:Sample:Axis1', value, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
###############################



##################################
# Added 8/24/2021 - C Do
# sliding shearcell by yangyang wang
def sc_stop():
    scantitle = 'sc_stop()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SC:Mot:Main:SetState', 0, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def sc_setmanual():
    scantitle = 'sc_setmanual()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SC:Mot:Main:SetState', 1, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def sc_setcycle():
    scantitle = 'sc_setcycle()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SC:Mot:Main:SetState', 2, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()




def sc_setspeed(value):
    scantitle = 'sc_setspeed(' + str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:SE:SC:Mot:Cycle:Speed', value, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


##################################







##################################
# Added 1/20/2023 - G Nagy & C Do
# power outlet switch

def outletswitch(args):
    if args.lower() == 'on' or args.lower() == 'start' :
        scantitle = 'outletswitch('+ args + ')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Sample:OutletSwitch', 1, completion = False))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan() # clears the cmds array       
    elif args.lower() == 'off' or args.lower() =='stop':
        scantitle = 'outletswitch('+ args + ')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set('BL6:Sample:OutletSwitch', 0, completion = False))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()
    else:
        raise Exception("BL6-ScriptError: unknown arguments. (start, stop, on, off)")
##################################






##################################
# Added 1/21/2022 - C Do
# psylotech tensile stage
def psylo_tension_step(speed=0.1, dist=1, selector='both'):
    scantitle = 'psylo_tension_step(' + str(speed) + ', ' + str(dist) + ', ' + str(selector) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 

    if selector == 'primary' :
        cmds.append(Set('BL6:SE:PsyloTech:AxisSelector', 0, completion=False, readback=False))
    elif selector == 'secondary' :
        cmds.append(Set('BL6:SE:PsyloTech:AxisSelector', 1, completion=False, readback=False))
    else :
        cmds.append(Set('BL6:SE:PsyloTech:AxisSelector', 2, completion=False, readback=False))
    cmds.append(Delay(1))
    cmds.append(Set('BL6:SE:PsyloTech:MoveSpeed', speed, completion=False, readback=False))
    cmds.append(Delay(1))
    cmds.append(Set('BL6:SE:PsyloTech:StepDistance', dist, completion=False, readback=False))
    cmds.append(Delay(2))
    cmds.append(Set('BL6:SE:PsyloTech:TensionStep', 1, completion=False, readback=False))
    cmds.append(Delay(float(dist/speed + 2)))
    cmds.append(Set('BL6:SE:PsyloTech:STOP', 1, completion=False, readback=False))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
	




##################################



##############
# SCAN CONTROL
##############
    

def delay(time):
    global timetotal
    timetotal = timetotal + time
    scantitle = 'delay('+str(time) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Delay(time))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def newscan():
    global cmds
    # print "...Resetting cmds for a new scan."
    cmds = []


def setipts(value):
    scantitle = 'setipts('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:CS:IPTS', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 

def setitems(value):
    scantitle = 'setitems('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:CS:ITEMS', value, completion = True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 
    
#############################
# added 11/3/2020 - W. Heller
#############################
def setruntitle(title):
    scantitle = 'setruntitle('+str(title)+')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle ))  
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))  
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan() 
#############################


def submit(scantitle=os.path.basename(sys.argv[0])):
    print "...Submitting scan : " + scantitle
    cmds.append(Set('BL6:CS:LineLog:Add', 'submit(' + scantitle + ')' )) 
    id = submitsmart(cmds, scantitle)
    print "...scan id = " + str(id)
    newscan()  # after submission, reset the cmds variable

def start():
    scantitle = 'start()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

def stop():
    scantitle = 'stop()'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


def waitPC(value):
    global pctotal
    pctotal = pctotal + value
    scantitle = 'waitPC('+str(value) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    cmds.append(Wait('BL6:Det:PCharge:C', value, comparison='increase by'))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()



def runsample(title, racktype, timetype, pos, limit):
    global pctotal, timetotal
    scantitle = 'runsample('+title + ', ' + racktype + ', ' + timetype + ', ' + str(pos) + ', ' + str(limit) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))

    if racktype == 'tumbler':
        print "...Set tumbler for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 1, completion=True))
    elif racktype == 'banjo':
        print "...Set banjo for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 2, completion=True))
    elif racktype == 'peltier':
        print "...Set peltier for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 3, completion=True))
    elif racktype == 'ti':
        print "...Set ti rack for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 4, completion=True))
    elif racktype == 'humid':
        print "...Set humidity cell for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 5, completion=True))
    else: 
        raise Exception("unknown sample environment type")        
    if pos > 0 :
        cmds.append(Set('BL6:Mot:SampleTable:Menu', pos, completion=True))
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))

    if timetype == 'pc' or timetype == 'PC':
        cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
        pctotal = pctotal + limit
    elif timetype.lower() == 'time':
        cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
        timetotal = timetotal + limit
    else:
        raise Exception("unknown time type")   
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))

    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()


#sampleid is the ITEMS number of the sample
def runsampleid(title, sampleid,  racktype, timetype, pos, limit):
    global pctotal, timetotal
    scantitle = 'runsample('+title + ', ' + str(sampleid) + ', ' + racktype + ', ' + timetype + ', ' + str(pos) + ', ' + str(limit) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))
    cmds.append(Set('BL6:CS:ITEMS', sampleid, completion = True))

    if racktype == 'tumbler':
        print "...Set tumbler for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 1, completion=True))
    elif racktype == 'banjo':
        print "...Set banjo for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 2, completion=True))
    elif racktype == 'peltier':
        print "...Set peltier for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 3, completion=True))
    elif racktype == 'ti':
        print "...Set ti rack for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 4, completion=True))
    elif racktype == 'humid':
        print "...Set humidity cell for transX"
        cmds.append(Set('BL6:Mot:SampleTable:FillMenu', 5, completion=True))
    else: 
        raise Exception("unknown sample environment type")        
    if pos > 0 :
        cmds.append(Set('BL6:Mot:SampleTable:Menu', pos, completion=True))
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))

    if timetype == 'pc' or timetype == 'PC':
        cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
        pctotal = pctotal + limit
    elif timetype.lower() == 'time':
        cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
        timetotal = timetotal + limit
    else:
        raise Exception("unknown time type")   
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))

    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
    
    
    


# added 10/31/17 - William Heller and Chris Stanley.  Happy Halloween, Changwoo!

def runfurnace(title, timetype, pos, limit):
    global pctotal, timetotal
    scantitle = 'runfurnace('+title + ', ' + timetype + ', ' + str(pos) + ', ' + str(limit) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))
    cmds.append(Set('BL6:Mot:FurnaceTable:Menu', pos, completion=True))
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
    
    if timetype == 'pc' or timetype == 'PC':
        cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
        pctotal = pctotal + limit
    elif timetype.lower() == 'time':
        cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
        timetotal = timetotal + limit
    else:
        raise Exception("unknown time type")   
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

# added 10/28/20 Changwoo
# this is old eq-sans furnace sample environment runsample command
# runsampleid command designed for eq-sans furnace sample environment
def runfurnaceid(title,sampleid, timetype, pos, limit):
    global pctotal, timetotal
    scantitle = 'runfurnaceid('+title + ', ' + timetype + ', ' + str(pos) + ', ' + str(limit) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))
    cmds.append(Set('BL6:CS:ITEMS', sampleid, completion = True))
    cmds.append(Set('BL6:Mot:FurnaceTable:Menu', pos, completion=True))
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
    
    if timetype == 'pc' or timetype == 'PC':
        cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
        pctotal = pctotal + limit
    elif timetype.lower() == 'time':
        cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
        timetotal = timetotal + limit
    else:
        raise Exception("unknown time type")   
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()

##################################
# Added 12/2/2019 - William Heller
def runcryostat(title, timetype, limit):
    global pctotal, timetotal
    scantitle = 'runcryostat('+title + ', ' + timetype + ', ' + str(limit) + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        
    cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title))
    cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
    
    if timetype == 'pc' or timetype == 'PC':
        cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
        pctotal = pctotal + limit
    elif timetype.lower() == 'time':
        cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
        timetotal = timetotal + limit
    else:
        raise Exception("unknown time type")   
    cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()
##################################

def loadconf(file_name):
    config_path = "/home/controls/var/QRangeConfigurations/" + file_name
    print "...Use conf file " + config_path
    ( config_dir, config_file ) = os.path.split(config_path)
    ( config_ioc, config_ext ) = os.path.splitext(config_file)
    config = Autosave(path=config_dir, ioc=config_ioc, prefix="")
    #print config
    #print config.settings
    scantitle = 'loadconf('+file_name + ')'
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
    
    # remove unnecessary PVs
    config.delete('BL6:CS:QPlan:Comment')
    config.delete('BL6:CS:QPlan:BSforQ')

    # scattering
    if config_ioc.endswith('_scatt'):
        cmds.append(Comment('Set scattering configuration.'))
        cmds.append(Set('BL6:Mot:shutter:SFWMoveShutter', 2, completion=True))
        cmds.append(Set('BL6:Mot:detectorZ', config.settings['BL6:CS:QPlan:SampleDetDistance'], completion=True))
        cmds.append(Set('BL6:Chop:Skf14:SpeedEnum', config.settings['BL6:CS:QPlan:Freq'], completion=True))  # same enum/order in Q Planner
        cmds.append(Parallel(
            Set('BL6:Chop:Skf14:InitWvlenReq', config.settings['BL6:CS:QPlan:WLMin'], completion=True),

            Set('BL6:Mot:beamslit1:Menu', config.settings['BL6:CS:QPlan:S1s'], completion=True), # same enum order in Q Planner
            Set('BL6:Mot:beamslit2:Menu', config.settings['BL6:CS:QPlan:S2s'], completion=True), # same enum order in Q Planner
            Set('BL6:Mot:beamslit3:Menu', config.settings['BL6:CS:QPlan:S3s'], completion=True), # same enum order in Q Planner
            Set('BL6:CS:beamslit4', config.settings['BL6:CS:QPlan:S4'], completion=True),

            Set('BL6:Mot:beamstopX', config.settings['BL6:CS:QPlan:BSX'], completion=True),
            Set('BL6:Mot:beamstopY30', config.settings['BL6:CS:QPlan:BS30Ys'], completion=True),
            Set('BL6:Mot:beamstopY60', config.settings['BL6:CS:QPlan:BS60Ys'], completion=True),
            Set('BL6:Mot:beamstopY90', config.settings['BL6:CS:QPlan:BS90Ys'], completion=True),
            
            Set('BL6:CS:DataType', 0)
            ))
            
    # transmission
    elif config_ioc.endswith('_trans'):
        cmds.append(Comment('Set transmission configuration.'))
        cmds.append(Set('BL6:Mot:shutter:SFWMoveShutter', 2, completion=True))
        cmds.append(Set('BL6:Mot:detectorZ', config.settings['BL6:CS:QPlan:SampleDetDistance'], completion=True))
        cmds.append(Set('BL6:Chop:Skf14:SpeedEnum', config.settings['BL6:CS:QPlan:Freq'], completion=True)) # same enum/order in Q Planner
        cmds.append(Parallel(
            Set('BL6:Chop:Skf14:InitWvlenReq', config.settings['BL6:CS:QPlan:WLMin'], completion=True),
            Set('BL6:Mot:beamslit1:Menu', config.settings['BL6:CS:QPlan:S1t'], completion=True), # same enum order in Q Planner
            Set('BL6:Mot:beamslit2:Menu', config.settings['BL6:CS:QPlan:S2t'], completion=True), # same enum order in Q Planner
            Set('BL6:Mot:beamslit3:Menu', config.settings['BL6:CS:QPlan:S3t'], completion=True), # same enum order in Q Planner
            Set('BL6:CS:beamslit4', config.settings['BL6:CS:QPlan:S4'], completion=True),

            Set('BL6:Mot:beamstopX', config.settings['BL6:CS:QPlan:BSX'], completion=True),
            Set('BL6:Mot:beamstopY30', config.settings['BL6:CS:QPlan:BS30Yt'], completion=True),
            Set('BL6:Mot:beamstopY60', config.settings['BL6:CS:QPlan:BS60Yt'], completion=True),
            Set('BL6:Mot:beamstopY90', config.settings['BL6:CS:QPlan:BS90Yt'], completion=True),
            Set('BL6:CS:DataType', 1)
            ))
    else:
        raise Exception("unknown configuration type")
        # shouldn't proceed by just ignoring this problem
    id = submitsmart(cmds, scantitle)
    print(scantitle)
    newscan()



def maghscanup(startvalue, endvalue, step, waittime, title, timetype, limit):
    '''
    Perform data collection by changing magh field from startvalue to endvalue (kG) by step (kG)
    title is used as a basename.

    PV limit value check is not currently performed here. 
    Once we decide which algorithm to use for checking, this can be implemented easily.
    '''
    global pctotal, timetotal
    scantitle = "maghscanup(" + str(startvalue) + ", " + str(endvalue) + ", " + str(step) + ", " +str(waittime) + ", "+ title + ", " + timetype + ", " + str(limit) + ")"
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle  )) 
    print(scantitle)
    
    if startvalue < endvalue:
        value = startvalue
        while value <= endvalue:
            subscantitle = "...maghscanup(" + title + " at " + str(value) + " kG)"
            cmds.append(Set('BL6:CS:LineLog:Add', subscantitle ))
            print(subscantitle)
            cmds.append(Set('BL6:SE:MagH:SetUpperSweepLimit', value, completion=True, readback=True, tolerance=0.2 ))
            cmds.append(Set('BL6:SE:MagH:SetSweepMode', 0, completion=True, readback=True, tolerance=0.2, timeout=10))
            cmds.append(Delay(waittime))
            timetotal = timetotal + waittime
            cmds.append(Script("SetTextPV", "BL6:SMS:RunInfo:RunTitle", title + " at Field = `BL6:SE:MagH:ReadField`"))
            # cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title + ' at pv = ' + str(value) ))
            cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
            if timetype == 'pc' or timetype == 'PC':
                cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
                pctotal = pctotal + limit
            elif timetype.lower() == 'time':
                cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
                timetotal = timetotal + limit
            else:
                raise Exception("unknown time type")   
            cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
            value += step
    else:
        value = startvalue
        if step >0:
            raise Exception("Check the sign of the step")
        while value >= endvalue:
            cmds.append(Set('BL6:CS:LineLog:Add', "...maghscanup(" + title + " at " + str(value) + " kG)" ))
            print(subscantitle)
            cmds.append(Set('BL6:SE:MagH:SetUpperSweepLimit', value, completion=True, readback=True, tolerance=0.2 ))
            cmds.append(Set('BL6:SE:MagH:SetSweepMode', 0, completion=True, readback=True, tolerance=0.2, timeout=10))
            cmds.append(Delay(waittime))
            cmds.append(Script("SetTextPV", "BL6:SMS:RunInfo:RunTitle", title + " at Field = `BL6:SE:MagH:ReadField`"))
            # cmds.append(Set('BL6:SMS:RunInfo:RunTitle', title + ' at pv = ' + str(value) ))
            cmds.append(Set('BL6:CS:RunControl:Start', 1, completion=True))
            if timetype == 'pc' or timetype == 'PC':
                cmds.append(Wait('BL6:Det:PCharge:C', limit, comparison='increase by'))
                pctotal = pctotal + limit
            elif timetype.lower() == 'time':
                cmds.append(Wait('BL6:Det:N1:AcquireTimer_RBV', limit, comparison = 'increase by'))
                timetotal = timetotal + limit
            else:
                raise Exception("unknown time type")   
            cmds.append(Set('BL6:CS:RunControl:Stop', 1, completion=True))
            value += step
    id = submitsmart(cmds, scantitle)
    newscan()





############
# ETC
############

def setpv(pv, value, wait=True):
    """
    generalized command to set PVs
    """
    if pv.lower() == 'detector' :
        movedetector(value)
    elif pv.lower() == 'beamstopx' :
        beamstopX(value)
    elif pv.lower() == 'beamstopy30':
        beamstopY30(value)
    elif pv.lower() == 'beamstopy60':
        beamstopY60(value)
    elif pv.lower() == 'beamstopy90':
        beamstopY90(value)
    elif pv.lower() == 'beamslit1':
        beamslit1(value)
    elif pv.lower() == 'beamslit2':
        beamslit2(value)
    elif pv.lower() == 'beamslit3':
        beamslit3(value)
    elif pv.lower() == 'beamslit4':
        beamslit4(value)
    elif pv.lower() == 'wl':
        setWL(value)
    elif pv.lower() == 'chopperspeed' or pv.lower() =='chopperfreq' or pv.lower()=='freq' :
        chopperfreq(value)
    elif pv.lower() == 'tumbler':
        tumbler(value)
    elif pv.lower() == 'shutter' or pv.lower()=='secondaryshutter':
        if value.lower() == 'open':
            openShutter()
        elif value.lower() =='close':
            closeShutter()
        else:
            print '.Error. Value is not recognized.'
    elif pv.lower() == 'transx':
        movetransx(value)
    else:
        print "...Not a predefined PV. Processing as a raw command"
        scantitle = 'set(' +pv + ', ' + str(value) + ')'
        cmds.append(Set('BL6:CS:LineLog:Add', scantitle )) 
        cmds.append(Set(pv, value, completion = wait))
        id = submitsmart(cmds, scantitle)
        print(scantitle)
        newscan()

def estimatetimeold():
    print ".Total PC = %.2f C \n..........= %.2f hours (%.1f min) at 1.2 MW \n..........= %.2f hours (%.1f min) at 1.0 MW \n..........= %.2f hours (%.1f min) at 1.3 MW"  % (pctotal , pctotal/4.32, pctotal/4.32*60 , pctotal/3.6, pctotal/3.6*60, pctotal/4.68, pctotal/4.68*60)
    print ".Other time = %.1f s = %.2f hours" %(timetotal, timetotal/3600)

def estimatetime(power=1.4):
    print ".Total PC = %.2f C \n" %(pctotal)
    print "..........= %.2f hours (%.1f min) at %.2f MW \n"  % (pctotal/(3.6*power), 60.0*pctotal/(3.6*power), power)
    print ".....Other time = %.1f s = %.2f hours\n\n" % (timetotal, float(timetotal)/3600)
    print ".....Total time = %.2f hours\n" % ((float(timetotal)/3600 + pctotal/(3.6*power)))
    print ".....Now = ", datetime.now()
    print ".....Ending = ", datetime.now() + timedelta(hours= (float(timetotal)/3600 + pctotal/(3.6*power)))

def estimatetimefs(power=1.4):
    print ".Total PC = %.2f C \n" %(pctotal)
    print "..........= %.2f hours (%.1f min) at %.2f MW \n"  % (2*pctotal/(3.6*power), 60.0*2*pctotal/(3.6*power), power)
    print ".....Other time = %.1f s = %.2f hours\n\n" % (timetotal, timetotal/3600)
    print ".....Total time = %.2f hours\n" % ((timetotal/3600 + 2*pctotal/(3.6*power)))
    print ".....Now = ", datetime.now()
    print ".....Ending = ", datetime.now() + timedelta(hours= (timetotal/3600 + 2*pctotal/(3.6*power)))
    
    
def resettime(): # reset time counter
    global pctotal
    global timetotal
    pctotal = 0.0
    timetotal = 0


def readpv(pv):
    '''
    This function can be used to read PV value at the time when this command is executed.
    However, if you use this function, the python script will not complete loading until
    this command is executed. 
    '''
    global pctotal, timetotal, gsimulate
    scantitle = "readpv(" + str(pv) + ")"
    cmds.append(Set('BL6:CS:LineLog:Add', scantitle  )) 
    #cmds.append(Script("SetTextPV", "BL6:SMS:RunInfo:RunTitle", "`BL6:SE:MagH:ReadField`"))
    # BL6:CS:Chat
    id = submitsmart(cmds, scantitle)
    if gsimulate == True:
        temp = caget(pv)
    else:
        scan_info = client.scanInfo(id)
        while not scan_info.isDone():
            time.sleep(0.2)
            scan_info=client.scanInfo(id)
        temp = caget(pv)
    print('readpv = ' + str(temp))
    return temp


      
def simulatethis(scantitle=os.path.basename(sys.argv[0])):
    '''
    This function simulates a scan or an ensamble of scans in the script.
    It does not require any parameters.
    '''
    global gsimulate
    print("\n")
    print("...Simulating the scan  " )
    print("\n")
    gsimulate = True
    
    
def submitsmart(cmds, scantitle):
    global gsimulate
    if gsimulate == True:
        id = client.simulate(cmds)
        # print('simulate')        
    else:
        id = client.submit(cmds,scantitle)
    return id
