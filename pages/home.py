#TODO, check for blank names
#TODO, make paths OS independent

import dash
from dash import Dash, html, dcc, callback, Input, Output, State, Patch, ALL, MATCH, ctx, no_update, clientside_callback, ClientsideFunction
from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import numpy as np
import os
import yaml
from pathlib import Path

profile_dir = './data/profiles/'
users_file = './data/users.yml'

dash.register_page(__name__, path='/')

def create_default_figure(title = ''):
    default_figure = make_subplots()
    default_figure.update_layout(
        title=title,
        xaxis=dict(
            title="Time",
            showticklabels=False
        ),
        yaxis=dict(
            title="\u0394f MHz",
            fixedrange=False
        ),
        legend_title="Legend",
        margin=dict(l=20, r=0, t=20, b=20)
    )
    default_figure.add_trace(go.Scatter(x=[], y=[], mode='markers', name='Channel 1', type='scatter',
                        showlegend=False))
    return default_figure

def create_bar_figure(title = ''):
    figure = make_subplots()
    # default_figure.update_layout(
    #     title=title,
    #     xaxis=dict(
    #         title="Time",
    #         showticklabels=False
    #     ),
    #     yaxis=dict(
    #         title="Value",
    #         fixedrange=False
    #     ),
    #     legend_title="Legend",
    #     margin=dict(l=20, r=0, t=20, b=20)
    # )
    # default_figure.add_trace(go.Scatter(x=[], y=[], mode='markers', name='Channel 1', type='scatter',
    #                     showlegend=False))
    figure.add_trace(
        go.Bar(
            x=[],                  # No data
            y=[],                  # No categories
            orientation='h',       # Horizontal bars
            showlegend=False
        )
    )

    figure.update_layout(
        margin=dict(l=0, r=0, t=20, b=20)
    )

    return figure

def create_edit_modal(plot_id):
    return dbc.Modal(
                [
                    dbc.ModalHeader(dbc.ModalTitle(id = {'type': 'edit-laser-title', 'index': plot_id}, children="Edit Laser Information")),
                    dbc.ModalBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div('Laser name:', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Input(id={'type': 'laser-name-edit', 'index': plot_id}, placeholder='Enter name', type='text', value='', className='h-100 w-100')
                            ], width=6, className='h-100')
                        ], align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.Div('Laser center frequency (GHz):', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Input(id={'type': 'laser-center-freq-edit', 'index': plot_id}, placeholder='Enter frequency', type='number', value=0, className='h-100 w-100')
                            ], width=6, className='h-100')
                        ], align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.Div('Laser tolerance (GHz):', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Input(id={'type': 'laser-tol-edit', 'index': plot_id}, placeholder='Enter tolerance', type='number', value=1, className='h-100 w-100')
                            ], width=6, className='h-100')
                        ], align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.Div('Points in History:', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Input(id={'type': 'npts-input-edit', 'index': plot_id}, placeholder='Enter number of points in graph', type='number', value=100, className='h-100 w-100')
                            ], width=6, className='h-100')
                        ], align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.Div('Lock tolerance (MHz):', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Input(id={'type': 'lock-tol-edit', 'index': plot_id}, placeholder='Enter tolerance', type='number', value=5, className='h-100 w-100')
                            ], width=6, className='h-100')
                        ], align='center'),
                        dbc.Row([
                            dbc.Col([
                                html.Div('Track that laser is locked: ', className='h-100 w-100')
                            ], width=6, className='h-100'),
                            dbc.Col([
                                dbc.Checkbox(id = {'type': 'laser-lock-btn-edit', 'index': plot_id})
                            ], width=6, className='h-100')
                        ], align='center')
                    ]),
                    dbc.ModalFooter([
                        dbc.Button("Finish", id={'type' : "finish-laser-edit", 'index': plot_id}, className="ms-auto", n_clicks=0),
                        dbc.Button("Cancel", id={'type': 'cancel-laser-edit', 'index': plot_id}, n_clicks=0)
                    ]),
                ],
                id={'type': "edit-laser-dialog", 'index': plot_id},
                is_open=False,
            )

def create_new_block(plot_id, title='', name='', center_freq=508848.920, freq_tol=1, lock_tol_MHz = 5, n_pts=100, track_lock=False):
    info = dict()
    info['id'] = plot_id
    info['name'] = name
    info['f'] = center_freq
    info['df'] = freq_tol
    info['n_pts'] = n_pts
    info['edit_clicks'] = 0
    info['cur_amp'] = 0
    info['lock_status'] = track_lock
    info['lock_tol_MHz'] = lock_tol_MHz
    # At the moment, cur_lock_condition and lock_pt_counter is purely used for the log. 
    info['cur_lock_condition'] = track_lock
    info['lock_pt_counter'] = 5 # 5 consecutive points in the lock region is required, so upon creation, the lock condition is ready to be locked
    child = dbc.Row([
        dbc.Col([
            dbc.Row([
                dbc.Col([html.Div(id={'type': 'laser_title', 'index': plot_id}, children=name, className='h-100 laser-title-text d-flex justify-content-center align-items-center')]
                    , width=4),
                dbc.Col([html.Div(id={'type': 'freq_info', 'index': plot_id}, children=[], className='h-100', style= {'border-bottom': '3px solid black'})]
                    , width=8)],
                className='w-100 d-flex flex-grow-1'),  
            dbc.Row(dbc.Col([html.Div(id={'type': 'freq_digits', 'index': plot_id}, children=[], className='h-100 d-flex justify-content-center align-items-end justify-content-sm-end')], width=12
                    ), className= 'w-100'
                )
        ], className="d-flex flex-column h-100 justify-content-end align-items-center align-items-sm-end g-0", width=12, sm=6),
        dbc.Col([
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(id={'type': 'lock-btn', 'index': plot_id}, label=
                                 html.Div(id={'type': 'lock-btn-text', 'index': plot_id}, children='Unlock Alert (' + '\u00B1' + str(lock_tol_MHz) + ' MHz)', className='lock-tol-text'), value=track_lock)
                ], {'size': 3, 'offset': 4}),
                dbc.Col([
                    dbc.Button("Edit", id={'type': 'edit-btn', 'index': plot_id}, n_clicks=0, size='sm')
                ], width = {'size': 2, 'offset': 0}),
                dbc.Col([
                    dbc.Button("Delete", id={'type': 'delete-btn', 'index': plot_id}, n_clicks=0, size='sm', color='danger')
                ], width={'size': 3, 'offset': 0})
            ]),
            dbc.Row([dbc.Col(
                dcc.Graph(id={'type': 'data_plot', 'index': plot_id}, figure=create_default_figure(), mathjax=True,
                      config={
                        'scrollZoom': False,          # Disable zooming with mouse wheel
                        'displayModeBar': False,      # Disable the mode bar (toolbar)
                        'staticPlot': True,           # Disable panning, zooming, etc.
                        'displaylogo': False,         # Hide the Plotly logo
                        'showTips': False,            # Disable hover information
                        'editable': False,            # Disable editing of plot elements
                        'showAxisDragHandles': False, # Disable dragging of axes
                        'showAxisRangeEntry': False,   # Disable axis range entry boxes
                        'responsive': False
                    }, className = 'h-100'), width=8),
                    dbc.Col(
                        dcc.Graph(id={'type': 'bar_plot', 'index': plot_id}, figure=create_bar_figure(), mathjax=True,
                      config={
                        'scrollZoom': False,          # Disable zooming with mouse wheel
                        'displayModeBar': False,      # Disable the mode bar (toolbar)
                        'staticPlot': True,           # Disable panning, zooming, etc.
                        'displaylogo': False,         # Hide the Plotly logo
                        'showTips': False,            # Disable hover information
                        'editable': False,            # Disable editing of plot elements
                        'showAxisDragHandles': False, # Disable dragging of axes
                        'showAxisRangeEntry': False,   # Disable axis range entry boxes
                        'responsive': False
                    }, className = 'h-100'), width=4)
            ], className="plot-fig")
        ], className='d-flex flex-column justify-content-end g-0',width=12, sm=6),
        create_edit_modal(plot_id),
        dcc.Store(id={'type': 'laser-metadata', 'index': plot_id}, data=info, storage_type='memory'),
        dcc.Store(id={'type': 'log-msg', 'index': plot_id}, storage_type='memory')
    ], className='d-flex g-0 flex-row justify-content-center align-items-end')
    return child


modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Laser Information")),
                dbc.ModalBody([
                    html.P(id='laser-freq-options', children='', className='text-center suggestion-text text-wrap'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Laser name:', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='laser-name', placeholder='Enter name', type='text', value='', className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Laser center frequency (GHz):', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='laser-center-freq', placeholder='Enter frequency', type='number', value=0, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Laser tolerance (GHz):', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='laser-tol', placeholder='Enter tolerance', type='number', value=1, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Points in History:', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='npts-input', placeholder='Enter number of points in graph', type='number', value=100, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Lock tolerance (MHz):', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='lock-tol', placeholder='Enter tolerance', type='number', value=5, className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center'),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Track that laser is locked: ', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Checkbox(id = 'laser-lock-btn')
                        ], width=6, className='h-100')
                    ], align='center')

                    # dbc.Checkbox(id={'type': 'lock-btn', 'index': plot_id}
                ]),
                dbc.ModalFooter([
                    dbc.Button("Add", id="add-laser", className="ms-auto", n_clicks=0),
                    dbc.Button("Cancel", id='cancel-laser', n_clicks=0)
                ]),
            ],
            id="add-laser-dialog",
            is_open=False,
        ),
    ]
)

profile_modal = html.Div(
    [
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Load/Save Profile")),
                dbc.Row([
                        dbc.Col([html.Div('Profiles loaded from ' + profile_dir, className='h-100 w-100 text-wrap text-center mb-2')])
                    ]),
                dbc.ModalBody([
                    dcc.Dropdown(
                        id='profile-selector',
                        options=[],
                        placeholder="Select an action",
                        multi=False,
                        className='mb-2'
                    ),
                    dbc.Row([
                        dbc.Col([
                            html.Div('Profile name:', className='h-100 w-100')
                        ], width=6, className='h-100'),
                        dbc.Col([
                            dbc.Input(id='profile-name', placeholder='Enter name', type='text', value='', className='h-100 w-100')
                        ], width=6, className='h-100')
                    ], align='center', id='new-profile-input', style={"display": "flex", "flexWrap": "wrap", "marginLeft": "-0.75rem", "marginRight": "-0.75rem"})
                ]),
                dbc.ModalFooter([
                    dbc.Button("Load", id="load-profile", className="ms-auto", n_clicks=0),
                    dbc.Button("Save", id='save-profile', n_clicks=0),
                    dbc.Button("Cancel", id='cancel-profile', n_clicks=0),
                    dbc.Button("Delete", id='delete-profile', n_clicks=0, color='danger')
                ]),
            ],
            id="add-profile-dialog",
            is_open=False,
        ),
    ]
)

layout = dbc.Container([
    modal,
    profile_modal,
    html.Div(id='laser-container', children=[]),
    dbc.Row([dbc.Col(dbc.Button("Add Laser", id="start-add-laser-dialog", n_clicks=0), width='auto'),
             dbc.Col(dbc.Button("Load/Save Profile", id="start-profile-dialog", n_clicks=0),width='auto')]),
    dcc.Store(id='tab-data', data = {}, storage_type='memory'),
    dcc.Interval(id='home-page-load', interval=100, n_intervals=0, max_intervals=1)
], fluid=True)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_plot'
    ),
    Output({'type': 'data_plot', 'index': MATCH}, 'figure'),
    Output({'type': 'bar_plot', 'index': MATCH}, 'figure'),
    Output({'type': 'freq_info', 'index': MATCH}, 'children'),
    Output({'type': 'freq_digits', 'index': MATCH}, 'children'),
    Output({'type': 'laser-metadata', 'index': MATCH}, 'data', allow_duplicate=True),
    Output({'type': 'freq_digits', 'index': MATCH}, 'style'),
    Output({'type': 'log-msg', 'index': MATCH}, 'data', allow_duplicate=True),
    Input('wm_data', 'data'),
    State({'type': 'data_plot', 'index': MATCH}, 'figure'),
    State({'type': 'bar_plot', 'index': MATCH}, 'figure'),
    State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
    State({'type': 'freq_digits', 'index': MATCH}, 'style'),
    prevent_initial_call=True
)
# def update_plot(data):
#     if data is None or len(data[0]) == 0:
#         return no_update
#     new_data = data
#     freqs = np.array(data[0])
#     idxs = abs(freqs - 508848.922) < 0.1
#     if np.any(idxs):
#         new_freqs = freqs[idxs]
#         times = np.array(data[3])
#         new_times = times[idxs]
#         fig = Patch()
#         fig['data'][0]['x'].extend(new_times.tolist())
#         fig['data'][0]['y'].extend(new_freqs.tolist())
#     else:
#         return no_update
#     return fig

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='open_add_laser_dialog'
    ),
    Output("add-laser-dialog", "is_open", allow_duplicate=True),
    Output("laser-freq-options", "children"),
    Input("start-add-laser-dialog", "n_clicks"), 
    Input("cancel-laser", "n_clicks"),
    State('tab-data', 'data'),
    State('wm_data', 'data'),
    prevent_initial_call=True
)

@callback(
    Output("laser-container", "children", allow_duplicate=True),
    Output('add-laser-dialog', 'is_open', allow_duplicate=True),
    Output('tab-data', 'data', allow_duplicate=True),
    Input("add-laser", "n_clicks"),
    State('laser-name', 'value'),
    State('laser-center-freq', 'value'),
    State('laser-tol', 'value'),
    State('npts-input', 'value'),
    State('lock-tol', 'value'),
    State('laser-lock-btn', 'value'),
    State('tab-data', 'data'),
    prevent_initial_call=True
)
def add_new_laser(n_clicks, laser_name, laser_freq, laser_tol, npts_input, lock_tol, track_lock, tab_data):
    if n_clicks > 0:
        new_tab_data = Patch()
        if 'n_figs' in tab_data:
            pos = tab_data['n_figs']
        else:
            pos = 0
        if 'pos_to_id_map' in tab_data:
            new_tab_data['pos_to_id_map'].append(n_clicks)
        else:
            new_tab_data['pos_to_id_map'] = [n_clicks]
        if 'freqs' in tab_data:
            new_tab_data['freqs'].append(laser_freq)
        else:
            new_tab_data['freqs'] = [laser_freq]
        if 'names' in tab_data:
            new_tab_data['names'].append(laser_name)
        else:
            new_tab_data['names'] = [laser_name]
        if 'tols' in tab_data:
            new_tab_data['tols'].append(laser_tol)
        else:
            new_tab_data['tols'] = [laser_tol]
        if 'nptss' in tab_data:
            new_tab_data['nptss'].append(npts_input)
        else:
            new_tab_data['nptss'] = [npts_input]
        if 'lock_tols' in tab_data:
            new_tab_data['lock_tols'].append(lock_tol)
        else:
            new_tab_data['lock_tols'] = [lock_tol]
        if 'track_locks' in tab_data:
            new_tab_data['track_locks'].append(track_lock)
        else:
            new_tab_data['track_locks'] = [track_lock]
        new_tab_data['n_figs'] = pos + 1
        container = Patch()
        container.append(create_new_block(n_clicks, title=laser_name, name=laser_name, center_freq=laser_freq, freq_tol=laser_tol, lock_tol_MHz=lock_tol, n_pts=npts_input, track_lock=track_lock))
        return container, 0, new_tab_data
    return [], 0, {}

# TODO Move clientside
@callback(
    Output("laser-container", "children", allow_duplicate=True),
    Output('tab-data', 'data', allow_duplicate=True),
    Input({'type': 'delete-btn', 'index': ALL}, "n_clicks"),
    State('tab-data', 'data'),
    State("laser-container", "children"),
    prevent_initial_call=True
)
def delete_laser(n_clicks_list, tab_data, cur_figs):
    if not any(n_clicks_list):
        return no_update, no_update

    # clicked_index = n_clicks_list.index(max(filter(None, n_clicks_list)))
    triggered_id = ctx.triggered_id
    id = triggered_id['index']
    try:
        pos = tab_data['pos_to_id_map'].index(id)
    except ValueError:
        return no_update, no_update
    tab_data['n_figs'] = tab_data['n_figs'] - 1
    del cur_figs[pos]
    del tab_data['pos_to_id_map'][pos]
    del tab_data['freqs'][pos]
    del tab_data['names'][pos]
    del tab_data['tols'][pos]
    del tab_data['nptss'][pos]
    del tab_data['lock_tols'][pos]
    del tab_data['track_locks'][pos]
    return cur_figs, tab_data

# TODO move to clientside
@callback(
    Output({'type': 'edit-laser-dialog', 'index': MATCH}, 'is_open', allow_duplicate=True),
    Output({'type': 'edit-laser-title', 'index': MATCH}, 'children'),
    Output({'type': 'laser-name-edit', 'index': MATCH}, 'value'),
    Output({'type': 'laser-center-freq-edit', 'index': MATCH}, 'value'),
    Output({'type': 'laser-tol-edit', 'index': MATCH}, 'value'),
    Output({'type': 'npts-input-edit', 'index': MATCH}, 'value'),
    Output({'type': 'lock-tol-edit', 'index': MATCH}, 'value'),
    Output({'type': 'laser-lock-btn-edit', 'index': MATCH}, 'value'),
    Output({'type': 'laser-metadata', 'index': MATCH}, 'data', allow_duplicate=True),
    Input({'type': 'edit-btn', 'index': MATCH}, 'n_clicks'),
    Input({'type': 'cancel-laser-edit', 'index': MATCH}, 'n_clicks'),
    State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
    prevent_initial_call = True
)
def open_edit_laser(n_clicks, n_clicks_cancel, metadata):
    triggered_id = ctx.triggered_id
    if isinstance(triggered_id, dict):
        if triggered_id['type'] == 'edit-btn':
            if n_clicks > metadata['edit_clicks']:
                new_title = f"Edit {metadata['name']} Information"
                name = metadata['name']
                center_freq = metadata['f']
                freq_tol = metadata['df']
                npts = metadata['n_pts']
                lock_tol = metadata['lock_tol_MHz']
                lock_status = metadata['lock_status']
                patched = Patch()
                patched['edit_clicks'] = metadata['edit_clicks'] + 1
                return 1, new_title, name, center_freq, freq_tol, npts, lock_tol, lock_status, patched
            else:
                return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        elif (triggered_id['type'] == 'cancel-laser-edit'):
            return 0, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        else:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    else:
        return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
    
clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_laser_metadata'
    ),
    Output({'type': 'laser-metadata', 'index': MATCH}, 'data', allow_duplicate=True),
    Output({'type': 'edit-laser-dialog', 'index': MATCH}, 'is_open', allow_duplicate=True),
    Output({'type': 'laser_title', 'index': MATCH}, 'children'),
    Output({'type': 'lock-btn-text', 'index': MATCH}, 'children'),
    Output({'type': 'lock-btn', 'index': MATCH}, 'value'),
    Input({'type': "finish-laser-edit", 'index': MATCH}, 'n_clicks'),
    State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
    State({'type': 'laser-name-edit', 'index': MATCH}, 'value'),
    State({'type': 'laser-center-freq-edit', 'index': MATCH}, 'value'),
    State({'type': 'laser-tol-edit', 'index': MATCH}, 'value'),
    State({'type': 'lock-tol-edit', 'index': MATCH}, 'value'),
    State({'type': 'npts-input-edit', 'index': MATCH}, 'value'),
    State({'type': 'laser-lock-btn-edit', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_lock_status'
    ),
    Output({'type': 'laser-metadata', 'index': MATCH}, 'data', allow_duplicate=True),
    Input({'type': 'lock-btn', 'index': MATCH}, 'value'),
    State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_tab_data_from_lock'
    ),
    Output('tab-data', 'data', allow_duplicate=True),
    Input({'type': 'lock-btn', 'index': ALL}, 'value'),
    State('tab-data', 'data'),
    prevent_initial_call=True
)

clientside_callback(
    ClientsideFunction(
        namespace='clientside',
        function_name='update_tab_data_from_edit'
    ),
    Output('tab-data', 'data', allow_duplicate=True),
    Input({'type': "finish-laser-edit", 'index': ALL}, 'n_clicks'),
    State({'type': 'laser-name-edit', 'index': ALL}, 'value'),
    State({'type': 'laser-center-freq-edit', 'index': ALL}, 'value'),
    State({'type': 'laser-tol-edit', 'index': ALL}, 'value'),
    State({'type': 'lock-tol-edit', 'index': ALL}, 'value'),
    State({'type': 'npts-input-edit', 'index': ALL}, 'value'),
    State({'type': 'laser-lock-btn-edit', 'index': ALL}, 'value'),
    State('tab-data', 'data'),
    prevent_initial_call=True
)
# def update_tab_data_from_edit(btn, name, center_f, laser_tol, lock_tol, npts, tab_data):
#     print(ctx)
#     # triggered_id = ctx.triggered_id
#     # id = triggered_id['index']
#     # try:
#     #     pos = tab_data['pos_to_id_map'].index(id)
#     # except ValueError:
#     #     return no_update
#     # new_tab_data = Patch()
#     # new_tab_data['names'][pos] = name
#     # new_tab_data['freqs'][pos] = center_f
#     # new_tab_data['tols'][pos] = laser_tol
#     # new_tab_data['nptss'][pos] = npts
#     # new_tab_data['lock_tols'][pos] = lock_tol
#     return no_update

@callback(
    Output('add-profile-dialog', 'is_open', allow_duplicate=True),
    Output('profile-selector', 'options'),
    Output('profile-selector', 'value'),
    Input("start-profile-dialog", 'n_clicks'),
    Input('cancel-profile', 'n_clicks'),
    prevent_initial_call = True
)
def open_laser_calib_modal(open_btn, cancel_btn):
    triggered_id = ctx.triggered_id
    if (triggered_id == 'cancel-profile'):
        return 0, no_update, no_update
    elif (triggered_id == 'start-profile-dialog'):
        dir_path = Path(profile_dir)
        yml_files = list(dir_path.glob("*.yml"))
        yml_strings = [str(file.name) for file in yml_files]
        ret_options = ['Add new profile']
        ret_options.extend(yml_strings)
        return 1, ret_options, 'Add new profile'
    else:
        return no_update, no_update, no_update

# TODO Make clientside
@callback(
    Output('new-profile-input', 'style'),
    Input('profile-selector', 'value')
)
def show_and_hide_add_profile_name(selected_value):
    patched = Patch()
    if (selected_value == 'Add new profile'):
        patched['display'] = 'flex'
    else:
        patched['display'] = 'none'
    return patched

@callback(
    Output('add-profile-dialog', 'is_open', allow_duplicate=True),
    Input('save-profile', 'n_clicks'),
    State('profile-selector', 'value'),
    State('profile-name', 'value'),
    State('tab-data', 'data'),
    State('uuid', 'data'),
    prevent_initial_call=True
)
def save_profile(btn, prof, name, data, uuid):
    if prof == 'Add new profile':
        new_fname = profile_dir + name + '.yml'
        users_fname = name + '.yml'
    else:
        new_fname = profile_dir + prof
        users_fname = prof
    del data['pos_to_id_map']
    with open(new_fname, 'w') as f:
        yaml.dump(data, f)
    with open(users_file, 'r') as f:
        users_data = yaml.safe_load(f) or {}
    users_data[uuid] = users_fname
    with open(users_file, 'w') as f:
        yaml.dump(users_data, f)

@callback(
    Output('add-profile-dialog', 'is_open', allow_duplicate=True),
    Input('delete-profile', 'n_clicks'),
    State('profile-selector', 'value'),
    prevent_initial_call=True
)
def delete_profile(btn, name):
    full_name = profile_dir + name
    print(full_name)
    if os.path.exists(full_name):
        os.remove(full_name)
    return 0

# clientside_callback(
#     ClientsideFunction(
#         namespace='clientside',
#         function_name='browser_open_msg'
#     ),
#     Output({'type': 'log-msg', 'index': -1}, 'data', allow_duplicate=True),
#     Input('home-page-load', 'n_intervals'),
#     prevent_initial_call=True
# )

@callback(
    Output('add-profile-dialog', 'is_open', allow_duplicate=True),
    Output('tab-data', 'data'),
    Output("laser-container", "children", allow_duplicate=True),
    Output('msg_modal', 'is_open', allow_duplicate=True),
    Output('msg_title', 'children'),
    Output('msg_content', 'children'),
    Input('load-profile', 'n_clicks'),
    Input('home-page-load', 'n_intervals'),
    State('profile-selector', 'value'),
    State('uuid', 'data'),
    prevent_initial_call=True
)
def load_profile(btn, on_load, name, uuid):
    triggered_id = ctx.triggered_id
    if triggered_id == 'home-page-load':
        with open(users_file, 'r') as f:
            users_data = yaml.safe_load(f) or {}
        if uuid in (users_data):
            name = users_data[uuid]
    if name is None:
        return no_update, no_update, no_update, no_update, no_update, no_update
    tot_fname = profile_dir + name
    if os.path.exists(tot_fname):
        with open(tot_fname, 'r') as f:
            data = yaml.safe_load(f) or None
    else:
        data = None
    if data is None:
        return 0, no_update, no_update, 1, 'Error', 'File not found, or could not be loaded safely'
    try:
        params = []
        if 'track_locks' not in data:
            data['track_locks'] = [False] * data['n_figs']
        for i in range(data['n_figs']):
            # Make sure no problem here, before creating any blocks
            params.append([data['names'][i], data['freqs'][i], data['tols'][i], data['nptss'][i], data['lock_tols'][i], data['track_locks'][i]])
        id = -2 # negative ids for each of these blocks. -1 reserved since global log-msg has index -1
        new_children = []
        new_pos_to_id_map = []
        for i in range(data['n_figs']):
            new_children.append(create_new_block(id, title=params[i][0], name=params[i][0], center_freq=params[i][1], freq_tol=params[i][2], lock_tol_MHz=params[i][4], n_pts=params[i][3], track_lock=params[i][5]))
            new_pos_to_id_map.append(id)
            id = id - 1
        data['pos_to_id_map'] = new_pos_to_id_map
        with open(users_file, 'r') as f:
            users_data = yaml.safe_load(f) or {}
        users_data[uuid] = name
        with open(users_file, 'w') as f:
            yaml.dump(users_data, f)
        return 0, data, new_children, 0, no_update, no_update
    except Exception as e:
        return 0, no_update, no_update, 1, 'Error', 'Message: ' + str(e)