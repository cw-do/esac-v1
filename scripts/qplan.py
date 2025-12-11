"""
Python IOC for EQSANS Q Range Planner.

@author Marie Yao
"""

# Standard Python support
import atexit
import code
import logging
import os
import time
import _thread, threading
import math
import datetime

# EPICS support
from sns.ca_client import cainit, caput, caget, CAThread
from pcaspy import Driver, Alarm, Severity
from Util.RingLogHandler import RingLogHandler
from Util.Autosave import Autosave
from DAS.CAServerThread import CAServerThread, threads
from scan.util.seconds import formatSecondsAsTime

# Process Variable prefix
pv_prefix = os.environ['BL'] + ':CS:QPlan:'
asg_pv_prefix_default = os.environ['BL'] + ':CS:'

# Keep the last 5 log messages in a ring buffer
ringlog = RingLogHandler(size=5)
ringlog.setFormatter(logging.Formatter( \
    "%(asctime)-11s %(levelname)s %(message)s", "%Y-%m-%d- %H:%M:%S"))

max_ringlog_text = 2048
logging.basicConfig(format = \
    "%(asctime)-15s:%(name)s:%(filename)s(%(lineno)d):%(levelname)s %(message)s")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().addHandler(ringlog)
ringlog.setLevel(logging.INFO)
logging.getLogger('pcaspy').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# for auto save
saverestore = Autosave(path="/home/controls/var/bl6-QPlan",
                       ioc="bl6-QPlan", prefix=pv_prefix)

cainit()

# beamline specific
config_folder = "/home/controls/var/QRangeConfigurations/" # writable by bl-user

L1 = 14.122 # units: metres; moderator to sample distance
L1_in_mm = 14122. # units: mm; moderator to sample distance 

detector_size = 1056. # units: mm; detector width

Slit1_distance = 10080. # units: mm
Slit2_distance = 11156. # units: mm
Slit3_distance = 12150. # units: mm
Slit4_distance = 14122. # units: mm

beamstop_sizes = [30., 60., 90.] # units: mm

Slit1_diameters = [float('nan'), 5., 10., 15., 20., 25., 10., 25., 26.] # units: mm
Slit2_Slit3_diameters = [float('nan'), 0., 5., 10., 15., 20., 25., 20., 25.] # units: mm

freq_options = [30., 60.] # units: Hz; same order as BL6:Chop:Skf14:SpeedEnum for ScanBuilder

# Define served PVs
pvdb = {
   # existing config
   'ExistingConfigSelect'  : { 'type': 'string' }, # input list come from existingConfig folder
   'LoadConfigButton'      : { 'type': 'enum', 'enums': ['Not Load', 'Load'], 'value': 0 },
   'UpdateConfigList'      : { 'type': 'enum', 'enums': ['Not Update', 'Update'], 'value': 0 }, # trigger
   # visual reminder around button
   'LoadConfigButtonATTN'        : { 'type': 'enum', 'enums': [ 'No', 'Yes' ] },

   # new config
   'S1s'                    : { 'type': 'enum', 'enums': ['Undefined', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd10_Cd', 'd25_Cd', 'd26_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit1:Menu
   'S2s'                    : { 'type': 'enum', 'enums': ['Undefined', 'closed', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd20_Cd', 'd25_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit2:Menu
   'S3s'                    : { 'type': 'enum', 'enums': ['Undefined', 'closed', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd20_Cd', 'd25_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit3:Menu
   'S4'                    : { 'type': 'int', 'unit': 'mm' }, # no motor
   'S1t'                    : { 'type': 'enum', 'enums': ['Undefined', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd10_Cd', 'd25_Cd', 'd26_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit1:Menu
   'S2t'                    : { 'type': 'enum', 'enums': ['Undefined', 'closed', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd20_Cd', 'd25_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit2:Menu
   'S3t'                    : { 'type': 'enum', 'enums': ['Undefined', 'closed', 'd5mm', 'd10mm', 'd15mm', 'd20mm', 'd25mm', 'd20_Cd', 'd25_NoCd'], 'value': 0 }, # same as BL6:Mot:beamslit3:Menu

   'SampleDetDistance'     : { 'type': 'int', 'unit': 'mm' }, # honor detectorZ limits

   'BSX'                   : { 'type': 'int' },
   'BS30Ys'                : { 'type': 'int' },
   'BS60Ys'                : { 'type': 'int' },
   'BS90Ys'                : { 'type': 'int' },
   'BS30Yt'                : { 'type': 'int' },
   'BS60Yt'                : { 'type': 'int' },
   'BS90Yt'                : { 'type': 'int' },
   'BSforQ'                : { 'type': 'enum', 'enums': ['BeamStop30', 'BeamStop60', 'BeamStop90',], 'value': 0 }, # TODO: use for visible rules

   'Freq'                  : { 'type': 'enum', 'enums': ['30 Hz (Frame skipping)', '60 Hz',], 'value': 0 }, # use for visible rule for Frame2 results
   'WLMin'                 : { 'type': 'float', 'unit': 'A', 'prec': 3 },
   'Chop1'                 : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay
   'Chop2'                 : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay
   'Chop3'                 : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay
   'Chop4'                 : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay

   'TOFMin'                : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay
   'TOFMax'                : { 'type': 'float', 'unit': 'microseconds', 'prec': 3 }, # phase delay

   'Comment'               : { 'type': 'string' }, # 40 characters

   'CalcButton'            : { 'type': 'enum', 'enums': ['Not Calc', 'Calc'], 'value': 0 },
   # visual reminder around button
   'CalcButtonATTN'        : { 'type': 'enum', 'enums': [ 'No', 'Yes' ] },

   # results
   'BeamDia'               : { 'type': 'float', 'unit': 'mm', 'prec': 3 },

   # frame1
   'WLMax'                 : { 'type': 'float', 'unit': 'A', 'prec': 3 },
   'QMin'                  : { 'type': 'float', 'unit': '1/A', 'prec': 3 },
   'QMaxEdge'              : { 'type': 'float', 'unit': '1/A', 'prec': 3 },
   'QMaxCorner'            : { 'type': 'float', 'unit': '1/A', 'prec': 3 },
   # frame2
   'WL2Min'                : { 'type': 'float', 'unit': 'A', 'prec': 3 },
   'WL2Max'                : { 'type': 'float', 'unit': 'A', 'prec': 3 },
   'QMin2'                 : { 'type': 'float', 'unit': '1/A', 'prec': 3 },
   'QMax2Edge'             : { 'type': 'float', 'unit': '1/A', 'prec': 3 },
   'QMax2Corner'           : { 'type': 'float', 'unit': '1/A', 'prec': 3 },

   # save config
   'ConfigName'            : { 'type': 'string' }, # 40 characters
   'ConfigNameType'        : { 'type': 'string' }, # 40 characters
   # visual reminder in case files already exist
   'ConfigNameTypeATTN'        : { 'type': 'enum', 'enums': [ 'No', 'Yes' ] },

   'ConfigFileExists'      : { 'type': 'enum', 'enums': [ 'No', 'Yes' ] , 'value': 0 },

   'SaveConfigButton'      : { 'type': 'enum', 'enums': ['Not Save', 'Save'], 'value': 0 },
   'SaveConfigOverwriteButton'      : { 'type': 'enum', 'enums': ['Not Save', 'Save'], 'value': 0, 'asg': 'BEAMLINE'},

   # simulation models
   'Model'                 : { 'type': 'enum', 'enums': ['model1', 'model2', 'model1'], 'value': 0 },
   'ModelUpdateButton'     : { 'type': 'enum', 'enums': ['Not Update', 'Update'], 'value': 0 },

   'FileNameScatt'         : { 'type': 'char', 'count': 200 },
   'FileNameTrans'         : { 'type': 'char', 'count': 200 },

   'Log'                   : { 'type': 'char', 'count': max_ringlog_text }, # TODO: display on screen?
}

# Define 'dbl' for PV list 
dbl = [ pv_prefix + pv for pv in list(pvdb.keys()) ]

# PVs for auto save and SaveConfigButton and CalcButtonATTN
need_save = [
    'S4', 'SampleDetDistance', 'BSX', 'Freq', 'WLMin', 'Comment', # for both Scattering and Transmission
    'S1s', 'S2s', 'S3s', 'BS30Ys', 'BS60Ys', 'BS90Ys', # Scattering
    'S1t', 'S2t', 'S3t', 'BS30Yt', 'BS60Yt', 'BS90Yt', # Transmission
    'BSforQ', # for load
    ]

class QPlan(Driver):
    def __init__(self):
        super(QPlan, self).__init__()
        # Restore autosaved values
        saverestore.restorePVs(self, pvdb)
        
        # init PVs not autosaved
        self.setParam('ExistingConfigSelect', "-")
        self.setParam('UpdateConfigList', 1)
        self.setParam('CalcButtonATTN', 1)
        self.setParam('LoadConfigButtonATTN', 0)
        self.setParam('ConfigNameType', "-")
        self.setParam('ConfigNameTypeATTN', 0)
        self.setParam('Model', 0)
        self.setParam('FileNameScatt', [ 45 ]) #ascii of '-'
        self.setParam('FileNameTrans', [ 45 ]) #ascii of '-'
        self.setParam('Log', [ 72, 101, 108, 108, 111 ]) #ascii of 'Hello'

        self.setParam('ConfigFileExists', 0)
        self.setParam('SaveConfigButton', 0)
        self.setParam('SaveConfigOverwriteButton', 0)

        # also update chopper phases
        wl_min = self.getParam('WLMin')
        freq = freq_options[self.getParam('Freq')]
        # TODO: exceptions

        self.calc_phases(wl_min, freq)

        # Writing to these PVs triggers executing method on worker thread
        self.workers = { 'SaveConfigButton': self.save_config,
                         'SaveConfigOverwriteButton': self.save_config_overwrite_if_ncessary,
                         'LoadConfigButton': self.load_config
                       }
        self.worker_thread = None

        # Start thread for periodic processing
        self.event = threading.Event()
        self.thread = threading.Thread(target = self.process)
        self.thread.name = "QPlan Driver"
        self.thread.setDaemon(True)
        self.thread.start()

    def process_file_exists(self):
        file_exists = False
        try:
            # scattering 
            config_file_scatt = config_folder + str(self.getParam('FileNameScatt'))
            file_exists = os.path.isfile(config_file_scatt)

            # print('\n\nIn process_file_exists(). file {} exists: {}\n\n'.format(config_file_scatt, file_exists))

            if not file_exists:
                # transmission
                config_file_trans = config_folder + str(self.getParam('FileNameTrans'))
                # check if file exists
                file_exists = os.path.isfile(config_file_trans)

                # print('\n\nIn process_file_exists(). file {} exists: {}\n\n'.format(config_file_trans, file_exists))

        except Exception as e:
            logger.exception(e)

        self.setParam('ConfigFileExists', 1 if file_exists else 0)
        self.setParam('ConfigNameTypeATTN', 1 if file_exists else 0)

    def process(self):
        """Processing thread
           Runs forever, updating PVs
        """
        while True:
            self.setParam('Log', ringlog.getMessagesString(max_ringlog_text))

            self.process_file_exists()
            
            self.updatePVs()
            self.event.wait(1.0)

    def write(self, reason, value):
        try:
            # Launch worker thread
            if reason in self.workers:
                if value > 0:
                    if self.worker_thread:
                        logging.error("Worder thread is active, need to await its completion")
                        return True
                    self.worker_thread = CAThread(target=self.workers[reason])
                    self.worker_thread.start()
            elif reason == 'ExistingConfigSelect':
                self.setParam(reason, value) # not autosave
                self.setParam('LoadConfigButtonATTN', 1)
            elif reason == 'SampleDetDistance':
                self.setParam('CalcButtonATTN', 1)
                # take care of motor limits
                low_limit = caget('BL6:Mot:detectorZ.LLM')
                high_limit = caget('BL6:Mot:detectorZ.HLM')
    
                if value < low_limit:
                    value = float(low_limit)
                if value > high_limit:
                    value = float(high_limit)
    
                self.set_save(reason, value)

                # also update chopper phases
                wl_min = self.getParam('WLMin')
                freq = freq_options[self.getParam('Freq')]
                # TODO: exceptions

                self.calc_phases(wl_min, freq)

            elif reason == 'BSforQ':
                self.setParam('CalcButtonATTN', 1)
                # set default values for beamstop Ys accordingly.
                self.set_save(reason, value)
                if value == 0: # BS30
                    self.set_save('BS30Ys', -1)
                    self.set_save('BS60Ys', 5)
                    self.set_save('BS90Ys', 5)

                    self.set_save('BS30Yt', -1)
                    self.set_save('BS60Yt', 5)
                    self.set_save('BS90Yt', 5)
                elif value == 1: # BS60
                    self.set_save('BS30Ys', 10)
                    self.set_save('BS60Ys', -1)
                    self.set_save('BS90Ys', 5)

                    self.set_save('BS30Yt', 10)
                    self.set_save('BS60Yt', -1)
                    self.set_save('BS90Yt', 5)
                elif value == 2: # BS90
                    self.set_save('BS30Ys', 10)
                    self.set_save('BS60Ys', 5)
                    self.set_save('BS90Ys', -1)

                    self.set_save('BS30Yt', 10)
                    self.set_save('BS60Yt', 5)
                    self.set_save('BS90Yt', -1)

            elif reason == 'Freq':
                self.setParam('CalcButtonATTN', 1)
                self.set_save(reason, value)
                
                # in case a user change Freq after typed WLMin
                #TODO: calc TOF min and max?
                
                wl_min = self.getParam('WLMin')
                freq = freq_options[value]
                # TODO: exceptions

                self.calc_phases(wl_min, freq)

            elif reason == 'WLMin':
                self.setParam('CalcButtonATTN', 1)
                self.set_save(reason, value)
                #TODO: calc TOF min and max?

                wl_min = value
                freq = freq_options[self.getParam('Freq')]
                # TODO: exceptions

                self.calc_phases(wl_min, freq)

            #elif reason == 'Chop1':
                #self.set_save(reason, value)
                #TODO: calc WLMin and other three choppers' phase delay?
                #TODO: calc TOF min and max
            #elif reason == 'Chop2':
                #self.set_save(reason, value)
                #TODO: calc WLMin and other three choppers' phase delay?
                #TODO: calc TOF min and max
            #elif reason == 'Chop3':
                #self.set_save(reason, value)
                #TODO: calc WLMin and other three choppers' phase delay?
                #TODO: calc TOF min and max
            #elif reason == 'Chop4':
                #self.set_save(reason, value)
                #TODO: calc WLMin and other three choppers' phase delay?
                #TODO: calc TOF min and max

            elif reason == 'CalcButton':
                self.calc() # also update ConfigName and config file names
                self.setParam('CalcButtonATTN', 0)
            elif reason == 'ConfigNameType': # also update config file names
                self.setParam('ConfigNameTypeATTN', 0)
                self.setParam(reason, value)
                
                #assemble file names
                config_name = self.getParam('ConfigName') # generated part
                # append free typing section
                config_name += value # TODO: special characters
                #print config_name
                self.setParam('FileNameScatt', config_name + "_scatt.sav")
                self.setParam('FileNameTrans', config_name + "_trans.sav")

            #elif reason == 'UpdateModelButton':
                #self.setParam(reason, value) # TODO: remove
                #TODO: update

            elif reason in need_save:
                # accept & persist the received value
                self.setParam('CalcButtonATTN', 1)
                self.set_save(reason, value)
            else:
                self.setParam(reason, value)# not autosave

            self.updatePVs()
        except Exception as e:
            logger.exception(e)
            return False

        return True
    def calc_phases(self, wl_min, freq):
        sample_detector_distance = self.getParam('SampleDetDistance') # units: mm; int
        #print wl_min, freq, sample_detector_distance, L1_in_mm
        
        # call JK's calc function to calc phase delay for four choppers
        (chopper_speed_in_Hz, phase1, phase2, phase3, phase4)=self.calcChopperByStartingWavelength(wl_min, freq, sample_detector_distance, L1_in_mm)
        # if issue with sample_detector_distance for 30 Hz: all phases will be set to 0
        
        self.setParam('Chop1', phase1)
        self.setParam('Chop2', phase2)
        self.setParam('Chop3', phase3)
        self.setParam('Chop4', phase4)

    def set_save(self, reason, value):
        # accept & persist the received value
        self.setParam(reason, value)
        saverestore.set(reason, self.getParam(reason))

    def save_config_base(self, prevent_overwrite=True):
        try:
            # scattering 
            config_file_scatt = config_folder + str(self.getParam('FileNameScatt'))
            # check if file exists
            if prevent_overwrite and os.path.isfile(config_file_scatt): # won't write scatt or trans file
                logger.info("File %s exists.", config_file_scatt)
                self.setParam('ConfigNameTypeATTN', 1)
                
            else:# write scatt file
                logger.info("Saving configuration to %s", config_file_scatt)
                saverestore.write(config_file_scatt)
                
                # remove beam stop Y PVs for transmission
                f_scatt = open(config_file_scatt, "r")
                lines_scatt = f_scatt.readlines()
                f_scatt.close()
                
                f_scatt = open(config_file_scatt, "w")
                for line in lines_scatt:
                    if "Comment " in line: # add before using "t " to filter
                        f_scatt.write(line)
                    elif "t " not in line:
                        f_scatt.write(line)
                f_scatt.close()

                # transmission
                config_file_trans = config_folder + str(self.getParam('FileNameTrans'))
                # check if file exists
                if prevent_overwrite and os.path.isfile(config_file_trans): # won't write trans file only
                    logger.info("File %s exists.", config_file_trans)
                    self.setParam('ConfigNameTypeATTN', 1)
                else:# write trans file
                    logger.info("Saving configuration to %s", config_file_trans)
                    saverestore.write(config_file_trans)
                    
                    # remove beam stop Y PVs for scattering
                    f_trans = open(config_file_trans, "r")
                    lines_trans = f_trans.readlines()
                    f_trans.close()
                    
                    f_trans = open(config_file_trans, "w")
                    for line in lines_trans:
                        if "s " not in line:
                            f_trans.write(line)
                    f_trans.close()
        finally:
            self.worker_thread = None
            self.setParam('UpdateConfigList', 1)

    def save_config(self):
        self.save_config_base(prevent_overwrite=True)

    def save_config_overwrite_if_ncessary(self):
        self.save_config_base(prevent_overwrite=False)

    def load_config(self):
        try:
            config = self.getParam('ExistingConfigSelect')
            
            # load scatt
            config_path = config_folder + config + "_scatt.sav"
            logger.info("Reading configuration from %s", config_path)
            ( config_dir, config_file ) = os.path.split(config_path)
            ( config_ioc, config_ext ) = os.path.splitext(config_file)
            saved = Autosave(path=config_dir, ioc=config_ioc, prefix=pv_prefix)
            saved.restorePVs(self, pvdb)

            # load trans, 6 different PVs (and 7 PVs are the same as in scatt
            config_path = config_folder + config + "_trans.sav"
            logger.info("Reading configuration from %s", config_path)
            ( config_dir, config_file ) = os.path.split(config_path)
            ( config_ioc, config_ext ) = os.path.splitext(config_file)
            saved = Autosave(path=config_dir, ioc=config_ioc, prefix=pv_prefix)
            saved.restorePVs(self, pvdb)
            saverestore.savePVs(self, pvdb)

            # Don't restore the 'ConfigFile'
            #saved.delete('ConfigFile')

            # calc chopper phases
            wl_min = self.getParam('WLMin')
            freq = freq_options[self.getParam('Freq')]
            # TODO: exceptions

            self.calc_phases(wl_min, freq)

            # show CalcButtonATTN and hide LoadConfigButtonATTN
            self.setParam('CalcButtonATTN', 1)
            self.setParam('LoadConfigButtonATTN', 0)
        finally:
            self.updatePVs()
            
            self.worker_thread = None

    def calc(self):
        # prep inputs
        beamstop = beamstop_sizes[self.getParam('BSforQ')]
        S1s_dia = Slit1_diameters[self.getParam('S1s')]
        S2s_dia = Slit2_Slit3_diameters[self.getParam('S2s')]
        S3s_dia = Slit2_Slit3_diameters[self.getParam('S3s')]
        S4_dia = self.getParam('S4')
        sample_detector_distance = self.getParam('SampleDetDistance') # units: mm; int
        sdd_m = float(sample_detector_distance)/1000. # units: metres
        wavelength_min = self.getParam('WLMin')
        freq = freq_options[self.getParam('Freq')]
        corner_r = math.sqrt(2.*(detector_size/2.)*(detector_size/2.)) # units: mm
        #print corner_r
        # TODO: exceptions
        
        if freq == 60: # frame1 only
            tof_min = (wavelength_min*(L1 + sdd_m))/0.0039560346 # units: microseconds

            frame = (1./freq)*1000000. # units: microseconds
            tof_max = tof_min + frame # units: microseconds
            wavelength_max = (tof_max*0.0039560346)/(L1 + sdd_m) # units: Angstroms
            #print freq, tof_min, frame, tof_max
            q_min = 4.*math.pi*math.sin(math.atan2(beamstop/2.,sample_detector_distance)/2.)/wavelength_max # units: 1/A
            q_max_edge = 4.*math.pi*math.sin(math.atan2(detector_size/2.,sample_detector_distance)/2.)/wavelength_min # units: 1/A
            q_max_corner = 4.*math.pi*math.sin(math.atan2(corner_r,sample_detector_distance)/2.)/wavelength_min # units: 1/A

            self.setParam('TOFMin', tof_min)
            self.setParam('TOFMax', tof_max)
            self.setParam('WLMax', wavelength_max)
            self.setParam('QMin', q_min)
            self.setParam('QMaxEdge', q_max_edge)
            self.setParam('QMaxCorner', q_max_corner)

            # TODO after models: set to some out of range values
            # for markers only - appears no visible rules for them; won't be display; do not save
            self.setParam('WL2Min', wavelength_min)
            self.setParam('WL2Max', wavelength_max)

        if freq == 30: # frame1 and frame2
            # use 60Hz frame
            frame_60 = (1./60)*1000000. # units: microseconds

            # frame 1
            tof_min_f1 = (wavelength_min*(L1 + sdd_m))/0.0039560346 # units: microseconds

            tof_max_f1 = tof_min_f1 + frame_60 # units: microseconds
            wavelength_max_f1 = (tof_max_f1*0.0039560346)/(L1 + sdd_m) # units: Angstroms

            q_min_f1 = 4.*math.pi*math.sin(math.atan2(beamstop/2.,sample_detector_distance)/2.)/wavelength_max_f1 # units: 1/A
            q_max_edge_f1 = 4.*math.pi*math.sin(math.atan2(detector_size/2.,sample_detector_distance)/2.)/wavelength_min # units: 1/A
            q_max_corner_f1 = 4.*math.pi*math.sin(math.atan2(corner_r,sample_detector_distance)/2.)/wavelength_min # units: 1/A

            # frame 2
            tof_min_f2 = tof_max_f1 + frame_60 # units: microseconds
            wavelength_min_f2 = (tof_min_f2*0.0039560346)/(L1 + sdd_m) # units: Angstroms

            tof_max_f2 = tof_min_f2 + frame_60 # units: microseconds
            wavelength_max_f2 = (tof_max_f2*0.0039560346)/(L1 + sdd_m) # units: Angstroms

            q_min_f2 = 4.*math.pi*math.sin(math.atan2(beamstop/2.,sample_detector_distance)/2.)/wavelength_max_f2 # units: 1/A
            q_max_edge_f2 = 4.*math.pi*math.sin(math.atan2(detector_size/2.,sample_detector_distance)/2.)/wavelength_min_f2 # units: 1/A
            q_max_corner_f2 = 4.*math.pi*math.sin(math.atan2(corner_r,sample_detector_distance)/2.)/wavelength_min_f2 # units: 1/A

            self.setParam('TOFMin', tof_min_f1)
            self.setParam('TOFMax', tof_min_f2) # TODOs

            # frame 1
            self.setParam('WLMax', wavelength_max_f1)
            self.setParam('QMin', q_min_f1)
            self.setParam('QMaxEdge', q_max_edge_f1)
            self.setParam('QMaxCorner', q_max_corner_f1)

            # frame 2
            self.setParam('WL2Min', wavelength_min_f2)
            self.setParam('WL2Max', wavelength_max_f2)
            self.setParam('QMin2', q_min_f2)
            self.setParam('QMax2Edge', q_max_edge_f2)
            self.setParam('QMax2Corner', q_max_corner_f2)

        # calc beam diameter
        beam_dia = 0
        if (not math.isnan(S1s_dia)) and S1s_dia>0:
            beam_dia = (S1s_dia + S4_dia)/(Slit4_distance - Slit1_distance)*sample_detector_distance + S4_dia
        if (not math.isnan(S2s_dia)) and S2s_dia>0:
            beam_dia2 = (S2s_dia + S4_dia)/(Slit4_distance - Slit2_distance)*sample_detector_distance + S4_dia
            if beam_dia>beam_dia2:
                beam_dia = beam_dia2
        if (not math.isnan(S3s_dia)) and S3s_dia>0:
            beam_dia3 = (S3s_dia + S4_dia)/(Slit4_distance - Slit3_distance)*sample_detector_distance + S4_dia
            if beam_dia>beam_dia3:
                beam_dia = beam_dia3

        self.setParam('BeamDia', beam_dia)

        # calc config name, *_scatt.sav and *_trans.sav
        config_name = 'conf_' 
        config_name += str(int(sample_detector_distance)) + 'mm_' 
        config_name += str(wavelength_min).replace('.', 'p') + 'A_'
        config_name += str(int(freq)) + 'Hz'
        #config_name += datetime.datetime.now().strftime("%Y%m%d")
        self.setParam('ConfigName', config_name)

        #append free typing section, necessary redundancy
        config_name += str(self.getParam('ConfigNameType'))
        #print config_name
        self.setParam('FileNameScatt', config_name + "_scatt.sav")
        self.setParam('FileNameTrans', config_name + "_trans.sav")

        logger.info("Calculation finished.")

    def calcChopperByStartingWavelength(self, start_wavelenth, chopper_speed_in_Hz, sample_to_detector_in_mm=None,sample_to_moderator_in_mm=None):
        """
            This is based on JK's script at https://128.219.164.55/repos/PythonControl/branches/eqsans/pydas/legacy/zhao_jk/eqsans_scans.py
            
            calculate chopper phases using chopper_speed_in_Hz , sample_to_detector_in_mm,sample_to_moderator_in_mm
        """
        detector_location=sample_to_detector_in_mm+sample_to_moderator_in_mm

        chopper1_location=5700         # in mili meters
        chopper2_location=7800
        chopper3_location=9497
        chopper4_location=9507
        chopper1_opening=129.605    # angle in degree
        chopper2_opening=179.989
        chopper3_opening=230.010
        chopper4_opening=230.007
    
        pulse_width = 0
        #pulse_width = 20. * 1e-6        # in sec per Angstrom
        beam_crosssection=0    # 40 mm
        chopper_disc_diameter = 578.5        #mm, disc diameter is ~635mm. disc center to beam center ~578.5/2
    
        bandwidth_at_60Hz=3.956e6/detector_location/60.    # 60Hz bandwidth
        wl1=start_wavelenth
        wl2=start_wavelenth+bandwidth_at_60Hz
        
        if chopper_speed_in_Hz == 30 :        # we assume frame skipping mode for 30Hz. Pulse rejection is not considered.
            detector_z_tol=5
            if sample_to_detector_in_mm > 5000 + detector_z_tol :
                logger.info('Frame Skipping operation does not work for SDD > 5m!\n')
                #print '    Returning without any action'
                return (0,0,0,0,0)
    
            phase1_offset=19024.3             # experimentally determined value in micro sec. needs to be added to calc. value.
            phase2_offset=18820
            phase3_offset=19714
            phase4_offset=19361.4
            frame_width=1e6/chopper_speed_in_Hz
            beam_crosssection_adjust = beam_crosssection/ (chopper_disc_diameter * 3.1415926) /chopper_speed_in_Hz /2     # delay the opening by half the beam cross section
                                                                                                                        # or close it earlier by half the beam cross section
            half_angle_to_sec= 1./ 360. /chopper_speed_in_Hz /2.
    
            wl3=wl2+bandwidth_at_60Hz                        #second frame
            wl4=wl3+bandwidth_at_60Hz
            phase1 = chopper1_location/3.956e6*wl3 - 1./60.        # chopper 1 opening edge aligned to wl3, now in sec, this come from previous pulse
            phase1 +=  beam_crosssection_adjust                # delay the opening by half the beam cross section
            phase1 += chopper1_opening * half_angle_to_sec    # move to center
            phase1 = 1e6 * phase1 + phase1_offset            # add adjust, now in micro sec
            phase1 %= frame_width
    
            phase2 = chopper2_location/3.956e6*wl2            # chopper 2 closing edge aligned to wl2,now in sec
            phase2 -= beam_crosssection_adjust                # close the choppler by half the beam cross section earlier
            phase2 -= chopper2_opening * half_angle_to_sec    # move to center
            phase2 = 1e6 * phase2 + phase2_offset            # adjust, now in micro sec
            phase2 %= frame_width
    
            phase3 = chopper3_location/3.956e6*wl4 - 1./60.        # chopper 3 closing edge aligned to wl4
            phase3 -=  beam_crosssection_adjust                # close the choppler by half the beam cross section earlier
            phase3 -= chopper3_opening * half_angle_to_sec    # move to center
            phase3 = 1e6 * phase3 + phase3_offset            # adjust
            phase3 %= frame_width
    
            phase4 = chopper4_location/3.956e6*wl1            # chopper 4 opening edge aligned to wl1,now in sec
            phase4 += beam_crosssection_adjust                # delay the opening by half the beam cross section
            phase4 += pulse_width * wl1    /detector_location * chopper4_location            # only T4 need pulse width adjust
            phase4 += chopper4_opening * half_angle_to_sec    # move to center
            phase4 = 1e6 * phase4 + phase4_offset            # adjust, now in micro sec
            phase4 %= frame_width

            #print 'Beam cross section adjust to choppers for 30Hz: '
            #print '    T1: opens later    by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print '    T2: closes earlier by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print '    T3: closes earlier by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print '    T4: opens later    by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print
            #print 'Pulse width adjust: T4 open later by ', int(pulse_width * wl1 /detector_location * chopper4_location*1e6+0.5)    ,' micro sec'
            #print

            return (chopper_speed_in_Hz, phase1, phase2, phase3,phase4)
    
        elif chopper_speed_in_Hz == 60 :                # this is the normal op.
            phase1_offset=9507                    # experimentally determined value in micro sec. needs to be added to calc. value.
            phase2_offset=9471
            phase3_offset=9829.7
            phase4_offset=9584.3
            frame_width=1e6/ chopper_speed_in_Hz        # in micro sec
            half_angle_to_sec= 1./ 360. /chopper_speed_in_Hz /2.
            beam_crosssection_adjust = beam_crosssection/ (chopper_disc_diameter * 3.1415926) /chopper_speed_in_Hz /2     # delay the opening by half the beam cross section
                                                                                                                    # or close it earlier by half the beam cross section
            if wl1 > 13 :    # we align the chopper differently between wl1>13 and wl1<=13 to stop leaks.
                phase1 = chopper1_location/3.956e6*wl1             # chopper 1 opening edge aligned to wl1, now in sec, T1 does not need adjust for 60Hz
                phase1 += chopper1_opening * half_angle_to_sec        # move to center
                phase2 = chopper2_location/3.956e6*wl2            # chopper 2 closing edge aligned to wl2,now in sec, T2 does not need adjust for 60Hz
                phase2 -= chopper2_opening * half_angle_to_sec        # move to center
            else:
                phase1 = chopper1_location/3.956e6*wl2             # chopper 1 closing edge aligned to wl2, now in sec, T1 does not need adjust for 60Hz
                phase1 -= chopper1_opening * half_angle_to_sec        # move to center
                phase2 = chopper2_location/3.956e6*wl1            # chopper 2 opening edge aligned to wl1,now in sec, T2 does not need adjust for 60Hz
                phase2 += chopper2_opening * half_angle_to_sec        # move to center
            phase1 = 1e6 * phase1 + phase1_offset            # add adjust, now in micro sec
            phase1 %= frame_width
            phase2 = 1e6 * phase2 + phase2_offset            # adjust, now in micro sec
            phase2 %= frame_width
    
            phase3 = chopper3_location/3.956e6* wl2             # chopper 3 closing edge aligned to wl2
            phase3 -= beam_crosssection_adjust                # close the choppler by half the beam cross section earlier
            phase3 -= chopper3_opening * half_angle_to_sec    # move to center
            phase3 = 1e6 * phase3 + phase3_offset            # adjust
            phase3 %= frame_width
            
            #print chopper3_location,chopper3_opening,phase3_offset,phase3
            
            phase4 = chopper4_location/3.956e6*wl1            # chopper 4 opening edge aligned to wl1,now in sec
            phase4 += beam_crosssection_adjust                # delay the opening by half the beam cross section
            #print phase4
            phase4 += pulse_width * wl1    /detector_location * chopper4_location            # only T4 need pulse width adjust
            #print phase4
            phase4 += chopper4_opening * half_angle_to_sec    # move to center
            phase4 = 1e6 * phase4 + phase4_offset            # adjust, now in micro sec
            phase4 %= frame_width
    
            if detector_location < 360/chopper1_opening*chopper1_location : # T1 is not opened enough
                x1=3.956*(phase1 - phase1_offset - 1e6*chopper1_opening * half_angle_to_sec)/chopper1_location
                x1 -= wl1
                #print wl1,x1,phase1
                if x1>0 and x1<.2: # shouldn't be too big    
                    phase1 -= x1*chopper1_location/3.956
                #print phase1
                #x2=3.956*(phase2 - phase2_offset - 1e6*chopper2_opening * half_angle_to_sec)/chopper2_location
                #x3=3.956*(phase3 - phase3_offset - 1e6*chopper3_opening * half_angle_to_sec)/chopper3_location
                #x4=3.956*(phase4 - phase4_offset - 1e6*chopper4_opening * half_angle_to_sec)/chopper4_location
                #print x2,x3,x4

            #print 'Beam cross section adjust to choppers for 60Hz: '
            #print '    T3: closes earlier by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print '    T4: opens later    by ', int(beam_crosssection_adjust    * 1e6+0.5),' micro sec'
            #print
            #print 'Pulse width adjust: T4 opens later by ', int(pulse_width * wl1/detector_location * chopper4_location    * 1e6+0.5)    ,' micro sec'
            #print

            return (chopper_speed_in_Hz, phase1, phase2, phase3,phase4)

def add_access_security_to_pvs():
    """
    Apply access security to PVs in this IOC.
    """
    global pvdb

    # Add access security as necessary.
    updated_pvdb = {}
    # noinspection PyUnresolvedReferences
    for pv_name, pv_definition in list(pvdb.items()):
        if 'asg' not in pv_definition:
            pv_definition['asg'] = 'ALWAYS'
        updated_pvdb[pv_name] = pv_definition
    pvdb = updated_pvdb


add_access_security_to_pvs()

asg_prefix = os.environ.get('ASG_PREFIX')
if not asg_prefix:
    # noinspection PyUnresolvedReferences
    asg_prefix = asg_pv_prefix_default.rstrip(':')

print(('ASG Prefix: {}'.format(asg_prefix)))

asg_file = os.environ.get('ASG_FILE')

if asg_file:
    if os.path.isfile(asg_file):
        print(('Using access security file: ' + asg_file))
        driver_args = []
        ca_server = CAServerThread(pv_prefix, pvdb, QPlan, driver_args, asg_file, asg_prefix)
    else:
        raise ValueError('ASG file {} does not exist.'.format(asg_file))
else:
    print('Not using an access security file.')
    ca_server = CAServerThread(pv_prefix, pvdb, QPlan)

# Start CA Server
ca_server.start()

# "Arrange orderly shutdown"
def my_atexit():
    logger.info("Exiting QPlan Python IOC...")
    ca_server.shutdown()
    ca_server.join()

    print("Exited.")

atexit.register(my_atexit)

logger.info("QPlan Python IOC started...")

print("Entering interpreter, 'exit()' to shut down")
code.interact(local=locals())