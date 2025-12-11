
Module 4 — Multi-Configuration and Advanced Templates for EQ-SANS
=================================================================

This module contains templates for experiments involving multiple detector distances,
multiple wavelength bands, multiple temperatures, and multi-sample logic that spans
many configurations.

These templates follow strict EQ-SANS ordering rules:
1. For each configuration: transmission → scattering
2. Never return to a previous configuration
3. Empty beam usualy does not require scattering measurement
4. Use sample position = -1 for non-standard environments

All templates are written in clean markdown/text format for direct RAG ingestion.

---

1. Multi-Configuration (Two Configurations)
-------------------------------------------

This template measures transmission and scattering at two different configurations
(e.g., 4m 2.5A and 4m 10A).

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

# --- First configuration: 4m 2.5A ---
loadconf('conf_4000mm_2p5A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 2.5a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-A 4m 2.5a', 0, 'peltier', 'pc', 2, 0.15)
closeShutter()

loadconf('conf_4000mm_2p5A_60Hz_scatt')
openShutter()
runsampleid('S-A 4m 2.5a', 0, 'peltier', 'pc', 2, 1.0)
closeShutter()

# --- Second configuration: 4m 10A ---
loadconf('conf_4000mm_10p0A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 10a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-A 4m 10a', 0, 'peltier', 'pc', 2, 0.15)
closeShutter()

loadconf('conf_4000mm_10p0A_60Hz_scatt')
openShutter()
runsampleid('S-A 4m 10a', 0, 'peltier', 'pc', 2, 3.0)
closeShutter()
```

---

2. Multi-Configuration (Three Configurations)
---------------------------------------------

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
    loadconf(conf + '_trans')
    openShutter()
    runsampleid(f'T-emptybeam {label}', 0, 'peltier', 'pc', 1, 0.15)
    runsampleid(f'T-sampleA {label}', 0, 'peltier', 'pc', 2, 0.15)
    closeShutter()

    # Scattering
    loadconf(conf + '_scatt')
    openShutter()
    runsampleid(f'S-sampleA {label}', 0, 'peltier', 'pc', 2, 1.0)
    closeShutter()
```

---

3. Multi-Sample and Multi-Configuration Template
------------------------------------------------

This template handles several samples measured across multiple configurations.

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

samples = [
    (2, 'A'),
    (3, 'B'),
    (4, 'C')
]

configs = [
    ('conf_4000mm_2p5A_60Hz', '4m 2.5a'),
    ('conf_8000mm_8p0A_60Hz', '8m 8A')
]

for conf, label in configs:

    # Transmission
    loadconf(conf + '_trans')
    openShutter()
    runsampleid(f'T-emptybeam {label}', 0, 'peltier', 'pc', 1, 0.15)
    for pos, name in samples:
        runsampleid(f'T-{name} {label}', 0, 'peltier', 'pc', pos, 0.15)
    closeShutter()

    # Scattering
    loadconf(conf + '_scatt')
    openShutter()
    for pos, name in samples:
        runsampleid(f'S-{name} {label}', 0, 'peltier', 'pc', pos, 1.0)
    closeShutter()
```

---

4. Multi-Temperature + Multi-Configuration Template
---------------------------------------------------

```
from epics import caget
from scan import *
import os
import sys
sys.path.append('/home/controls/var/tmp/scripting/dev/')
from eqsans_scanfunctions_live import *

setipts(99999)

temps = [25, 40, 60]
samples = [(2, 'A')]

configs = [
    ('conf_4000mm_2p5A_60Hz', '4m 2.5a'),
    ('conf_4000mm_10p0A_60Hz', '4m 10a')
]

# Transmission is done only once (at initial temperature)
setpeltier1temp(25)
setpeltier2temp(25)

loadconf('conf_4000mm_2p5A_60Hz_trans')
openShutter()
runsampleid('T-emptybeam 4m 2.5a', 0, 'peltier', 'pc', 1, 0.15)
runsampleid('T-A 4m 2.5a', 0, 'peltier', 'pc', 2, 0.15)
closeShutter()

# Scattering at each config and temperature
for conf, label in configs:
    loadconf(conf + '_scatt')
    for T in temps:
        setpeltier1temp(T)
        setpeltier2temp(T)
        delay(600)
        openShutter()
        runsampleid(f'S-A {T}C {label}', 0, 'peltier', 'pc', 2, 1.0)
        closeShutter()
```


End of Module 4
