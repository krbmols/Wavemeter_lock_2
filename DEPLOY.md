# Deploying the wavemeter server

The app is a Dash (Flask) application that reads the Bristol wavemeter over
RS-422 and serves both a browser UI and a JSON API. Flask's built-in server is a
development server, so production runs behind **waitress** on the wavemeter PC,
with **nginx** on the KRb webserver reverse-proxying to it.

```
browser / linien  ->  nginx (192.168.0.116, wavemeter.nigrp.org)  ->  waitress (192.168.0.119:8050)  ->  Bristol on COM10
```

## 1. Wavemeter PC (192.168.0.119)

Create a virtual environment in the project directory:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

`requirements.txt` was frozen with `pip freeze` from a working install of
`dash numpy dash-bootstrap-components pyserial pyyaml waitress`.

Serve it:

```powershell
waitress-serve --port=8050 wgsi:server
```

`wgsi.py` exposes the Flask instance underneath the Dash app. waitress binds
`0.0.0.0` by default, so the server is reachable from the rest of the KRb
network — which is what nginx and the linien lock both need.

Notes that will bite otherwise:

- **Run it from the project directory.** `./data/profiles/`, `./data/calibration.yml`
  and the logs directory are all relative paths. If you later run this as a
  service (NSSM, or Task Scheduler with "run whether user is logged on or not")
  set the working directory explicitly.
- **Open TCP 8050 in Windows Firewall** for the local network, or nginx and the
  RedPitaya both get connection-refused even though waitress is listening.
- **Directories.** `server.py` creates its log directory and the CSV save
  directory at startup. Both default as before (`./logs/` and
  `C:\Users\Krb-Logging\wavemeter`) and can be overridden with the
  `WAVEMETER_LOGS_DIR` and `WAVEMETER_SAVE_DIR` environment variables.
- **The serial port is hardcoded** as `COM10` in `server.py`. Check it in Device
  Manager if the wavemeter comes up on a different port after a reboot.

## 2. KRb webserver (nilab@192.168.0.116)

Copy an existing site config and edit it:

```bash
cd /etc/nginx/sites-available
sudo cp ./labctrl-node.conf ./wavemeter.conf
```

```nginx
server {
    server_name wavemeter.nigrp.org;

    proxy_set_header X-Forwarded-For $remote_addr;

    location / {
        proxy_pass          http://192.168.0.119:8050;
        proxy_set_header    Host $host;
        proxy_set_header    X-Real-IP $remote_addr;
        proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header    X-Forwarded-Host $server_name;
        proxy_set_header    Upgrade $http_upgrade;
        proxy_set_header    Connection "upgrade";
        proxy_http_version  1.1;
        proxy_read_timeout  1200s;

        access_log      /var/log/nginx/wavemeter.access.log;
        error_log       /var/log/nginx/wavemeter.error.log;
    }
}
```

Enable it and reload:

```bash
cd /etc/nginx/sites-enabled
sudo ln -s ../sites-available/wavemeter.conf ./wavemeter.conf
sudo nginx -t          # always test before reloading
sudo nginx -s reload
```

`nginx -t` matters: a broken config reloads silently on some errors and then
fails to come back on the next restart.

## 3. HTTPS

The config above has no `listen` directive, so nginx falls back to port 80 —
plain HTTP. Once DNS for `wavemeter.nigrp.org` points at the KRb webserver, run:

```bash
sudo certbot --nginx -d wavemeter.nigrp.org
```

Certbot adds the `listen 443 ssl`, the certificate paths and the port-80 → 443
redirect block, exactly as it did for `krb.nigrp.org`.

## 4. Access control

Once this is public, `/data` and `/api/latest` are world-readable: every laser
frequency in the lab, no authentication. If that is not wanted, keep the human
pages public and restrict the API to the lab network:

```nginx
location /api/ {
    allow 192.168.0.0/24;
    deny all;
    proxy_pass http://192.168.0.119:8050;
    # ... same proxy_set_header block as above
}
```

## API

| Route | Returns |
| --- | --- |
| `GET /data` | The entire measurement cache: `freqs`, `amps`, `statuses`, `times` (2000 samples, ~2 s). What the browser UI plots. |
| `GET /api/latest` | The most recent reading of each laser currently on the wavemeter. |
| `GET /api/latest?freq=<GHz>&tol=<GHz>` | Just the laser within `tol` of `freq`, including its signed `detuning_MHz`. |

Nothing in a measurement says which laser it came from — the fiber switch
multiplexes them all through one head at 500 Hz — so lasers are separated by
frequency, the same way `assets/utils.js` and `lib/dataSaver.py` do it.
`/api/latest` does that server-side so a lock loop can poll one small document
instead of the whole history.

Optional query parameters: `max_age` (s, default 1.0), `min_amp` (default 0.05),
`n` (samples reduced for the median, default 10), and `cluster_tol` (GHz,
default 0.01) for the listing form.

A frequency is reported as the newest sample (`freq_GHz`) and as the median of
the newest `n` (`median_GHz`, with `std_MHz` as the spread). Lock against the
median: it rejects the occasional bad read without lagging. Frequencies carry
the calibration correction from `data/current_calibration.yml`.

`found: false` from the targeted form is a normal answer, not an error — the
laser may simply be dark. Callers should treat it as "unknown", not "off
resonance".

### For the linien wavemeter lock

Poll the LAN address directly:

```
http://192.168.0.119:8050/api/latest?freq=508848.92&tol=1.0
```

not `https://wavemeter.nigrp.org`. The RedPitaya's CA bundle is old enough that
a Let's Encrypt chain may not validate, and going through nginx puts DNS and a
second machine in the path of the lock loop.

## Testing without hardware

```bash
python -m tests.test_latest          # the latest-value logic, no dependencies beyond numpy
python -m tests.test_server_routes   # boots the real app with a stubbed Bristol
```

Both simulate the 500 Hz fiber switch, so they can run anywhere.
