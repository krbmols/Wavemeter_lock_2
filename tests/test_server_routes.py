"""Smoke test for the /api/latest route, run without a wavemeter attached.

    python -m tests.test_server_routes

Stubs the Bristol serial device with a synthetic 500 Hz fiber switch, boots the
real Dash/Flask app, and exercises the route through Flask's test client.  Set
WAVEMETER_LOGS_DIR and WAVEMETER_SAVE_DIR to keep the app's output out of the
working tree.
"""

import json
import os
import sys
import time

sys.path.insert(0, '.')

try:
    import dash  # noqa: F401
except ImportError:
    print('dash is not installed; skipping (pip install -r requirements.txt)')
    sys.exit(0)

C = 299792458.0
SWITCH_HZ = 500.0

# 309602.628 is the calibration laser in data/current_calibration.yml, so it is
# the one whose drift the calibration correction hides.  Start it on setpoint.
CALIB_LASER = 309602.628
LASERS = [CALIB_LASER, 434922.336, 508848.922]

# Nudged at runtime to drift the calibration laser mid-test.
drift_GHz = 0.0

failures = []


def check(name, condition, detail=''):
    if condition:
        print('  ok   %s' % name)
    else:
        print('  FAIL %s %s' % (name, detail))
        failures.append(name)


class FakeBristol:
    """Stands in for BristolRS422: one head, lasers multiplexed by the switch."""

    def __init__(self, port_number):
        self.serial_port = None

    def get_measurement(self):
        now = time.time()
        freq = LASERS[int(now * SWITCH_HZ) % len(LASERS)]
        if freq == CALIB_LASER:
            freq += drift_GHz
        # (wavelength nm, saturation, status word, scan index)
        return C / freq, 0.6, 4, 0


import lib.wavemeter
lib.wavemeter.BristolRS422 = FakeBristol

os.environ.setdefault('WAVEMETER_LOGS_DIR', '/tmp/wm-test/logs')
os.environ.setdefault('WAVEMETER_SAVE_DIR', '/tmp/wm-test/save')

import server

client = server.app.server.test_client()

# Let the acquisition worker fill the ring buffer.
time.sleep(0.5)

print('listing every laser')
res = client.get('/api/latest')
check('200', res.status_code == 200, '(got %d)' % res.status_code)
body = json.loads(res.data)
check('json parses', 'lasers' in body)
found = body.get('lasers', [])
check('one entry per laser', len(found) == len(LASERS), '(got %d)' % len(found))
# Served frequencies carry the calibration correction the acquisition worker
# applies (data/current_calibration.yml), which is what a lock loop wants, so
# compare against the nominal values with room for it.
got = sorted(f['freq_GHz'] for f in found)
check('frequencies match',
      all(abs(a - b) < 0.02 for a, b in zip(got, sorted(LASERS))),
      '(got %s)' % ['%.3f' % f for f in got])
check('fresh', all(f['age_s'] < 0.5 for f in found))

print('targeted query')
res = client.get('/api/latest?freq=%f&tol=1.0' % LASERS[1])
check('200', res.status_code == 200)
body = json.loads(res.data)
check('found', body.get('found') is True, '(%s)' % body.get('reason'))
check('right laser', abs(body['laser']['median_GHz'] - LASERS[1]) < 0.01)
check('detuning present', 'detuning_MHz' in body['laser'])

print('targeted query that misses')
res = client.get('/api/latest?freq=100000&tol=1.0')
body = json.loads(res.data)
check('200 not error', res.status_code == 200)
check('found false', body.get('found') is False)
check('laser null', body.get('laser') is None)
check('reason given', bool(body.get('reason')))

print('bad input')
check('non-numeric rejected',
      client.get('/api/latest?freq=abc&tol=1').status_code == 400)
check('freq without tol rejected',
      client.get('/api/latest?freq=500000').status_code == 400)
check('n < 1 rejected', client.get('/api/latest?n=0').status_code == 400)

print('a drifting calibration laser')
# Everything above ran with the laser on setpoint.  Move it 50 MHz and let the
# correction converge on the new offset, as it would if the laser unlocked.
drift_GHz = 0.05
time.sleep(0.5)

res = client.get('/api/latest?freq=%f&tol=0.5' % CALIB_LASER)
calibrated = json.loads(res.data)['laser']
res = client.get('/api/latest?freq=%f&tol=0.5&raw=1' % CALIB_LASER)
raw = json.loads(res.data)['laser']

check('both found', calibrated is not None and raw is not None)
check('calibrated reading looks on-setpoint',
      abs(calibrated['detuning_MHz']) < 10,
      '(got %.1f MHz -- the correction absorbed the drift)'
      % calibrated['detuning_MHz'])
check('raw reading shows the drift',
      abs(raw['detuning_MHz'] - 50) < 10,
      '(got %.1f MHz)' % raw['detuning_MHz'])
check('selection labelled',
      calibrated['used'] == 'calibrated' and raw['used'] == 'raw')
check('both frequencies always present',
      'raw_freq_GHz' in calibrated and 'freq_GHz' in raw)
check('listing reports which it used',
      json.loads(client.get('/api/latest?raw=1').data)['using'] == 'raw')

drift_GHz = 0.0

print('the /data route still works')
res = client.get('/data')
check('200', res.status_code == 200)
check('history intact', len(json.loads(res.data)['freqs']) > 10)

print('the Latest page renders')
res = client.get('/latest')
check('200', res.status_code == 200, '(got %d)' % res.status_code)

print()
if failures:
    print('%d check(s) failed: %s' % (len(failures), ', '.join(failures)))
    sys.exit(1)
print('all checks passed')
