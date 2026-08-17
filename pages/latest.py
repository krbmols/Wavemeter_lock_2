"""Latest-value page: one row per laser, newest reading only.

The home page plots the history of lasers you have configured.  This page
configures nothing -- it shows whatever is on the wavemeter right now, one line
each, and is the human-readable twin of the ``/api/latest`` JSON route that
external lock loops poll.
"""

import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
from time import time

from lib.latest import latest_frequencies, DEFAULT_MAX_AGE_S

dash.register_page(__name__, path='/latest')

# The saturation below which utils.js already warns the user on the home page.
LOW_AMP = 0.1

REFRESH_MS = 500

COLUMNS = ['Frequency (GHz)', 'Wavelength (nm)', 'Jitter (MHz)',
           'Saturation', 'Age (ms)']


def _wavemeter():
    # Imported lazily: server.py builds the Dash app (which imports this
    # module) before it constructs the Wavemeter, so this cannot be a
    # module-level import.  By the time a callback runs, server is fully loaded.
    import server
    return server.wavemeter


layout = dbc.Container([
    html.Div('Latest reading of every laser currently on the wavemeter.',
             className='text-center text-muted mb-2'),
    html.Div(id='latest-table', children=''),
    html.Div([
        'Machine-readable: ',
        html.Code('/api/latest'),
        ' for all lasers, ',
        html.Code('/api/latest?freq=<GHz>&tol=<GHz>'),
        ' for one.'
    ], className='text-center text-muted mt-3'),
    dcc.Interval(id='latest-refresh', interval=REFRESH_MS)
], fluid=True)


@callback(
    Output('latest-table', 'children'),
    Input('latest-refresh', 'n_intervals')
)
def update_latest_table(n_intervals):
    freqs, amps, statuses, times = _wavemeter().get_all_data()
    lasers = latest_frequencies(freqs, amps, statuses, times, time())

    if not lasers:
        return html.Div(
            'No light on the wavemeter in the last %g s.' % DEFAULT_MAX_AGE_S,
            className='text-center fst-italic mt-4'
        )

    # Brightest-recent discovery order is arbitrary to look at; sort by
    # frequency so a laser keeps its row between refreshes.
    lasers.sort(key=lambda laser: laser['freq_GHz'])

    rows = []
    for laser in lasers:
        dim = laser['amp'] < LOW_AMP
        rows.append(html.Tr([
            html.Td('%.3f' % laser['freq_GHz'], className='fw-bold'),
            html.Td('%.1f' % laser['wavelength_nm']),
            html.Td('%.1f' % laser['std_MHz']),
            html.Td('%.1f%%' % (laser['amp'] * 100),
                    style={'backgroundColor': 'yellow'} if dim else None),
            html.Td('%.0f' % (laser['age_s'] * 1e3)),
        ]))

    return dbc.Table(
        [html.Thead(html.Tr([html.Th(name) for name in COLUMNS])),
         html.Tbody(rows)],
        bordered=True, hover=True, striped=True, className='w-75 mx-auto'
    )
