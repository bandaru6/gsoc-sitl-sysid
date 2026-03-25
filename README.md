# GSoC 2026 — SITL Model Generation from Flight Data

**Candidate:** Aashrith Bandaru ([@bandaru6](https://github.com/bandaru6))
**Organization:** ArduPilot
**Mentor:** Nathaniel Mailhot
**Project size:** 350 hours

## Goal

Build a toolchain that takes ArduPilot DataFlash flight logs (`.bin`) and automatically estimates
the key vehicle dynamics and sensor parameters needed for SITL simulation, then outputs an updated
frame model and parameter file that better matches the real vehicle.

## Proposed Pipeline

```
ArduPilot DataFlash .bin log
        ↓
Log Parser + Time Alignment  (pymavlink DFReader)
        ↓
Segment Selector  (hover / maneuver / SYSID chirp windows)
        ↓
Grey-Box Optimizer  (nonlinear least squares / MLE)
        ↓ ←→ Physics Model  (mirrors ArduPilot SIM_Frame JSON structure)
        ↓
[JSON frame model]  +  [SIM_*.parm file]  +  [Fit report + confidence intervals]
        ↓
Validation Runner  (compare SITL replay vs real log — RMS attitude/rate error)
```

## Parameters Estimated

| Parameter | Description | Estimation Method |
|-----------|-------------|-------------------|
| `hoverThrOut` | Throttle fraction at hover | Median of CTUN.ThO during steady hover |
| `propExpo` | Thrust curve nonlinearity | Logged from MOT_THST_EXPO |
| `pwmMin` / `pwmMax` | Motor PWM range | Min/max of RCOU messages |
| `moment_of_inertia` | Ixx, Iyy, Izz (kg·m²) | NLLS fit from angular accel vs motor torque |
| `mdrag_coef` | Momentum drag coefficient | Fit from forward-flight attitude vs airspeed |
| `disc_area` | Rotor disc area (m²) | Combined with thrust coefficient fit |
| `SIM_ACC*_BIAS` | IMU accelerometer bias | Estimated from static/hover IMU segments |
| `SIM_GYR*_BIAS` | Gyro bias | Estimated from pre-arm static IMU segments |

## Tools

### `Tools/scripts/log_to_model_params.py`

Starter script that parses a DataFlash `.bin` log and outputs a SITL-compatible JSON model.

```bash
python3 Tools/scripts/log_to_model_params.py <flight_log.bin>
```

Output:
- `<log>_model.json` — starter frame model (hoverThrOut, propExpo, pwmMin/Max, battery params)
- Console summary of extracted parameters

Handles both old-format logs (`TimeMS`, `ThO` in 0–1000 scale) and new-format logs (`TimeUS`, `ThO` in 0–1).

## Dependencies

```bash
pip install pymavlink numpy
```

## Status

- [x] Log parser + hover throttle extraction (`log_to_model_params.py`)
- [ ] Full dynamics NLLS optimizer
- [ ] Sensor bias/noise estimation
- [ ] JSON frame model export (aligned to ArduPilot SIM_Frame fields)
- [ ] SIM_*.parm file writer
- [ ] Validation harness (sim-vs-real error metrics)
- [ ] SYSID-mode chirp log support

## References

- ArduPilot SITL documentation
- ArduPilot SYSID mode (chirp excitation for system identification)
- Ljung, L. — *System Identification: Theory for the User* (2nd ed.)
- Burri et al. — "Identification of the Propeller Coefficients and Dynamic Parameters of a Hovering Quadrotor From Flight Data" (IEEE 2020)
