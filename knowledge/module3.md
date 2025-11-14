
Module 3 — Standard Script Templates for EQ-SANS
=================================================

This module provides clean, ready-to-use templates for the most common EQ-SANS experiment types.
All templates are written in pure text/markdown so they can be pasted directly into a script editor
or stored in a RAG knowledge base.

Each template follows the correct execution order:
1. Standard imports
2. Set IPTS
3. Load transmission configuration
4. Transmission measurements
5. Load scattering configuration
6. Scattering measurements
7. Close shutter

These templates assume:
- ITEMS = 0 unless provided by the user
- sample_env = "peltier" unless specified otherwise

---

1. Template: Setting configuration only Script
-------------------------------------

Use this template when the user wants to drive instruments to specific configuration.
(e.g., for quick checks or calibration).

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

loadconf('CONFIG_trans')

```

Replace `CONFIG_trans` with actual configuration strings like 
- conf_2500mm_2p5A_60Hz_trans : 2.5m 2.5A 60Hz, transmission measurement
- conf_4000mm_10p0A_60Hz_scatt : 4m 10A 60Hz, scattering measurement
- conf_9000mm_15p0A_60Hz_scatt : 9m 15A 60Hz, scattering measurement
- conf_4000mm_2p5A_30Hz_scatt : 4m 2.5A 30Hz (so called frame-skipping mode), 


---

2. Template: Full Transmission + Scattering Script
--------------------------------------------------

This is the standard template for a single configuration.

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# Transmission
loadconf('conf_4000mm_2p5A_60Hz_trans')
openShutter()

runsampleid('T-emptybeam 4m 2.5a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-sampleA 4m 2.5a', 0, 'peltier', 'pc', 2, 0.15)
runsampleid('T-sampleB 4m 2.5a', 0, 'peltier', 'pc', 3, 0.15)

closeShutter()

# Scattering
loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()

runsampleid('S-sampleA 4m 2.5a', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 2.5a', 0, 'peltier', 'pc', 3, 1.0)

closeShutter()
```
NOTE: emptybeam is not measured in the scattering section, which is typical.


---

3. Template: Multi-Configuration Script 
-------------------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# first configuration 4m 2.5a
# Transmission
loadconf('conf_4000mm_2p5A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 2.5a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-sampleA 4m 2.5a', 0, 'peltier', 'pc', 2, 0.15)
runsampleid('T-sampleB 4m 2.5a', 0, 'peltier', 'pc', 3, 0.15)
closeShutter()

# Scattering
loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-sampleA 4m 2.5a', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 2.5a', 0, 'peltier', 'pc', 3, 1.0)
closeShutter()

# second configuration 4m 10a
# Transmission
loadconf('conf_4000mm_10p0A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 10a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-sampleA 4m 10a', 0, 'peltier', 'pc', 2, 0.15)
runsampleid('T-sampleB 4m 10a', 0, 'peltier', 'pc', 3, 0.15)
closeShutter()

# Scattering
loadconf('conf_4000mm_10p0A_60Hz_scatt')
openShutter()
runsampleid('S-sampleA 4m 10a', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 10a', 0, 'peltier', 'pc', 3, 1.0)
closeShutter()
```


---

4. Template: Temperature Series (Single Configuration)
------------------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# Initial temperature
setpeltier1temp(25)
setpeltier2temp(25)

# Transmission
loadconf('conf_4000mm_2p5A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 2.5a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-sampleA 4m 2.5a', 0, 'peltier', 'pc', 2, 0.15)
runsampleid('T-sampleB 4m 2.5a', 0, 'peltier', 'pc', 3, 0.15)
closeShutter()

# Scattering
loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-sampleA 4m 2.5a 25C', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 2.5a 25C', 0, 'peltier', 'pc', 3, 1.0)
closeShutter()

# Next temperature
setpeltier1temp(35)
setpeltier2temp(35)

delay(600) # as needed for temperature equilibration
# Scattering
loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-sampleA 4m 2.5a 35C', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 2.5a 35C', 0, 'peltier', 'pc', 3, 1.0)
closeShutter()


# Next temperature
setpeltier1temp(45)
setpeltier2temp(45)

delay(600) # as needed for temperature equilibration
# Scattering
loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-sampleA 4m 2.5a 45C', 0, 'peltier', 'pc', 2, 1.0)
runsampleid('S-sampleB 4m 2.5a 45C', 0, 'peltier', 'pc', 3, 1.0)
closeShutter()
```
NOTE: transmission is measured once. 

---

5. Template: Temperature Series (Single Configuration)
------------------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# Initial temperature
setpeltier1temp(25)
setpeltier2temp(25)

# Transmission
loadconf('CONFIG_trans')
openShutter()

runsampleid('T-emptybeam CONFIG', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-sample CONFIG', 0, 'peltier', 'pc', 2, 0.15)

closeShutter()

# Temperature list
temp_list = [25, 40, 60, 80]

# Scattering at each temperature
loadconf('CONFIG_scatt')

for T in temp_list:
    setpeltier1temp(T)
    setpeltier2temp(T)
    delay(600)

    openShutter()
    runsampleid(f'S-sample {T}C CONFIG', 0, 'peltier', 'pc', 2, 1.0)
    closeShutter()
```

---

6. Template: Non-Standard Sample Environment
--------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# Transmission (if needed)
loadconf('CONFIG_trans')
openShutter()

runsampleid('T-nonsample CONFIG', 0, 'peltier', 'pc', -1, 0.15)

closeShutter()

# Scattering
loadconf('CONFIG_scatt')
openShutter()

runsampleid('S-nonsample CONFIG', 0, 'peltier', 'pc', -1, 2.0)

closeShutter()
```

Rule:
Non-standard environment → position = -1.

---

7. Template: Multiple Configurations (Sequential)
------------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

configs = [
    ('conf_4000mm_2p5A_60Hz', '4m 2.5a'),
    ('conf_4000mm_7p0A_60Hz', '4m 7A'),
    ('conf_9000mm_15p0A_60Hz', '9m 15A')
]

for conf, label in configs:

    # Transmission
    loadconf(f'{conf}_trans')
    openShutter()
    runsampleid(f'T-emptybeam {label}', 0, 'peltier', 'pc', 1, 0.15)
    runsampleid(f'T-sample {label}', 0, 'peltier', 'pc', 2, 0.15)
    closeShutter()

    # Scattering
    loadconf(f'{conf}_scatt')
    openShutter()
    runsampleid(f'S-sample {label}', 0, 'peltier', 'pc', 2, 1.0)
    closeShutter()
```

---

End of Module 3
