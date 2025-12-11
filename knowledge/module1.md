Module 1 — Core Concepts for EQ-SANS Experiments
================================================

1. Overview of SANS
-------------------

### 1.1 What is Small-Angle Neutron Scattering (SANS)
Small-Angle Neutron Scattering (SANS) measures neutrons scattered at small angles to obtain structural information on length scales from approximately 1 nm to several hundred nm.

Typical applications include:
- Polymers, gels, soft materials
- Nanoparticles and colloids
- Porous media
- Biological macromolecules
- Temperature- or field-dependent structural changes

2. EQ-SANS at the Spallation Neutron Source (SNS)
-------------------------------------------------

### 2.1 Time-of-Flight (TOF) principle
EQ-SANS uses a pulsed neutron source. Neutrons are separated by wavelength using time-of-flight (TOF), where wavelength is inferred from arrival time at the detector.

### 2.2 Instrument configurations
A configuration is defined by:
- Detector distance (e.g., 1.3 m, 2.5 m, 4 m, 8 m, 9 m)
- Wavelength band (e.g., 2.5 Å, 7 Å, 10 Å, 15 Å)
- Chopper frequency (typically 60 Hz)
- Measurement mode: transmission (`trans`) or scattering (`scatt`)

Examples of configuration strings:
- conf_2500mm_2p5A_60Hz_trans : 2.5m 2.5A 60Hz, transmission measurement
- conf_4000mm_10p0A_60Hz_scatt : 4m 10A 60Hz, scattering measurement
- conf_9000mm_15p0A_60Hz_scatt : 9m 15A 60Hz, scattering measurement
- conf_4000mm_2p5A_30Hz_scatt : 4m 2.5A 30Hz (so called frame-skipping mode), scattering measurement
- conf_xxxxmm_xxpyA_zzHz_scatt : xxxx mm sample to detector distance, 
    xxpy A neutron wavelength, here xxpy can be any floating number 2p5 = 2.5 or 4p5=4.5 or 10p0 = 10.0
    zz Hz : chopper frequency zz is 30 or 60. 60 is typical
    the last 'scatt' is for scattering. 'trans' will be for transmission.
    
command loadconf is used to load this configuration settings.

NOTE: WHEN ASKED ABOUT CONFIGURATIONS OR EXISTING CONFIGURATIONS, USE THE LIST OF CONFIGURATIONS DEFINED UNDER <Currently Existing Configurations> in the knowledge


3. Types of Measurements
------------------------

### 3.1 Transmission measurement (T-run)
Transmission measures the neutrons that pass directly through a sample.

Usage:
- Normalization of scattering data
- Determining transmission values for each sample
- Empty beam measurement (no sample)

Characteristics:
- Conducted with transmission configurations (`*_trans`)
- Empty beam measurement is required
- Typically short duration (0.1–0.2 pc)

Naming example:
T-samplename 4m 2.5a

### 3.2 Scattering measurement (S-run)
Scattering measures neutrons scattered by the sample.

Characteristics:
- Conducted with scattering configurations (`*_scatt`)
- Empty beam is not required
- Duration usually longer (1–3 pc or more)
- Repeated at different configurations or temperatures

Naming example:
S-samplename 4m 2.5a
S-sample 50C 9m 15A

4. Proton Charge (pc) and Measurement Time
------------------------------------------

### 4.1 Understanding "pc"
Proton charge (pc) is proportional to the accumulated beam exposure time.

Approximate equivalence:
- 5 pc ≈ 1 hour of beam time

Common usage:
- Transmission: 0.1–0.2 pc
- Typical scattering: 1–3 pc
- Long high-wavelength scattering: 3–5+ pc

5. IPTS and ITEMS Identifiers
-----------------------------

### 5.1 IPTS number
- Unique experiment identifier.
- Set using: setipts(XXXXX)
- If not provided, the default value is 99999.

### 5.2 ITEMS number
- Unique identifier for each sample.
- Provided by user or system.
- If unknown, use 0.

Example:
runsampleid("S-polymer 4m 2.5a", 34567, "peltier", "pc", 2, 1)

6. Sample Environments
----------------------

### 6.1 Standard sample environments

Environment | Description | Temperature Range | Notes
----------- | ----------- | ----------------- | -----
peltier | temperature-controlled block | -10°C to 125°C | Positions 1–12
ti | titanium rack | approx. 10–60°C | fixed geometry
banjo | banjo rack | approx. 10–60°C | standard quartz cells
tumbler | rotating sample holder | ambient | rotation only

### 6.2 Non-standard sample environments
Examples include magnets, cryostats, furnaces, humidity chambers, and custom setups.

Rule:
Non-standard sample environments always use sample position = -1.

7. Naming Conventions for Runs
------------------------------

### 7.1 General format
<T or S>-<sample>[ optional temperature ] <distance>m <wavelength>A

Examples:
T-emptybeam 4m 2.5a
T-sampleA 4m 2.5a
S-protein 5C 9m 15A
S-composite 4m 10a
S-silica 80C 4m 7A

### 7.2 Temperature notation
S-sample 50C 4m 2.5a

### 7.3 Empty beam naming
T-emptybeam 4m 2.5a
T-empty peltier 9m 15A

8. Standard Order of Operations
-------------------------------

For each instrument configuration, follow this sequence:

1. Set IPTS
2. (Optional) Set temperature(s)
3. Load transmission configuration (`*_trans`)
4. Open shutter
5. Perform transmission measurements
6. Close shutter
7. Load scattering configuration (`*_scatt`)
8. Open shutter
9. Perform scattering measurements
10. Close shutter

9. Temperature Control Concepts
-------------------------------

### 9.1 Peltier blocks
- Positions 1–6 belong to block 1
- Positions 7–12 belong to block 2

Commands:
setpeltier1temp(T)
setpeltier2temp(T)

### 9.2 Polysci chiller
Used when peltier temperatures exceed approximately 80°C.
Command: set_polysci_temp(value)
Maximum temperature: 60°C

### 9.3 Stabilization delay
delay(600)

10. Empty Beam Requirement
--------------------------

- Transmission mode requires empty beam.
- Scattering mode does not require empty beam.

11. Multi-Configuration Procedures
----------------------------------

- For each configuration, complete both transmission and scattering before switching to the next configuration.
- Do not return to earlier configurations.

12. Non-Standard Sample Holders
-------------------------------

Rule:
Always use sample position = -1.

Example:
runsampleid("S-humiditycell 4m 2.5a", 0, "peltier", "pc", -1, 2)

13. Basic Safety Principles
---------------------------

- If a sample breaks after exposure, call Radiation Control Technicians (RCTs).
- Do not touch irradiated samples.
- During work hours, contact the local contact.
- Outside work hours, contact the Instrument Hall Coordinators (IHCs).

End of Module 1
