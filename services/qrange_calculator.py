import math
import os

class QRangeCalculator:
    def __init__(self):
        # Constants from qplan.py
        self.L1 = 14.122  # units: metres; moderator to sample distance
        self.L1_in_mm = 14122.  # units: mm; moderator to sample distance
        self.detector_size = 1056.  # units: mm; detector width
        self.Slit1_distance = 10080.  # units: mm
        self.Slit2_distance = 11156.  # units: mm
        self.Slit3_distance = 12150.  # units: mm
        self.Slit4_distance = 14122.  # units: mm
        self.beamstop_sizes = [30., 60., 90.]  # units: mm
        self.Slit1_diameters = [float('nan'), 5., 10., 15., 20., 25., 10., 25., 26.]  # units: mm
        self.Slit2_Slit3_diameters = [float('nan'), 0., 5., 10., 15., 20., 25., 20., 25.]  # units: mm
        self.freq_options = [30., 60.]  # units: Hz

        self.config_folder = "/home/controls/var/QRangeConfigurations/"

    def load_config_data(self, config_name):
        """Load configuration data from .sav files"""
        try:
            params = {}

            # Load scattering config
            config_path = self.config_folder + config_name + ".sav"
            #print(f"Trying to load scattering config from: {config_path}")
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('<') and ' ' in line:
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                key, value = parts
                                # Strip the PV prefix
                                if key.startswith('BL6:CS:QPlan:'):
                                    param_name = key[len('BL6:CS:QPlan:'):]
                                else:
                                    param_name = key
                                try:
                                    # Try to convert to float/int
                                    if '.' in value or 'e' in value.lower():
                                        params[param_name] = float(value)
                                    else:
                                        params[param_name] = int(float(value))  # Handle cases like '1.0'
                                except:
                                    params[param_name] = value
            '''
            # We don't need transmission config for Q-range calculation
            # Load transmission config if exists (overwrites scattering values where applicable)
            config_path_trans = self.config_folder + config_name.replace('_scatt', '_trans') + ".sav"
            # print(f"Trying to load transmission config from: {config_path_trans}")
            if os.path.exists(config_path_trans):
                with open(config_path_trans, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and not line.startswith('#') and not line.startswith('<') and ' ' in line:
                            parts = line.split(' ', 1)
                            if len(parts) == 2:
                                key, value = parts
                                # Strip the PV prefix
                                if key.startswith('BL6:CS:QPlan:'):
                                    param_name = key[len('BL6:CS:QPlan:'):]
                                else:
                                    param_name = key
                                try:
                                    if '.' in value or 'e' in value.lower():
                                        params[param_name] = float(value)
                                    else:
                                        params[param_name] = int(float(value))
                                except:
                                    params[param_name] = value
            '''
            return params
        except Exception as e:
            print(f"Error loading config {config_name}: {e}")
            return None

    def calculate_q_range(self, config_data):
        """Calculate Q range based on config data"""
        if not config_data:
            return None

        # Extract parameters
        beamstop = self.beamstop_sizes[config_data.get('BSforQ', 0)]
        S1s_dia = self.Slit1_diameters[config_data.get('S1s', 0)]
        S2s_dia = self.Slit2_Slit3_diameters[config_data.get('S2s', 0)]
        S3s_dia = self.Slit2_Slit3_diameters[config_data.get('S3s', 0)]
        S4_dia = config_data.get('S4', 0)
        sample_detector_distance = config_data.get('SampleDetDistance', 0)  # mm
        sdd_m = float(sample_detector_distance) / 1000.  # metres
        wavelength_min = config_data.get('WLMin', 0)
        freq = self.freq_options[config_data.get('Freq', 0)]
        corner_r = math.sqrt(2. * (self.detector_size / 2.) * (self.detector_size / 2.))

        results = {}

        if freq == 60:  # frame1 only
            tof_min = (wavelength_min * (self.L1 + sdd_m)) / 0.0039560346
            frame = (1. / freq) * 1000000.
            tof_max = tof_min + frame
            wavelength_max = (tof_max * 0.0039560346) / (self.L1 + sdd_m)

            q_min = 4. * math.pi * math.sin(math.atan2(beamstop / 2., sample_detector_distance) / 2.) / wavelength_max
            q_max_edge = 4. * math.pi * math.sin(math.atan2(self.detector_size / 2., sample_detector_distance) / 2.) / wavelength_min
            q_max_corner = 4. * math.pi * math.sin(math.atan2(corner_r, sample_detector_distance) / 2.) / wavelength_min

            results.update({
                'WLMin': wavelength_min,
                'WLMax': wavelength_max,
                'QMin': q_min,
                'QMaxEdge': q_max_edge,
                'QMaxCorner': q_max_corner,
                'TOFMin': tof_min,
                'TOFMax': tof_max
            })

        elif freq == 30:  # frame1 and frame2
            frame_60 = (1. / 60) * 1000000.

            # Frame 1
            tof_min_f1 = (wavelength_min * (self.L1 + sdd_m)) / 0.0039560346
            tof_max_f1 = tof_min_f1 + frame_60
            wavelength_max_f1 = (tof_max_f1 * 0.0039560346) / (self.L1 + sdd_m)

            q_min_f1 = 4. * math.pi * math.sin(math.atan2(beamstop / 2., sample_detector_distance) / 2.) / wavelength_max_f1
            q_max_edge_f1 = 4. * math.pi * math.sin(math.atan2(self.detector_size / 2., sample_detector_distance) / 2.) / wavelength_min
            q_max_corner_f1 = 4. * math.pi * math.sin(math.atan2(corner_r, sample_detector_distance) / 2.) / wavelength_min

            # Frame 2
            tof_min_f2 = tof_max_f1 + frame_60
            wavelength_min_f2 = (tof_min_f2 * 0.0039560346) / (self.L1 + sdd_m)
            tof_max_f2 = tof_min_f2 + frame_60
            wavelength_max_f2 = (tof_max_f2 * 0.0039560346) / (self.L1 + sdd_m)

            q_min_f2 = 4. * math.pi * math.sin(math.atan2(beamstop / 2., sample_detector_distance) / 2.) / wavelength_max_f2
            q_max_edge_f2 = 4. * math.pi * math.sin(math.atan2(self.detector_size / 2., sample_detector_distance) / 2.) / wavelength_min_f2
            q_max_corner_f2 = 4. * math.pi * math.sin(math.atan2(corner_r, sample_detector_distance) / 2.) / wavelength_min_f2

            results.update({
                'WLMin': wavelength_min,
                'WLMax': wavelength_max_f1,
                'QMin': q_min_f1,
                'QMaxEdge': q_max_edge_f1,
                'QMaxCorner': q_max_corner_f1,
                'WL2Min': wavelength_min_f2,
                'WL2Max': wavelength_max_f2,
                'QMin2': q_min_f2,
                'QMax2Edge': q_max_edge_f2,
                'QMax2Corner': q_max_corner_f2,
                'TOFMin': tof_min_f1,
                'TOFMax': tof_min_f2
            })

        # Calculate beam diameter
        beam_dia = 0
        if (not math.isnan(S1s_dia)) and S1s_dia > 0:
            beam_dia = (S1s_dia + S4_dia) / (self.Slit4_distance - self.Slit1_distance) * sample_detector_distance + S4_dia
        if (not math.isnan(S2s_dia)) and S2s_dia > 0:
            beam_dia2 = (S2s_dia + S4_dia) / (self.Slit4_distance - self.Slit2_distance) * sample_detector_distance + S4_dia
            if beam_dia > beam_dia2:
                beam_dia = beam_dia2
        if (not math.isnan(S3s_dia)) and S3s_dia > 0:
            beam_dia3 = (S3s_dia + S4_dia) / (self.Slit4_distance - self.Slit3_distance) * sample_detector_distance + S4_dia
            if beam_dia > beam_dia3:
                beam_dia = beam_dia3

        results['BeamDia'] = beam_dia

        return results