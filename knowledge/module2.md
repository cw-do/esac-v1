Module 2 — EQ-SANS Command Reference
====================================

This module provides a partial reference for commands frequently used in EQ-SANS experiment scripting.
Each command is documented with definition, parameters, rules, and usage examples.
This format is optimized for RAG-based LLM retrieval and deterministic script generation. Complete list of commands are found in the eqsans_scanfunctions_live.txt file.

---

1. Overview
-----------
All EQ-SANS experiment scripts require:
- Importing standard packages

All available functions can be found eqsans_scanfunctions_live.txt file.

---

2. Standard Imports
--------------------
Every EQ-SANS script begins with the same six import lines. These lines MUST be loaded:

from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

These imports must always appear at the top of every script unless the user specifically requests a variant.

3. Measurement principles
In order to obtain data from SANS experiment, one needs both transmission and scattering measurements. transmission measurements collects neutrons directly pass through the sample and set by the transmission configurations. scattering measurements collects scattered neutron data. For this, instrument needs to be prepared by scattering configurations. empty beam is required for the transmission but not required for the scattering measurement. 

setipts is used to set IPTS number for each experiment.
loadconf is used to load configuration setting and prepare instrument for the measuremnets
openShutter is to open the secondary shutter.
runsampleid is used to actually collect data and save neutron data as a file, which will be available in the analysis.sns.gov server.
closeShutter is to close secondary shutter.
setpeltier1temp is to change temperature of peltier block 1
setpeltier2temp is to change temperature of peltier block 2
set_polysci_temp is to set polysci chiller temperature


[Example script] Following script is to perform measurement on banjo and porsil. When asked for example template with 0 knowledge, give this example and just modify configuration if it was specified by the user.

```
# default packages need to be loaded for any type of experiment script.
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *  #use this for individual command-que

# then, set IPTS number which is unique to the experiment.
setipts(31836)

# now set instrument configuration for transmission measurement at 2.5m using 2.5A neutrons wavelength band. 
loadconf('conf_2500mm_2p5A_60Hz_trans')
# open the shutter and allow neutrons
openShutter()
# collect data until the proton charge (pc) reaches to 0.15
runsampleid('T-emptybeam 2.5m 2.5a ', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-banjo 2.5m 2.5a ', 0, 'peltier', 'pc', 2, 0.15)
runsampleid('T-porsil 2.5m 2.5a ', 0, 'peltier', 'pc', 3, 0.15)
# close shutter. before moving detector or changing configuration, it is recommended to close shutter
closeShutter()

# set configuration for 2.5m and 2.5A scattering experiment.
loadconf('conf_2500mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-banjo 2.5m 2.5a ', 0, 'peltier', 'pc', 2, 2)
runsampleid('S-porsil 2.5m 2.5a ', 0, 'peltier', 'pc', 3, 2)
closeShutter()
```

[explanation of above script] The packages imported here should be used in all script for eq-sans. Therefore first section of the code should remain same in any other eq-sans script.  

setipts() define the IPTS number. this is a unique number for each experiment. User needs to provide this number. If not specified by the user, you can use 99999 as a default and let user know.   

loadconf() is to set instrument a specific configuration. detailed parameters to tune the instrument is saved in the file specified in the input string, which is controlled by the instrument scientist. 'conf_2500mm_2p5A_60Hz_trans' means detector distance at 2.5m using neutron wavelength band defined by the minimum value of 2.5A. Chopper frequency is 60 HZ. and the last 'trans' means that this configuration is for the transmission measurement. If the configuration is for the scattering measurement, it will be 'scatt'.  

openShutter() is to open the secondary shutter. from this point, neutrons are allowed to the sample position. 

runsampleid(title, ITEMS, sample_env, pc/time, pos, duration) is mostly used command to actually collect data. 

- title: In the 'T-emptybeam 2.5m 2.5a', 'T-' represents for the transmission measurement. 'emptybeam' is the actual sample label. In this case, it is an empty beam measurement, which means that there is no sample in the beam. '2.5m 2.5a' is another way of specifying instrument configuration. Since we used 2.5m 2.5A wavelength band, we want to add this information in the label text. For example, if sample A is being measured for 4m and 10A scattering configuration, the title will be 'S-A 4m 10a'. Another example, if sample 'protein' scattering is being measured for 9m detector distance and 15A wavelength band at temperature=5C, the title will be 'S-protein 5C 9m 15A'. For example, if 'polymer' scattering is being measured at 1.3m detector distance using 1A wavelength band, the title will be 'S-polymer 1.3m 1a'.

- Second input is the ITEMS number. this will be specified by user. each sample may have unique ITEMS number. ITEMS number is different from IPTS number. If ITEMS number is not given for each sample, just use 0. 

- sample_env, The third parameter of the runsampleid function, indicates the choice of sample environment.  'peltier' is peltier block which can vary temperature from -10C to 125C. 'ti' is for the titanium-rack. 'banjo' is for the banjo rack. 'tumbler' is for tumbler, which keeps rotating samples.  'ti' rack and 'banjo' rack has norrower controlled temperature which is 10C to 60C. 

- next input is used to define the unit of duration of experiment. it is either 'pc' or 'time'. 'pc' means proton charge and 'time' means time in seconds. this is the unit of duration specified in the last input. note that proton charge value 5 is approximately 1 hour.

- next input is the sample position.  

- last input is the duration. if 'pc' is selected in the 4th input of the runsampleid function, the number provided in this last input means proton charge value. For example, runsampleid(title, 0, 'peltier', 'pc', 1, 0.5) will collect data for position 1 of peltier untile proton charge 

- Therefore, in the runsampleid('T-porsil 2.5m 2.5a ', 0, 'peltier', 'pc', 3, 0.15) says that sample name is porsil. it is measured at 2.5m detector distance using 2.5a neutron wavelength band. it is using peltier sample environment and in position 3. and data will be collected until the proton charge value becomes 0.15. 

extra examples
runsampleid('T-porsil 2.5m 2.5a ', 0, 'peltier', 'pc', 3, 0.15) : measure transmission of porsil. using 2.5m detector distance and 2.5A neutron wavenelength. samples are mounted in the position 3 of the peltier block sample environment. data will be collected until proton charge reaches 0.15

runsampleid('S-composite 4m 2.5a ', 0, 'banjo', 'pc', 3, 3.5) : measure scattering of sample named 'composite'. using 4m detector distance and 2.5A neutron wavenelength. samples are mounted in the position 3 of the banjo rack. data will be collected until proton charge reaches 3.5

proton charge 5 is equivalent to 1 hour or 3600 seconds. therefore. total measurement time for the following script is 4 proton charge which is 3600/5*4 = 2880 seconds

loadconf('conf_2500mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-banjo 2.5m 2.5a ', 0, 'peltier', 'pc', 2, 2)
runsampleid('S-porsil 2.5m 2.5a ', 0, 'peltier', 'pc', 3, 2)
closeShutter()


if user wants to finish all scattering experiment within one hour, then the each pc value needs to be evenly distributed. for example, following is to measure 5 sample over 1 hour.
loadconf('conf_2500mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-a 2.5m 2.5a ', 11111,  'peltier', 'pc', 2, 1)
runsampleid('S-b 2.5m 2.5a ', 22222, 'peltier', 'pc', 3, 1)
runsampleid('S-c 2.5m 2.5a ', 33333, 'peltier', 'pc', 4, 1)
runsampleid('S-d 2.5m 2.5a ', 22332, 'peltier', 'pc', 5, 1)
runsampleid('S-e 2.5m 2.5a ', 11234, 'peltier', 'pc', 6, 1)
closeShutter()

in the above example, ITEMS number for each samples are different, they are given as 11111, 22222, 33333, 22332, 11234. As such, if items number of sampleID is given, they should be used.

End of Module 2
