#!/usr/bin/env python3
"""
log_to_model_params.py

Extracts key SITL model parameters from an ArduPilot DataFlash .bin log
and outputs a starter JSON frame model compatible with sim_vehicle.py.

Usage:
    python3 log_to_model_params.py <flight_log.bin>

Author: Aashrith Bandaru (github.com/bandaru6)
GSoC 2026 - SITL Model Generation from Flight Data
"""

import sys
import json
import numpy as np
from pymavlink import DFReader


def get_timestamp(m):
    """Return timestamp in microseconds, handling both old (Time) and new (TimeUS) formats."""
    if hasattr(m, 'TimeUS'):
        return m.TimeUS
    if hasattr(m, 'TimeMS'):
        return m.TimeMS * 1000
    return 0


def extract_hover_throttle(log_path):
    """Extract hoverThrOut from CTUN.ThO during steady hover segments."""
    log = DFReader.DFReader_binary(log_path)

    throttle_vals = []
    climb_rates = []

    while True:
        m = log.recv_msg()
        if m is None:
            break
        t = m.get_type()
        if t == "CTUN":
            thr = getattr(m, 'ThO', getattr(m, 'ThrOut', None))
            if thr is not None:
                throttle_vals.append((get_timestamp(m), thr))
        elif t == "BARO":
            climb_rates.append((get_timestamp(m), getattr(m, 'CRt', 0)))

    if not throttle_vals:
        return None

    # Hover = low climb rate window; use median throttle as hoverThrOut
    throttle_arr = np.array([v[1] for v in throttle_vals])
    hover_thr = float(np.median(throttle_arr))
    # Normalize: older logs use 0–1000 scale; SITL expects 0.0–1.0
    if hover_thr > 1.0:
        hover_thr = hover_thr / 1000.0
    return hover_thr


def extract_battery_params(log_path):
    """Extract reference battery parameters from BAT messages."""
    log = DFReader.DFReader_binary(log_path)

    voltages = []
    currents = []
    resistances = []

    while True:
        m = log.recv_msg()
        if m is None:
            break
        if m.get_type() == "BAT":
            if hasattr(m, 'Volt') and m.Volt > 0:
                voltages.append(m.Volt)
            if hasattr(m, 'Curr') and m.Curr > 0:
                currents.append(m.Curr)
            if hasattr(m, 'Res') and m.Res > 0:
                resistances.append(m.Res)

    return {
        "refVoltage": float(np.median(voltages)) if voltages else None,
        "refCurrent": float(np.median(currents)) if currents else None,
        "refBatRes":  float(np.median(resistances)) if resistances else None,
    }


def extract_motor_pwm_range(log_path):
    """Extract motor PWM min/max from RCOU messages."""
    log = DFReader.DFReader_binary(log_path)

    pwm_vals = []
    while True:
        m = log.recv_msg()
        if m is None:
            break
        if m.get_type() == "RCOU":
            for field in ["C1", "C2", "C3", "C4"]:
                val = getattr(m, field, None)
                if val and val > 0:
                    pwm_vals.append(val)

    if not pwm_vals:
        return None, None
    return int(np.min(pwm_vals)), int(np.max(pwm_vals))


def extract_prop_expo(log_path):
    """Extract propExpo from MOT_THST_EXPO parameter if logged."""
    log = DFReader.DFReader_binary(log_path)
    while True:
        m = log.recv_msg()
        if m is None:
            break
        if m.get_type() == "PARM":
            if hasattr(m, 'Name') and m.Name == "MOT_THST_EXPO":
                return float(m.Value)
    return None


def build_model(log_path):
    """Build a starter SITL JSON model from a DataFlash log."""
    print(f"Parsing: {log_path}\n")

    hover_thr = extract_hover_throttle(log_path)
    battery   = extract_battery_params(log_path)
    pwm_min, pwm_max = extract_motor_pwm_range(log_path)
    prop_expo = extract_prop_expo(log_path)

    model = {}

    if hover_thr is not None:
        model["hoverThrOut"] = round(hover_thr, 4)
        print(f"  hoverThrOut : {model['hoverThrOut']}")

    if prop_expo is not None:
        model["propExpo"] = round(prop_expo, 4)
        print(f"  propExpo    : {model['propExpo']}")

    if pwm_min and pwm_max:
        model["pwmMin"] = pwm_min
        model["pwmMax"] = pwm_max
        print(f"  pwmMin/Max  : {pwm_min} / {pwm_max}")

    for k, v in battery.items():
        if v is not None:
            model[k] = round(v, 4)
            print(f"  {k:<12}: {v:.4f}")

    print("\nNote: mass, moment_of_inertia, disc_area, mdrag_coef require")
    print("dynamics fitting (nonlinear least squares) — coming in full pipeline.\n")

    return model


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 log_to_model_params.py <flight_log.bin>")
        sys.exit(1)

    log_path = sys.argv[1]
    model = build_model(log_path)

    out_path = log_path.replace(".bin", "_model.json")
    with open(out_path, "w") as f:
        json.dump(model, f, indent=2)

    print(f"Starter model written to: {out_path}")
    print("Load with: sim_vehicle.py -v ArduCopter --model=json --add-param-file=<model.json>")


if __name__ == "__main__":
    main()
