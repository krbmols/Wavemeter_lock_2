import dash
from dash import html, dcc, clientside_callback, ClientsideFunction, Input, Output, State, callback
import dash_bootstrap_components as dbc
import os

dash.register_page(__name__, path='/log')

logs_dir = './logs/'

def get_last_lines(path, num_lines=30, encoding='utf-8'):
    if not os.path.exists(path):
        return "[File not found]"

    newline_count = 0
    chunk_size = 1024
    buffer = b''
    with open(path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        position = file_size

        while position > 0 and newline_count <= num_lines:
            read_size = min(chunk_size, position)
            position -= read_size
            f.seek(position)
            chunk = f.read(read_size)
            buffer = chunk + buffer
            newline_count = buffer.count(b'\n')

        # Now decode and split only the last lines
        text = buffer.decode(encoding, errors='replace')
        lines = text.splitlines()[-num_lines:]
        lines.reverse()
        return '\n'.join(lines)

layout = dbc.Container([
    html.Div(id ='uuid-display', children='', className='text-center display-6 mb-2'),
    html.Pre(id='log-display', children=''),
    dcc.Interval(id='log-page-load', interval=100, n_intervals=0, max_intervals=0)
])

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='display_uuid'
    ),
    Output('uuid-display', 'children'),
    Input('log-page-load', 'n_intervals'),
    State('uuid', 'data')
)

@callback(
    Output('log-display', 'children'),
    Input('log-page-load', 'n_intervals'),
    State('uuid', 'data')
)
def display_log(n_intervals, uuid):
    fname = logs_dir + uuid + '.txt'
    return get_last_lines(fname)