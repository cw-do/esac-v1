
Module 5 — Temperature Control Rules and High‑Temperature Procedures
====================================================================

This module describes all temperature‑related procedures for EQ‑SANS experiments,
including Peltier block control, Polysci chiller requirements, temperature sequencing,
and safety‑constrained operating limits.

All rules are written in plain markdown/text for optimal ingestion into a RAG system.

---

1. Temperature Control Overview
-------------------------------

Temperature control at EQ‑SANS primarily uses:

- Peltier block (positions 1–12)
- Polyscience chiller (water circulation system)

Typical use cases include:
- Temperature‑dependent scattering  
- Equilibration studies  
- Multi‑temperature series  
- High‑temperature polymer or solvent behavior  

This module defines the operational rules for accurate and safe temperature control.

---

2. Peltier Temperature Control
------------------------------

### 2.1 Peltier blocks
- **Block 1** controls positions **1–6**
- **Block 2** controls positions **7–12**

### 2.2 Commands
```
setpeltier1temp(T)
setpeltier2temp(T)
```

### 2.3 Allowed temperature range
- Peltier: **−10°C to +125°C**

### 2.4 Rules
1. Peltier control is used only when `sample_env = 'peltier'`.
2. Set both block temperatures when samples may occupy multiple positions.
3. Always allow equilibration time after temperature changes:
   ```
   delay(600)   # 10 minutes typical
   ```
4. For multi‑temperature series, temperature changes should be monotonic when possible
   (e.g., warm → hot → cool).

---

3. Using the Polysci Chiller for High Temperatures
--------------------------------------------------

The Peltier system requires chilled water circulation.  
At temperatures above ~80°C, the load on the Peltier increases significantly.

### 3.1 Polysci command
```
set_polysci_temp(value)
```

### 3.2 Maximum temperature
- Maximum allowed Polysci temperature: **60°C**

### 3.3 High‑temperature thresholds
- When Peltier temperature ≥ **80°C**:
  - The Polysci temperature MUST be set to **60°C**.
- When Peltier temperature ≥ **100°C**:
  - This is still allowed, but Polysci must remain at **60°C**.
  - Additional equilibration time is required.

### 3.4 Example rule set
```
If Peltier temperature < 80C:
    Polysci temperature not required to change.
If 80C <= Peltier temperature <= 125C:
    set_polysci_temp(60)
```

---

4. Stabilization and Equilibration Rules
----------------------------------------

### 4.1 Required equilibration
After setting Peltier temperature:
```
delay(600)  # wait 10 minutes
```

Longer waits may be necessary if:
- temperature > 90°C  
- sample has large thermal mass  
- initial temperature difference is large  

### 4.2 Recommended sequencing
For multi‑temperature operations:
1. Start at lowest temperature
2. Increase stepwise
3. Perform highest temperature last
4. Return to room temperature at the end of script:
```
setpeltier1temp(20)
setpeltier2temp(20)
set_polysci_temp(20)
```

---

5. Transmission Rules vs Temperature
------------------------------------

### 5.1 Transmission is typically **not** repeated
If samples are temperature stable (e.g., solid or sealed liquid cells):
- Transmission measurements are performed **once**, at the initial configuration.

### 5.2 Exceptions requiring new transmission
A new transmission measurement is needed when:
- sample changes physically with temperature (phase transitions, boiling, etc.)
- the user explicitly requests temperature‑dependent transmission
- non‑standard environments are used with unknown beam attenuation
- scattering intensity is expected to vary significantly with temperature

### 5.3 Default guideline for LLM
```
Default: Transmission only once.
Repeat transmission only if the user specifically requests or instability is likely.
```

---

6. High‑Temperature Multi‑Configuration Logic
---------------------------------------------

When performing multiple configurations at high temperature:

1. **Transmission** is performed only once (first configuration).
2. **Scattering** is performed at each configuration and each temperature.
3. **Polysci must be set BEFORE increasing Peltier temperatures above 80°C.**
4. Cooling back down must occur at the end.

### Example high‑temperature sequence
```
set_polysci_temp(60)

setpeltier1temp(80)
setpeltier2temp(80)
delay(600)

# scattering ...
```

---

7. Non‑Standard Environments + Temperature
------------------------------------------

Non‑standard sample environments (magnet, cryostat, furnace, humidity cell)
often have their own temperature control.

Rules:
1. Always set sample position = −1.
2. Do not use `setpeltier1temp` or `setpeltier2temp`.
3. Do not use Polysci temperature control unless explicitly combined with peltier.
4. If furnace/cryostat is used, the user must specify temperature control commands
   (these are external to EQ‑SANS scripting).

---

8. Safety Rules for Temperature Control
---------------------------------------

1. Never exceed Peltier maximum temperature of **125°C**.
2. Never set Polysci temperature above **60°C**.
3. Avoid rapid thermal cycling (ΔT > 50°C instantly).
4. If sample breaks during high‑temperature runs:
   - Close shutter
   - Call Radiation Control Technicians (RCTs)
5. Always cool the Peltier back to 20°C after finishing:
```
setpeltier1temp(20)
setpeltier2temp(20)
set_polysci_temp(20)
```

---

9. Summary Table
-----------------

Item | Rule
-----|-----
Peltier range | −10°C to 125°C
Polysci max | 60°C
High‑temp threshold | ≥80°C requires Polysci=60°C
Stabilization | delay(600) after temperature change
Transmission repetition | Only if needed or requested
Non‑standard env | position = −1, do not use Peltier commands
End‑of‑experiment | return temperature to 20°C

---

End of Module 5
