"""Latest-value extraction from the wavemeter measurement cache.

The wavemeter produces a single flat stream of measurements: a fiber switch
cycles the lasers through one Bristol head at 500 Hz, so consecutive samples in
``Wavemeter``'s ring buffer belong to *different* lasers.  Nothing in the
measurement identifies which laser it came from -- lasers are told apart by
frequency alone, exactly as the browser does in ``assets/utils.js``
(``calcFreqOptions``) and as the CSV logger does in ``lib/dataSaver.py``.

This module walks the buffer newest-first and reports only the most recent
sample of each distinct frequency, so a client can read one number per laser
instead of the whole 2000-sample history served by ``/data``.

The functions here are pure -- they take the arrays returned by
``Wavemeter.get_all_data()`` and no hardware -- so they can be exercised
without a wavemeter attached.
"""

import numpy as np

# Speed of light, m/s.  Frequencies are GHz throughout, wavelengths nm, which
# makes ``freq_GHz = C / wavelength_nm`` (as in lib/wavemeter.py).
C = 299792458.0

# Two samples closer together than this are taken to be the same laser.
# Matches the 10 MHz grouping lib/dataSaver.py uses when writing the CSV log.
DEFAULT_CLUSTER_TOL_GHZ = 0.01

# Below this saturation a reading is noise, not light.  Also from dataSaver.
DEFAULT_MIN_AMP = 0.05

# Ignore anything older than this.  The switch revisits a given laser every
# (n_channels x 2 ms), so a laser that is actually present is never more than a
# few tens of ms stale; a full second means "gone", not "slow".
DEFAULT_MAX_AGE_S = 1.0

# How many of the newest samples per laser to reduce for the median/jitter.
DEFAULT_N_AVERAGE = 10


def _usable_indices(freqs, amps, times, now, min_amp, max_age_s):
    """Indices of live, bright-enough samples, newest first."""
    order = np.argsort(times)[::-1]
    fresh = (now - times[order] <= max_age_s) & (amps[order] >= min_amp)
    return order[fresh]


def _summarise(freqs, amps, statuses, times, idxs, now):
    """Build the report for one laser from its sample indices, newest first."""
    newest = idxs[0]
    values = freqs[idxs]
    freq = float(freqs[newest])
    status = statuses[newest]

    return {
        'freq_GHz': freq,
        # The median is what a client should lock against: it rejects the
        # occasional bad read without lagging like a mean over a long window.
        'median_GHz': float(np.median(values)),
        'std_MHz': float(np.std(values) * 1e3) if len(values) > 1 else 0.0,
        'n': int(len(idxs)),
        'wavelength_nm': C / freq if freq else None,
        'amp': float(amps[newest]),
        'status': int(status) if status is not None else None,
        'time': float(times[newest]),
        'age_s': float(now - times[newest]),
    }


def latest_frequencies(freqs, amps, statuses, times, now,
                       cluster_tol_GHz=DEFAULT_CLUSTER_TOL_GHZ,
                       min_amp=DEFAULT_MIN_AMP,
                       max_age_s=DEFAULT_MAX_AGE_S,
                       n_average=DEFAULT_N_AVERAGE):
    """Latest reading of every laser currently on the wavemeter.

    Returns a list of report dicts, brightest-recent first in discovery order
    (i.e. ordered by how recently each laser was sampled).
    """
    freqs, amps, times = np.asarray(freqs, dtype=float), \
        np.asarray(amps, dtype=float), np.asarray(times, dtype=float)

    if len(freqs) == 0:
        return []

    clusters = []       # newest frequency seen for each laser
    members = []        # sample indices belonging to it, newest first

    for i in _usable_indices(freqs, amps, times, now, min_amp, max_age_s):
        for k, seed in enumerate(clusters):
            if abs(freqs[i] - seed) < cluster_tol_GHz:
                if len(members[k]) < n_average:
                    members[k].append(i)
                break
        else:
            clusters.append(freqs[i])
            members.append([i])

    return [_summarise(freqs, amps, statuses, times, idxs, now)
            for idxs in members]


def latest_near(freqs, amps, statuses, times, now, target_GHz, tol_GHz,
                min_amp=DEFAULT_MIN_AMP,
                max_age_s=DEFAULT_MAX_AGE_S,
                n_average=DEFAULT_N_AVERAGE):
    """Latest reading within ``tol_GHz`` of ``target_GHz``, or None.

    This is the query a lock loop wants: one request answers "where is my laser
    right now, and is it still inside my window?".  ``detuning_MHz`` is measured
    from the median, signed so that positive means above the target.
    """
    freqs, amps, times = np.asarray(freqs, dtype=float), \
        np.asarray(amps, dtype=float), np.asarray(times, dtype=float)

    if len(freqs) == 0:
        return None

    idxs = [i for i in _usable_indices(freqs, amps, times, now, min_amp, max_age_s)
            if abs(freqs[i] - target_GHz) <= tol_GHz][:n_average]

    if not idxs:
        return None

    report = _summarise(freqs, amps, statuses, times, idxs, now)
    report['target_GHz'] = float(target_GHz)
    report['tol_GHz'] = float(tol_GHz)
    report['detuning_MHz'] = (report['median_GHz'] - float(target_GHz)) * 1e3
    return report
