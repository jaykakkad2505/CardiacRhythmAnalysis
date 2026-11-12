"""
ECG Processing Pipeline (utils/ecg_processing.py)

Implements the backend workflow from the architecture spec:
  ECG CSV/Dataset -> Pandas File Reader -> Data Validation -> Signal
  Processing -> Parameter Calculation -> Heart Rate / RR / PR / QRS / QT /
  QTc -> Medical Rule Engine -> Diagnosis

Uses NeuroKit2 for signal cleaning, R-peak detection, and full P-QRS-T
wave delineation (this is what makes real PR/QRS/QT interval measurement
possible, not just beat-to-beat heart rate).
"""

import numpy as np
import neurokit2 as nk

from config import NORMAL_RANGES


class ECGValidationError(Exception):
    pass


def validate_signal(signal, sampling_rate):
    if signal is None or len(signal) == 0:
        raise ECGValidationError("The file contains no waveform samples.")
    if sampling_rate <= 0:
        raise ECGValidationError("Sampling rate must be a positive number.")
    if len(signal) < sampling_rate * 2:
        raise ECGValidationError("Need at least 2 seconds of waveform data to analyze.")
    if not np.all(np.isfinite(signal)):
        raise ECGValidationError("The waveform contains invalid (non-numeric) values.")
    return True


def _marker_indices(signals, column):
    return np.where(signals[column].values == 1)[0]


def process_ecg(signal, sampling_rate):
    """
    Runs the full pipeline: clean -> detect R-peaks -> delineate P/QRS/T
    waves -> compute clinical parameters -> apply the Medical Rule Engine.

    Returns a dict with:
      params: {heart_rate, rr_interval, pr_interval, qrs_duration,
               qt_interval, qtc_interval, beat_count, signal_duration}
      finding: str  (e.g. "Normal sinus rhythm")
      status: str   ("Stable" or "Review needed")
      flags: list of str  (which specific parameters are out of range)
      rpeaks: array of R-peak sample indices (for plotting)
      cleaned_signal: cleaned waveform array (for plotting)
    """
    validate_signal(signal, sampling_rate)
    signal = np.asarray(signal, dtype=float)

    cleaned = nk.ecg_clean(signal, sampling_rate=sampling_rate)

    try:
        _, rpeaks_info = nk.ecg_peaks(cleaned, sampling_rate=sampling_rate)
        r_peaks = rpeaks_info["ECG_R_Peaks"]
        if len(r_peaks) < 2:
            raise ECGValidationError("Could not detect enough heartbeats in this recording.")

        # 'prominence' delineation gives tighter, more clinically realistic
        # wave boundaries than the default method for this kind of signal.
        _, waves = nk.ecg_delineate(cleaned, rpeaks_info, sampling_rate=sampling_rate, method="prominence")
    except ECGValidationError:
        raise
    except Exception as exc:
        raise ECGValidationError(f"Could not process this waveform: {exc}")

    def marker(col):
        arr = np.array(waves.get(col, []), dtype=float)
        return arr[~np.isnan(arr)].astype(int) if len(arr) else np.array([], dtype=int)

    p_onsets = marker("ECG_P_Onsets")
    r_onsets = marker("ECG_R_Onsets")
    r_offsets = marker("ECG_R_Offsets")
    t_offsets = marker("ECG_T_Offsets")

    rr_intervals = np.diff(r_peaks) / sampling_rate
    mean_rr = float(np.mean(rr_intervals)) if len(rr_intervals) else None
    heart_rate = round(60.0 / mean_rr) if mean_rr else None

    pr_interval = _mean_paired_interval(p_onsets, r_onsets, sampling_rate)
    qrs_duration = _mean_paired_interval(r_onsets, r_offsets, sampling_rate)
    qt_interval = _mean_paired_interval(r_onsets, t_offsets, sampling_rate)

    qtc_interval = None
    if qt_interval and mean_rr:
        qtc_interval = qt_interval / (mean_rr ** 0.5)  # Bazett's formula

    params = {
        "heart_rate": heart_rate,
        "rr_interval": round(mean_rr, 3) if mean_rr else None,
        "pr_interval": round(pr_interval, 3) if pr_interval else None,
        "qrs_duration": round(qrs_duration, 3) if qrs_duration else None,
        "qt_interval": round(qt_interval, 3) if qt_interval else None,
        "qtc_interval": round(qtc_interval, 3) if qtc_interval else None,
        "beat_count": len(r_peaks),
        "signal_duration": round(len(signal) / sampling_rate, 1),
    }

    finding, status, flags = diagnose(params)

    return {
        "params": params,
        "finding": finding,
        "status": status,
        "flags": flags,
        "rpeaks": r_peaks,
        "cleaned_signal": cleaned,
    }


def _mean_paired_interval(starts, ends, sampling_rate):
    """Pairs each start marker with the nearest following end marker on
    the same beat and averages the resulting interval, skipping beats
    where delineation failed (NaN / misaligned markers)."""
    if len(starts) == 0 or len(ends) == 0:
        return None

    intervals = []
    ends_sorted = np.sort(ends)
    for s in starts:
        candidates = ends_sorted[ends_sorted >= s]
        if len(candidates) == 0:
            continue
        e = candidates[0]
        interval = (e - s) / sampling_rate
        if 0 < interval < 1.0:  # sanity bound - discard bad delineation pairs
            intervals.append(interval)

    if not intervals:
        return None
    return float(np.mean(intervals))


def diagnose(params):
    """
    The Medical Rule Engine: compares calculated parameters against fixed
    clinical thresholds (config.NORMAL_RANGES) and produces a plain-language
    finding plus a status used to color-code reports.
    """
    flags = []

    def check(name, label):
        value = params.get(name)
        if value is None:
            return
        low, high = NORMAL_RANGES[name]
        if value < low:
            flags.append(f"{label} low ({value})")
        elif value > high:
            flags.append(f"{label} high ({value})")

    check("heart_rate", "Heart rate")
    check("pr_interval", "PR interval")
    check("qrs_duration", "QRS duration")
    check("qtc_interval", "QTc interval")

    if not flags:
        return "Normal sinus rhythm", "Stable", flags

    hr = params.get("heart_rate")
    if hr is not None:
        if hr > NORMAL_RANGES["heart_rate"][1]:
            primary = "Sinus tachycardia"
        elif hr < NORMAL_RANGES["heart_rate"][0]:
            primary = "Sinus bradycardia"
        else:
            primary = "Rhythm irregularity detected"
    else:
        primary = "Rhythm irregularity detected"

    return primary, "Review needed", flags
