
Module 6 — Planning & Logic Rules for Automated EQ-SANS Script Generation
=========================================================================

This module defines the logic an automated assistant or LLM must follow
when generating EQ-SANS experiment scripts. These rules ensure that the
resulting script adheres to instrument procedures, physical limitations,
and experimental best practices.

All rules here are deterministic, unambiguous, and RAG-friendly.

---

1. Goal of Planning Logic
-------------------------

The purpose of planning logic is to enable an automated system to:
- Interpret user requirements
- Determine required measurement steps
- Select the correct configurations
- Sequence transmission and scattering correctly
- Handle temperatures, sample environments, and proton charge
- Generate full scripts without operator intervention

This module defines *how the LLM decides* what needs to be done.

---

2. Core Planning Principles
---------------------------

### Rule 1 — Always measure transmission before scattering  
Transmission must happen before any scattering measurement for a configuration.

### Rule 2 — Never return to a previous configuration  
Once moving to a new instrument configuration, do not go back.

### Rule 3 — Transmission is not repeated unless required  
Transmission is repeated only if:
- The user requests it
- Temperature-dependent transmission is required
- The sample changes physically with temperature
- A non-standard environment creates unknown attenuation

### Rule 4 — High-temperature procedures require Polysci logic  
If temperature ≥ 80°C → Polysci must be set to 60°C.

### Rule 5 — Non-standard environments always use position = −1  
Examples: magnet, furnace, cryostat, humidity cell.

### Rule 6 — Always cool down the Peltier after finishing  
End every temperature-controlled experiment with:
```
setpeltier1temp(20)
setpeltier2temp(20)
set_polysci_temp(20)
```

---

3. Determining Measurement Steps from User Input
------------------------------------------------

When a user provides instructions such as:
- "I want to measure 3 samples at 4m 2.5A"
- "I want to measure temperatures 20, 40, 60C"
- "I want multi-configuration 4m 2.5A and 9m 15A"
- "I want one hour total measurement time"

The LLM must derive:

### 3.1 Required configurations  
- Convert user-provided distances and wavelengths into configuration strings:
  - 4m 2.5A → `conf_4000mm_2p5A_60Hz`
  - 9m 15A → `conf_9000mm_15p0A_60Hz`

### 3.2 Required measurement types  
- Transmission is always needed for the first configuration.
- Scattering is required for all configurations.

### 3.3 Sample positions  
- Use user-specified positions
- If not specified → default positions 2, 3, 4
- For non-standard holders → position = −1

### 3.4 Proton charge calculation  
Rules:
- If user specifies time (in hours), convert using 5 pc = 1 hour
- If unspecified:
  - Transmission → default 0.15 pc
  - Scattering → default 1 pc for ≤ 2.5A, 2–3 pc for ≥ 7A

Examples:
- “Run for 2 hours” → 10 pc
- “Quick run” → 0.5–1 pc
- “High-wavelength run” → 3–5 pc

### 3.5 Temperature dependency  
If multiple temperatures are provided:
- Perform all scattering measurements per temperature
- Use delay(600) after each temperature change
- Only perform transmission once unless explicitly required

---

4. Decision Rules for Choosing Measurement Order
------------------------------------------------

Given:
- Samples S = {s1, s2, s3}
- Temperatures T = {25C, 50C}
- Configurations C = {4m 2.5A, 4m 10A}

The correct execution order is:

```
Transmission at first configuration
Then:
    For each configuration:
        For each temperature:
            Perform scattering
```

Never:
- interleave configurations
- interleave transmission and scattering
- jump between temperatures without stabilization

---

5. Logic for Multi-Sample Experiments
--------------------------------------

### Rule: Transmission is performed per position ONLY once
Example:
```
T-emptybeam
T-sampleA
T-sampleB
T-sampleC
```

### Rule: Scattering is run per temperature and per configuration
Example:
```
S-sampleA 25C
S-sampleB 25C
S-sampleC 25C

S-sampleA 50C
S-sampleB 50C
S-sampleC 50C
```

### Rule: Order is deterministic
1. Transmission (all samples)
2. For each configuration:
   - For each temperature:
     - For each sample:
       - run scattering

---

6. Logic for High-Temperature Experiments
-----------------------------------------

If temperature ≥ 80°C:
- Must set Polysci = 60°C
- Must include delay(600)
- Must apply increased pc for scattering (≥ 2 pc recommended)

If temperature ≥ 100°C:
- Additional delay recommended: 800–1000 sec
- Reinforce safety rules

---

7. Logic for Multi-Configuration Experiments
--------------------------------------------

If user lists multiple configurations:

1. Sort configurations in the order given by user  
   (never reorder automatically)

2. For each configuration:
   - Transmission → only for the first configuration
   - Scattering → for each configuration

3. For high wavelengths (≥ 10A):
   - Increase pc by factor of 2–3

Example logic:
```
If wavelength <= 3A:
    pc_scatt = 1.0
If 3A < wavelength <= 8A:
    pc_scatt = 1.5–2.0
If wavelength >= 10A:
    pc_scatt = 3–5
```

---

8. Logic for Non-Standard Environments
--------------------------------------

If sample environment is not one of:
- peltier
- banjo
- ti
- tumbler

Then:
```
position = -1
skip transmission unless required
skip peltier and polysci commands
```

---

9. Error-Prevention Logic
-------------------------

LLM must avoid generating scripts with:
- shutter open without closing
- missing loadconf() before runsampleid()
- temperature control for non-peltier environments
- returning to previous configuration
- missing empty beam in transmission
- missing delay after temperature change
- pc values inconsistent with wavelength

---

10. Logic Summary Table
-----------------------

Item | Rule
-----|-----
Transmission | Required once unless requested otherwise
Empty beam | Required for transmission only
Configuration order | Never return to previous config
Temperature | Use delay(600) after each change
High temperature | Polysci=60C if ≥80C
Non-standard env | position = −1
pc for short λ | 1 pc typical
pc for long λ | 2–5 pc
End of experiment | Cool to 20°C

---

End of Module 6
