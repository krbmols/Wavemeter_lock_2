import dash
from dash import Dash, html, dcc, callback, Input, Output, State, Patch, ALL, MATCH, ctx, no_update, clientside_callback, ClientsideFunction
import dash_bootstrap_components as dbc
from lib.wavemeter import Wavemeter
from lib.dataSaver import DataSaver
from lib.latest import latest_frequencies, latest_near, DEFAULT_CLUSTER_TOL_GHZ, \
    DEFAULT_MIN_AMP, DEFAULT_MAX_AGE_S, DEFAULT_N_AVERAGE
import numpy as np
import signal
import sys
import yaml
import os
from flask import request, jsonify
from datetime import datetime
from time import time as unix_time
import atexit

# cur_targets = np.array([750000, 713289.100, 650000, 508848.922, 508848.402, 508332.499, 467044.500, 462900, 445000, 434912.747, 391016, 365753, 328966, 320008.235, 309602.628, 296387, 282288.730])
cur_targets = np.array([508848.922, 508332.499, 309602.628, 296387, 282288.730])
calib_profile_file = './data/calibration.yml'
curr_calib_file = './data/current_calibration.yml'
# Both may be overridden by the environment so the app can be run somewhere
# other than the wavemeter PC (a test box, a spare machine) without editing it.
logs_dir = os.environ.get('WAVEMETER_LOGS_DIR', './logs/')
save_directory = os.environ.get('WAVEMETER_SAVE_DIR', "C:\\Users\\Krb-Logging\\wavemeter")
# save_directory = '.'

res_name = 'Calibration: None'
calib_freq = None
calib_tol = None
if os.path.exists(curr_calib_file):
    with open(curr_calib_file, 'r') as f:
        data = yaml.safe_load(f) or {}
    if 'name' in data:
        res_name = 'Calibration: ' + data['name']
        calib_freq = data['freq']
        calib_tol = data['tol']

app = Dash(title='Fast Wavemeter', update_title=None, prevent_initial_callbacks="initial_duplicate", external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True)
# wavemeter = Wavemeter(targets=cur_targets, calibration=calib_freq, calibration_tol=calib_tol)
wavemeter = Wavemeter(port='COM10', cache_n_measurements = 2000, calibration=calib_freq, calibration_tol=calib_tol)
# Neither directory is created anywhere else, and both are written to as soon
# as a browser connects, so make sure they exist before the workers start.
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(save_directory, exist_ok=True)

ds = DataSaver(wavemeter, save_directory)
# wavemeter = Wavemeter(targets=np.array([713289.100, 650000, 508848.922]))

calib_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Change/Edit Calibration")),
                dbc.ModalBody([
                    dbc.Row([
                        dbc.Col([html.Div('Calibrations loaded from ' + calib_profile_file, className='h-100 w-100 text-wrap text-center mb-2')])
                    ]),
                    dcc.Dropdown(
                        id='calibration-selector',
                        options=[],
                        placeholder="Select a preset calibration",
                        multi=False,
                        className='mb-2'
                    ),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Calibration name:', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='calib-name', placeholder='Enter name', type='text', value='', className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Calibration frequency (GHz):', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='calib-freq', placeholder='Enter frequency', type='number', value=0, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Calibration tolerance (GHz):', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='calib-tol', placeholder='Enter tolerance', type='number', value=0.5, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center')
                ]),
                dbc.ModalFooter([
                    dbc.Button("Use", id="use-calib", className="ms-auto", n_clicks=0),
                    dbc.Button("Save and Use", id='save-and-use-calib', n_clicks=0),
                    dbc.Button("Cancel", id='cancel-calib', n_clicks=0),
                    dbc.Button("Delete", id='delete-calib', n_clicks=0, color='danger')
                ]),
            ],
            id="change-laser-calib",
            is_open=False,
        ),
    ]
)

msg_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(id='msg_title', children="Message")),
                dbc.ModalBody([
                    html.Div(id='msg_content', children=[])
                ]),
                dbc.ModalFooter([
                    dbc.Button("Close", id='close-msg', n_clicks=0)
                ]),
            ],
            id="msg_modal",
            is_open=False,
        ),
    ]
)

app.layout = dbc.Container([
    dbc.Row([html.Div('Fast Wavemeter', className='text-center display-3 fw-bold mb-4')]),
    dbc.Row([dbc.Col([dbc.Nav([dbc.NavItem(dbc.NavLink("Home", active='exact', href="/")),
             dbc.NavItem(dbc.NavLink("Help", active='exact', href="/help")),
             dbc.NavItem(dbc.NavLink("Latest", active='exact', href="/latest")),
             dbc.NavItem(dbc.NavLink("Log", active='exact', href="/log"))
    ], pills=True, fill=True, justified=True)], width={'size': 4, 'offset': 4})]),
    html.Hr(className="my-4 mx-auto w-75 border border-2 border-secondary"),
    html.Div(id = 'all-current-freqs', children='', className='text-center mb-2 text-wrap'),
    dbc.Row([dbc.Col(html.Div(id = 'wm-error-text', children='', className='text-center mb-2 text-wrap wm-error-text')),
             dbc.Col(dbc.Button('Change Laser Calibration', id = 'change-laser-calib-btn', n_clicks=0, className='calibration-btn-text')),
             dbc.Col(html.Div(id = 'curr-calibration', children='', className='mb-2 text-wrap calibration-title-text'))
    ]),
    calib_modal,
    msg_modal,
    html.Div(dash.page_container, style={
        'margin': '0 auto',
        'padding': '0',
        'maxWidth': '100%',  # or set to '1200px' or desired max width
        'width': '100%',
    }, className = 'mt-2'),
    dcc.Interval(id='get_wm_data', interval=100),
    dcc.Interval(id='get_wm_err_data', interval=1000), # Poll for this less often
    dcc.Interval(id='update_all_freqs_display', interval=1000),
    dcc.Interval(id='server-page-load', interval=100, n_intervals=0, max_intervals=0),
    dcc.Store(id='wm_data', storage_type='local'),
    dcc.Store(id='wm_err_data', storage_type='local'),
    dcc.Store(id='calib_cache', storage_type='local'),
    dcc.Interval(id='get-uuid', interval=1, n_intervals=0, max_intervals=0),
    dcc.Store(id='uuid', storage_type='local'),
    dcc.Store(id={'type': 'log-msg', 'index': -1}, storage_type='local')
], fluid=True)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='get_uuid'
    ),
    Output('uuid', 'data'),
    Input('get-uuid', 'n_intervals'),
    State('uuid', 'data')
)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_all_freqs_display'
    ),
    Output('all-current-freqs', 'children'),
    Input('update_all_freqs_display', 'n_intervals'),
    State('wm_data', 'data')
)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_wm_error_display'
    ),
    Output('wm-error-text', 'children'),
    Input('wm_err_data', 'data')
)

@callback(
    Output('wm_data', 'data'),
    Input('get_wm_data', 'n_intervals')
)
def update_wm_data(n_intervals):
    freqs, amps, statuses, times = wavemeter.get_all_data()
    # print(len(times))
    return [freqs, amps, statuses, times]

@app.server.route('/data', methods=['GET'])
def serve_wm_data():
    freqs, amps, statuses, times = wavemeter.get_all_data()
    result = dict()
    result['freqs'] = freqs.tolist()
    result['amps'] = amps.tolist()
    result['statuses'] = statuses
    result['times'] = times.tolist()
    return jsonify(result)

def _float_arg(name, default):
    raw = request.args.get(name)
    if raw is None or raw == '':
        return default
    return float(raw)


@app.server.route('/api/latest', methods=['GET'])
def serve_latest_data():
    """The most recent reading of each laser, rather than the whole history.

    ``/data`` hands back the entire 2000-sample cache and leaves the caller to
    work out which samples belong to which laser.  This route does that work
    server-side so a lock loop can poll one small document:

        GET /api/latest
            -> every distinct frequency currently on the wavemeter

        GET /api/latest?freq=508848.92&tol=1.0
            -> just the laser within 1 GHz of 508848.92 GHz, with its detuning

    Optional in both forms: ``max_age`` (s), ``min_amp``, ``n`` (samples to
    reduce for the median), and ``cluster_tol`` (GHz) for the listing form.
    """
    try:
        max_age_s = _float_arg('max_age', DEFAULT_MAX_AGE_S)
        min_amp = _float_arg('min_amp', DEFAULT_MIN_AMP)
        n_average = int(_float_arg('n', DEFAULT_N_AVERAGE))
        cluster_tol = _float_arg('cluster_tol', DEFAULT_CLUSTER_TOL_GHZ)
        target = _float_arg('freq', None)
        tol = _float_arg('tol', None)
    except ValueError:
        return jsonify({'error': 'query parameters must be numeric'}), 400

    if n_average < 1:
        return jsonify({'error': 'n must be at least 1'}), 400
    if target is not None and tol is None:
        return jsonify({'error': 'freq requires tol'}), 400

    freqs, amps, statuses, times = wavemeter.get_all_data()
    now = unix_time()

    calib_err = wavemeter.get_wavemeter_error()
    result = {
        'time': now,
        'max_age_s': max_age_s,
        'min_amp': min_amp,
        'calibration_error_MHz': None if calib_err is None else calib_err * 1e3,
    }

    if target is None:
        result['lasers'] = latest_frequencies(
            freqs, amps, statuses, times, now,
            cluster_tol_GHz=cluster_tol, min_amp=min_amp,
            max_age_s=max_age_s, n_average=n_average
        )
    else:
        laser = latest_near(
            freqs, amps, statuses, times, now, target, tol,
            min_amp=min_amp, max_age_s=max_age_s, n_average=n_average
        )
        # A miss is a normal answer -- the laser may simply be dark -- so it is
        # reported as found=false rather than as an HTTP error.
        result['found'] = laser is not None
        result['laser'] = laser
        if laser is None:
            result['reason'] = (
                'no reading within %g GHz of %g GHz in the last %g s'
                % (tol, target, max_age_s)
            )

    return jsonify(result)

@callback(
    Output('wm_err_data', 'data'),
    Output('curr-calibration', 'children'),
    Input('get_wm_err_data', 'n_intervals')
)
def update_wm_err_data(n_intervals):
    res = wavemeter.get_wavemeter_error()
    res_name = 'Calibration: None'
    if os.path.exists(curr_calib_file):
        with open(curr_calib_file, 'r') as f:
            data = yaml.safe_load(f) or {}
        if 'name' in data:
            res_name = 'Calibration: ' + data['name']
    return res, res_name

@callback(
    Output('change-laser-calib', 'is_open', allow_duplicate=True),
    Output('calibration-selector', 'options'),
    Output('calibration-selector', 'value'),
    Output('calib_cache', 'data'),
    Input('change-laser-calib-btn', 'n_clicks'),
    Input('cancel-calib', 'n_clicks'),
    prevent_initial_call = True
)
def open_laser_calib_modal(open_btn, cancel_btn):
    triggered_id = ctx.triggered_id
    if (triggered_id == 'cancel-calib'):
        return 0, no_update, no_update, no_update
    elif (triggered_id == 'change-laser-calib-btn'):
        if os.path.exists(calib_profile_file):
            with open(calib_profile_file, 'r') as f:
                data = yaml.safe_load(f) or None
        else:
            data = None
        ret_options = ['Add new laser']
        if data:
            for key, value in data.items():
                if isinstance(value, dict) and ('freq_GHz' in value) and ('tol_GHz' in value):
                    ret_options.append(key)
        ret_options.append('No calibration')
        return 1, ret_options, 'Add new laser', data
    else:
        return no_update, no_update, no_update, no_update
    
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_calib_options'
    ),
    Output('calib-name', 'value'),
    Output('calib-freq', 'value'),
    Output('calib-tol', 'value'),
    Input('calibration-selector', 'value'),
    State('calib_cache', 'data')
)

@callback(
    Output('change-laser-calib', 'is_open', allow_duplicate=True),
    Input('use-calib', 'n_clicks'),
    Input('save-and-use-calib', 'n_clicks'),
    Input('delete-calib', 'n_clicks'),
    State('calibration-selector', 'value'),
    State('calib-name', 'value'),
    State('calib-freq', 'value'),
    State('calib-tol', 'value'),
    prevent_initial_call=True
)
def use_new_calibration(btn1, btn2, btn3, selected_value, name, freq, tol):
    triggered_id = ctx.triggered_id
    if (triggered_id == 'delete-calib'):
        if (selected_value == 'No calibration') or (selected_value == 'Add new laser'):
            return 0
        else:
            if os.path.exists(calib_profile_file):
                with open(calib_profile_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
                if selected_value in data:
                    del data[selected_value]
                with open(calib_profile_file, 'w') as f:
                    yaml.dump(data, f)
                return 0
            else:
                return 0


    if (selected_value == 'No calibration'):
        wavemeter.set_calibration(None, None)
        res_name = 'None'
    else:
        wavemeter.set_calibration(freq, tol)
        res_name = name
    
    info = dict()
    info['name'] = res_name
    info['freq'] = freq
    info['tol'] = tol
    with open(curr_calib_file, 'w') as f:
        yaml.dump(info, f)
    if (triggered_id == 'use-calib'):
        return 0

    if selected_value != "No calibration":
        # Here, we need to save the data
        if os.path.exists(calib_profile_file):
            with open(calib_profile_file, 'r') as f:
                    data = yaml.safe_load(f) or {}
        else:
            data = {}

        if name in data:
            data[name]['freq_GHz'] = freq
            data[name]['tol_GHz'] = tol
        else:
            new_dict = {}
            new_dict['freq_GHz'] = freq
            new_dict['tol_GHz'] = tol
            data[name] = new_dict

        # Step 3: Write back to YAML
        with open(calib_profile_file, 'w') as f:
            yaml.dump(data, f)
    return 0

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='close_msg'
    ),
    Output('msg_modal', 'is_open', allow_duplicate=True),
    Input('close-msg', 'n_clicks'),
    prevent_initial_call=True
)

@callback(
    Input({'type': 'log-msg', 'index': ALL}, 'data'),
    State('uuid', 'data'),
    prevent_initial_call=True
)
def append_to_log_file(msgs, uuid):
    if uuid is not None:
        fname = logs_dir + uuid + '.txt'
        current_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        triggered_id = ctx.triggered_id
        if triggered_id is None:
            return
        all_inputs = ctx.inputs_list[0]
        for i, input_obj in enumerate(all_inputs):
            if input_obj['id'] == triggered_id:
                msg = msgs[i]
        if msg is None:
            return
        with open(fname, 'a+') as f:
            f.write(current_time + ', ' + msg + "\n")

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='browser_open_msg'
    ),
    Output({'type': 'log-msg', 'index': -1}, 'data', allow_duplicate=True),
    Input('server-page-load', 'n_intervals'),
    prevent_initial_call=True
)

def cleanup():
    global wavemeter
    wavemeter.stop_worker()
    global ds
    ds.stop_worker()
    sys.exit(0)

# signal.signal(signal.SIGINT, cleanup)
atexit.register(cleanup)

# Run the app
if __name__ == '__main__':
    try:
        app.run(debug=False, use_reloader=False)
    except:
        cleanup()
