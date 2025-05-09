function getStandardDeviation (array) {
    const n = array.length
    const mean = array.reduce((acc, cur) => acc + cur, 0) / n
    return Math.sqrt(array.map(x => Math.pow(x - mean, 2)).reduce((acc, cur) => acc + cur, 0) / n)
}

function calcFreqOptions(freq_vals, curr_freq_vals, tolerance) {
    let options = [];
    let filterFunc;
    let this_freq;
    for (let i = freq_vals.length - 1; i >= 0; i--) {
        this_freq = freq_vals[i];
        filterFunc = function(item, index, array) {
            return Math.abs(item - this_freq) < tolerance ? true : false;
        };
        if (!curr_freq_vals.find(filterFunc) && !options.find(filterFunc)) {
            options.push(this_freq);
        }
    }
    return options;
}

window.dash_clientside = Object.assign({}, window.dash_clientside, {
    clientside: {
        /*
        Output({'type': 'data_plot', 'index': MATCH}, 'figure'),
        Output({'type': 'freq_info', 'index': MATCH}, 'children'),
        Output({'type': 'freq_digits', 'index': MATCH}, 'children'),
        Output({'type': 'laser-metadata', 'index': MATCH}, 'data'),
        Output({'type': 'freq_digits', 'index': MATCH}, 'style'),
        Input('wm_data', 'data'),
        Input({'type': 'data_plot', 'index': MATCH}, 'figure'),
        State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
        State({'type': 'freq_digits', 'index': MATCH}, 'style')
        */
        update_plot: function(newData, currentFig, info, prev_style) {
            if (!currentFig || !newData || !info) {
                return [window.dash_clientside.no_update, window.dash_clientside.no_update,  window.dash_clientside.no_update];
            }
            // Values we need
            const center_freq = info['f'];
            const freq_tol = info['df'];
            const n_pts = info['n_pts'];
            // Copy the current figure to avoid mutation
            let updatedFig = {...currentFig};
            updatedFig.data = [...updatedFig.data];

            if (!updatedFig.data[0]) {
                updatedFig.data[0] = {x: [], y: [], type: 'scatter', mode: 'lines'};
            }
            // Data to use
            const new_freqs = [];
            const new_times = [];
            const cur_times = [...updatedFig.data[0].x];
            let amp = info['cur_amp'];
            for (let i = 0; i < newData[0].length; i++){
                let this_freq = newData[0][i];
                let this_time = newData[3][i];
                if (Math.abs(this_freq - center_freq) < freq_tol && !(cur_times.includes(this_time))) {
                    new_freqs.push(this_freq - center_freq);
                    new_times.push(this_time);
                    amp = newData[1][i];
                }
            }
            const tot_times = updatedFig.data[0].x.concat(new_times);
            const tot_freqs = updatedFig.data[0].y.concat(new_freqs);
            if (tot_times.length > n_pts) {
                tot_times.splice(0, tot_times.length - n_pts);
                tot_freqs.splice(0, tot_freqs.length - n_pts);
            }

            updatedFig.data[0].x = tot_times;
            updatedFig.data[0].y = tot_freqs;

            // Split text output
            const split_num = (tot_freqs[tot_freqs.length - 1] + center_freq).toFixed(3).split(".");
            const std_freq = (getStandardDeviation(tot_freqs) * 1e3).toFixed(1); // MHz
            const wavelength = (299792458 / (tot_freqs[tot_freqs.length - 1] + center_freq)).toFixed(1);
            const amp_print = (amp * 100).toFixed(1)
            let this_color = 'white';
            if (amp < 0.1) {
                this_color = 'yellow';
            }

            const lock_status = info['lock_status'];
            const lock_tol_MHz = info['lock_tol_MHz'];
            let output_style;
            if (lock_status && (Math.abs(tot_freqs[tot_freqs.length - 1]) > lock_tol_MHz/1e3)) {
                output_style = Object.assign({}, prev_style);
                output_style.backgroundColor = '#f8d7da';
            }
            else {
                output_style = Object.assign({}, prev_style);
                delete output_style.backgroundColor;
            }
            // const span1 = document.createElement('span');
            // span1.textContent = 'hi';
            // span1.style.fontSize = '18px';
            
            // const span2 = document.createElement('span');
            // span2.textContent = 'world';
            // span2.style.fontSize = '22px';
            const info_span1 = { 'props': {'children': wavelength + ' nm, ', 'className' : 'freq-info-text-1'},'type': 'Span', 'namespace': 'dash_html_components'};
            const info_span2 = { 'props': {'children': '\u00B1' + std_freq + ' MHz', 'className' : 'freq-info-text-2'},'type': 'Span', 'namespace': 'dash_html_components'};
            const info_span3 = { 'props': {'children': ', ' + amp_print + '%', 'className': 'freq-info-text-2', 'style' : {'backgroundColor': this_color}},'type': 'Span', 'namespace': 'dash_html_components'};

            const span1 = { 'props': {'children': split_num[0] + '.', 'className' : 'freq-text-1'},'type': 'Span', 'namespace': 'dash_html_components'};
            const span2 = { 'props': {'children': split_num[1], 'className': 'freq-text-2'},'type': 'Span', 'namespace': 'dash_html_components'};
            const span3 = { 'props': {'children': ' GHz', 'className': 'freq-text-3'},'type': 'Span', 'namespace': 'dash_html_components'};
            let return_info = window.dash_clientside.no_update;
            if (amp != info['cur_amp']) {
                info['cur_amp'] = amp;
                return_info = info;
            }
            return [updatedFig, [info_span1, info_span2, info_span3], [span1, span2, span3], return_info, output_style];
        },
        /*
        Output("add-laser-dialog", "is_open", allow_duplicate=True),
        Output("laser-freq-options", "children"),
        Input("start-add-laser-dialog", "n_clicks"), 
        Input("cancel-laser", "n_clicks"),
        State('tab-data', 'data'),
        State('wm_data', 'data'),
        */
        open_add_laser_dialog: function(n_clicks_start, n_clicks_cancel, tab_data, wm_data) {
            const triggered_id = window.dash_clientside.callback_context.triggered_id;
            let dialog_state = 0;
            let new_text = window.dash_clientside.no_update;
            if (triggered_id == 'cancel-laser') {
                dialog_state = 0;
            }
            else if (triggered_id == 'start-add-laser-dialog') {
                dialog_state = 1;
                let wm_data_freqs = wm_data[0];
                let cur_freqs = tab_data['freqs'];
                if (!cur_freqs) {
                    cur_freqs = [];
                }
                let options = calcFreqOptions(wm_data_freqs, cur_freqs, 1);
                // let filterFunc;
                // let this_freq;
                // for (let i = 0; i < wm_data_freqs.length; i++) {
                //     this_freq = wm_data_freqs[i];
                //     filterFunc = function(item, index, array) {
                //         return Math.abs(item - this_freq) < 1 ? true : false;
                //     };
                //     if (!cur_freqs.find(filterFunc) && !options.find(filterFunc)) {
                //         options.push(this_freq);
                //     }
                // }
                options.sort();
                options = options.map((item, index, array) => {return index == 0 ? item.toFixed(3) : (' ' + item.toFixed(3));});
                new_text = 'Suggestions: ' + String(options);
            }
            else {
                dialog_state = 0;
            }
            return [dialog_state, new_text];
        },
        /*
        Output('all-current-freqs', 'children'),
        Input('update_all_freqs_display', 'n_intervals'),
        State('wm_data', 'data'),
        State('wm_err_data', 'data')
        */
        update_all_freqs_display: function(n_intervals, wm_data) {
            let freqs = wm_data[0];
            let options = calcFreqOptions(freqs, [], 0.25);
            options.sort();
            options = options.map((item, index, array) => {return index == 0 ? item.toFixed(3) : (' ' + item.toFixed(3));})
            let timestamp = wm_data[3].slice(-1)[0];
            const date = new Date(timestamp * 1000);
            return 'Current Readings (' + date.toLocaleString() + '): ' + String(options);
        },
        /*
        Output('wm-error-text', 'children'),
        Input('wm_err_data', 'data')
        */
        update_wm_error_display: function(wm_err) {
            let wm_err_str = 'Wavemeter Error: '
            if (!wm_err) {
                wm_err_str = wm_err_str + 'N/A';
            }
            else {
                wm_err_str = wm_err_str + (wm_err * 1e3).toFixed(0) + ' MHz';
            }
            return wm_err_str;
        },
        /*
        Output({'type': 'laser-metadata', 'index': MATCH}, 'data'),
        Output({'type': 'edit-laser-dialog', 'index': MATCH}, 'is_open', allow_duplicate=True),
        Output({'type': 'laser_title', 'index': MATCH}, 'children'),
        Output({'type': 'lock-btn', 'index': MATCH}, 'label'),
        Input({'type': "finish-laser-edit", 'index': MATCH}, 'n_clicks'),
        State({'type': 'laser-metadata', 'index': MATCH}, 'data'),
        State({'type': 'laser-name-edit', 'index': MATCH}, 'value'),
        State({'type': 'laser-center-freq-edit', 'index': MATCH}, 'value'),
        State({'type': 'laser-tol-edit', 'index': MATCH}, 'value'),
        State({'type': 'lock-tol-edit', 'index': MATCH}, 'value'),
        State({'type': 'npts-input-edit', 'index': MATCH}, 'value'),
        prevent_initial_call=True
        */
        update_laser_metadata: function(n_clicks, metadata, laser_name, laser_center_f, laser_tol, lock_tol, npts) {
            if (n_clicks > 0) {
                metadata['name'] = laser_name;
                metadata['f'] = laser_center_f;
                metadata['df'] = laser_tol;
                metadata['n_pts'] = npts;
                metadata['lock_tol_MHz'] = lock_tol;
                new_label = 'Unlock Alert (' + '\u00B1' + lock_tol.toString() + ' MHz)'
                return [metadata, 0, laser_name, new_label];
            }
            else {
                return [window.dash_clientside.no_update,  window.dash_clientside.no_update,  window.dash_clientside.no_update, window.dash_clientside.no_update];
            }
        },
        /*
        Output({'type': 'laser-metadata', 'index': MATCH}, 'data', allow_duplicate=True),
        Input({'type': 'lock-btn', 'index': MATCH}, 'value'),
        State({'type': 'laser-metadata', 'index': MATCH}, 'data')
        */
        update_lock_status: function (lock_btn, metadata) {
            if (lock_btn != metadata['lock_status']) {
                metadata['lock_status'] = lock_btn
                return metadata
            }
            return window.dash_clientside.no_update
        },
        /*
        Output('calib-name', 'value'),
        Output('calib-freq', 'value'),
        Output('calib-tol', 'value'),
        Input('calibration-selector', 'value'),
        State('calib-cache', 'data')
        */
        update_calib_options: function(selected_value, data) {
            let name = window.dash_clientside.no_update;
            let freq = window.dash_clientside.no_update;
            let tol = window.dash_clientside.no_update;
            if (selected_value in data) {
                const entry = data[selected_value];
                if ('freq_GHz' in entry && 'tol_GHz' in entry) {
                    name = selected_value;
                    freq = entry['freq_GHz'];
                    tol = entry['tol_GHz'];
                }
            }
            return [name, freq, tol];
        },
        /*
        Output('msg_modal', 'is_open'),
        Input('close-msg', 'n_clicks')
        */
        close_msg: function(btn) {
            return 0
        }
    }
});