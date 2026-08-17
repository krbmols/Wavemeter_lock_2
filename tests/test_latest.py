"""Offline checks for lib/latest.py, run without a wavemeter attached.

    python -m tests.test_latest

The fixture mimics the real acquisition: a fiber switch stepping at 500 Hz
across several lasers, with the Bristol read at ~1 kHz, so every laser appears
interleaved through one flat measurement stream.
"""

import sys
import numpy as np

sys.path.insert(0, '.')

from lib.latest import latest_frequencies, latest_near

SWITCH_HZ = 500.0
SAMPLE_HZ = 1000.0
LASERS = [282286.064, 309602.626, 434922.336, 508848.922]

failures = []


def check(name, condition, detail=''):
    if condition:
        print('  ok   %s' % name)
    else:
        print('  FAIL %s %s' % (name, detail))
        failures.append(name)


def make_stream(now, seconds=2.0, jitter_MHz=2.0, dark=(), seed=0,
                drift_GHz=0.0, drifting=None):
    """Interleaved measurements, newest at the end, as get_all_cached returns.

    ``drift_GHz`` moves ``drifting`` off its nominal frequency and, as the real
    calibration loop does when that laser is the calibration reference, hides
    the excursion from the calibrated array while leaving it in the raw one.
    """
    rng = np.random.default_rng(seed)
    n = int(seconds * SAMPLE_HZ)
    times = now - np.arange(n)[::-1] / SAMPLE_HZ

    freqs, raw_freqs, amps = [], [], []
    for t in times:
        # Which switch position is selected at this instant.
        laser = LASERS[int(t * SWITCH_HZ) % len(LASERS)]
        noise = rng.normal(0, jitter_MHz * 1e-3)
        shift = drift_GHz if laser == drifting else 0.0
        raw_freqs.append(laser + shift + noise)
        freqs.append(laser + noise)
        amps.append(0.02 if laser in dark else 0.6)

    statuses = [0] * n
    return np.array(freqs), np.array(raw_freqs), np.array(amps), statuses, times


now = 1_700_000_000.0

print('all lasers present')
stream = make_stream(now)
found = latest_frequencies(*stream, now)
check('one entry per laser', len(found) == len(LASERS),
      '(got %d)' % len(found))
check('frequencies match', sorted(round(f['freq_GHz']) for f in found)
      == sorted(round(f) for f in LASERS))
check('samples averaged', all(f['n'] > 1 for f in found),
      '(n = %s)' % [f['n'] for f in found])
check('jitter recovered', all(0.5 < f['std_MHz'] < 5 for f in found),
      '(std = %s)' % ['%.1f' % f['std_MHz'] for f in found])
check('fresh', all(f['age_s'] < 0.05 for f in found),
      '(age = %s)' % ['%.3f' % f['age_s'] for f in found])
check('wavelength sane', all(400 < f['wavelength_nm'] < 1200 for f in found),
      '(nm = %s)' % ['%.0f' % f['wavelength_nm'] for f in found])

print('a dark laser is dropped')
found = latest_frequencies(*make_stream(now, dark=(LASERS[1],)), now)
check('dark laser absent', len(found) == len(LASERS) - 1,
      '(got %d)' % len(found))
check('others still present',
      all(abs(f['freq_GHz'] - LASERS[1]) > 1 for f in found))

print('stale data is dropped')
stale = make_stream(now - 30.0)
check('nothing returned', latest_frequencies(*stale, now) == [])
check('near query misses',
      latest_near(*stale, now, LASERS[0], 1.0) is None)

print('empty cache')
empty = (np.array([]), np.array([]), np.array([]), [], np.array([]))
check('listing empty', latest_frequencies(*empty, now) == [])
check('near query None', latest_near(*empty, now, LASERS[0], 1.0) is None)

print('targeted query')
stream = make_stream(now)
target = LASERS[2]
one = latest_near(*stream, now, target, 1.0)
check('found', one is not None)
check('right laser', abs(one['median_GHz'] - target) < 0.01,
      '(got %.3f)' % one['median_GHz'])
check('detuning small', abs(one['detuning_MHz']) < 5,
      '(got %.2f MHz)' % one['detuning_MHz'])
check('target echoed', one['target_GHz'] == target and one['tol_GHz'] == 1.0)

print('targeted query with a laser offset from the setpoint')
offset = target - 0.4  # setpoint 400 MHz below where the laser sits
one = latest_near(*stream, now, offset, 1.0)
check('still inside a 1 GHz window', one is not None)
check('detuning reports the offset', abs(one['detuning_MHz'] - 400) < 10,
      '(got %.1f MHz)' % one['detuning_MHz'])
one = latest_near(*stream, now, target - 5.0, 1.0)
check('outside the window is a miss', one is None)

print('a neighbouring laser does not leak into the window')
close = list(LASERS)
one = latest_near(*stream, now, LASERS[0], 0.05)
check('only the targeted laser', one is not None
      and abs(one['median_GHz'] - LASERS[0]) < 0.05)

print("a drifting calibration laser is visible only in the raw frequency")
drifted = make_stream(now, drift_GHz=0.05, drifting=LASERS[1])  # +50 MHz
calibrated = latest_near(*drifted, now, LASERS[1], 0.5)
raw = latest_near(*drifted, now, LASERS[1], 0.5, use_raw=True)
check('calibrated reading looks on-setpoint',
      abs(calibrated['detuning_MHz']) < 5,
      '(got %.1f MHz)' % calibrated['detuning_MHz'])
check('raw reading shows the drift',
      abs(raw['detuning_MHz'] - 50) < 5,
      '(got %.1f MHz)' % raw['detuning_MHz'])
check('both frequencies reported either way',
      abs(calibrated['raw_freq_GHz'] - raw['raw_freq_GHz']) < 0.01
      and abs(calibrated['freq_GHz'] - raw['freq_GHz']) < 0.01)
check('selection labelled',
      calibrated['used'] == 'calibrated' and raw['used'] == 'raw')

print('raw and calibrated agree for every other laser')
one = latest_near(*drifted, now, LASERS[2], 0.5, use_raw=True)
check('undrifted laser unaffected', abs(one['detuning_MHz']) < 5,
      '(got %.1f MHz)' % one['detuning_MHz'])

print('json-safe types')
one = latest_near(*stream, now, target, 1.0)
one = latest_near(*stream, now, target, 1.0)
check('plain python scalars',
      all(isinstance(v, (float, int, str, type(None))) for v in one.values()),
      '(%s)' % {k: type(v).__name__ for k, v in one.items()})

print()
if failures:
    print('%d check(s) failed: %s' % (len(failures), ', '.join(failures)))
    sys.exit(1)
print('all checks passed')
