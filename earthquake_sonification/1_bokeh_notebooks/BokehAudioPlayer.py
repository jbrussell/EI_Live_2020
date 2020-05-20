# encoding: utf-8
# Original code from https://gist.github.com/nathanielatom/6442f94faca69dcf6efae146cb66c30c
#
# Modified by Josh Russell on 05/19/2020 for EI LIVE 2020:
# Now includes both a visual of the waveform as well as a spectrogram with linked x axes
#
import bokeh.models as bkm
import bokeh.core as bkc


class AudioPlayerModel(bkm.layouts.WidgetBox):
    """
    Audio player using https://howlerjs.com/.

    .. todo:: allow seek bar to drag when playing: where slider onclick => pause audio, offclick => play audio
    .. todo:: debug @audio.on('load', () => @model.seek_bar.end = @audio.duration()) not firing when audio 
              is already loaded (same file played in multiple instances on the same webpage) ... maybe once('play', ...)

    """

    __javascript__ = ["https://cdnjs.cloudflare.com/ajax/libs/howler/2.0.9/howler.core.min.js",
                      "https://cdnjs.cloudflare.com/ajax/libs/downloadjs/1.4.7/download.min.js"]

    __implementation__ = """
    import * as p from "core/properties"
    import {WidgetBox, WidgetBoxView} from "models/layouts/widget_box"

    export class AudioPlayerView extends WidgetBoxView

        initialize: (options) ->
            super(options)
            @audio = new Howl({src: [@model.audio_source]})
            @audio.on('play', () => @model.play_pause_button.label = "Pause")
            @audio.on('pause', () => @model.play_pause_button.label = "Play")
            @audio.on('stop', () => @model.play_pause_button.label = "Play"; @model.play_pause_button.active = false)
            @audio.on('load', () => @model.seek_bar.end = @audio.duration())
            @audio.on('end', () => @stop())
            @audio_mime_type = if @model.audio_source.includes(';base64,') then @model.audio_source.split(';base64,')[0].split(':')[1] else "text/plain"
            @audio_ext = if @audio_mime_type == "text/plain" then "_link.txt" else "." + @audio_mime_type.split("/")[1]
            @audio_ext = if @audio_ext == '.x-wav' then '.wav' else @audio_ext
            @connect(@model.play_pause_button.properties.active.change, @play_pause_press)
            @connect(@model.stop_button.properties.clicks.change, @stop)
            @connect(@model.download_button.properties.clicks.change, () => download(@model.audio_source, @model.default_title.value + @audio_ext, @audio_mime_type))
            @connect(@model.seek_bar.properties.value.change, () => @audio.seek(@model.seek_bar.value) if not @audio.playing())
            @connect(@model.volume_bar.properties.value.change, () => @audio.volume(@model.volume_bar.value))

        play: () =>
            if @audio.state() == "loaded"
                @audio.play()
                @step()
            else
                @model.play_pause_button.active = false

        pause: () =>
            @audio.pause()

        stop: () =>
            @audio.stop()
            @step()

        play_pause_press: () =>
            if @model.play_pause_button.active
                @play()
            else
                @pause()

        update_seek_bar: () =>
            @model.seek_bar.value = @audio.seek()

        step: () =>
            @update_seek_bar()
            if @audio.playing()
                requestAnimationFrame(@step)

    export class AudioPlayerModel extends WidgetBox
        default_view: AudioPlayerView
        type: "AudioPlayerModel"

        @define {
            audio_source:       [p.String, ]
            default_title:      [p.Any, ]
            play_pause_button:  [p.Any, ]
            stop_button:        [p.Any, ]
            download_button:    [p.Any, ]
            seek_bar:           [p.Any, ]
            volume_bar:         [p.Any, ]
        }

    """

    audio_source = bkc.properties.String(help="Audio file or base64 encoded file with header.")
    default_title = bkc.properties.Instance(bkm.widgets.TextInput, help="Audio player default_title, also used as download filename.")
    play_pause_button = bkc.properties.Instance(bkm.widgets.Toggle, help="Toggle used to control audio playback.")
    stop_button = bkc.properties.Instance(bkm.widgets.Button, help="Button used to halt audio playback.")
    download_button = bkc.properties.Instance(bkm.widgets.Button, help="Button used to download audio file.")
    seek_bar = bkc.properties.Instance(bkm.widgets.Slider, help="Seek bar to control playback.")
    volume_bar = bkc.properties.Instance(bkm.widgets.Slider, help="Volume bar to control playback gain.")

    def sonify_plotwf( data, fs,  # data to sonify
                       data_dis,  # data to plot
                       TargetDuration,  # duration of sonified waveform
                       default_title,  # will become output file name
                       title,
                       fs_resamp=44100,
                       x_axis_label='Sonified Time (seconds)',
                       y_axis_label='Displacement (mm)',
                       x_axis_label_true='True Time (hours)',
                       plot_width=800, plot_height=500,
                       seek_bar_color='red', 
                       seek_bar_width=3,
                       seek_bar_alpha=0.4,
                       seek_bar_throttle=15,  # milliseconds
                       time_series_start=0,  # offset in seconds
                       tools=['save','box_zoom','xwheel_zoom','ywheel_zoom','reset','crosshair','pan']
                       ):
        """
        Sonify data and plot waveforms.
        data vector should be numpy array
        
        """
        import numpy as np
        from scipy.io import wavfile
        import resampy
        import base64
        from io import BytesIO
        from bokeh.plotting import figure
        from bokeh.layouts import layout
        import BokehAudioPlayer

        # Seismogram duration
        duration = len(data)/fs
        # Frequency of desired trace
        fs_sound = int(fs*duration/TargetDuration)
        
        # Build time vector
        # time_steps_sound = np.linspace(0, data.size / fs_sound, data.size)
        time_steps = np.arange(0, TargetDuration, 1./fs_sound)  # time vector for sounds
        time_steps_true = np.arange(0, duration, 1./fs)  # time vector for true data
        
        # AudioPlayerModel can only accept wav files... we can get around this by writing the
        # waveform to a binary object in memory that looks like a wav file
        # Resample only for sake of sonification (plotting resampled waveform can be very laggy...)    
        datar = resampy.resample(data, fs_sound, fs_resamp)
        # Write data array to memory
        byte_io = BytesIO(bytes())
        # Convert to 16 bit PCM (again, AudioPlayerModel is finicky)
        data_16bitPCM = (datar/np.amax(np.absolute(datar))*32767).astype(np.int16)
        wavfile.write(byte_io, fs_resamp, data_16bitPCM)
        # Create base64-encoded data URI wav string (could also be a path to a wav file or a URL)
        audio_source = 'data:audio/wav;base64,'+base64.b64encode(byte_io.read()).decode('UTF-8')  # link or base64-encoded wavefile string
        # byte_io.read()

        # Bokeh Player setup - this is from a larger project, please forgive the weird syntax that's taken out of context
        player_options = {}
        player_options.setdefault("default_title", bkm.widgets.TextInput(value=default_title, title="", width=150, sizing_mode='scale_width'))
        player_options.setdefault("play_pause_button", bkm.widgets.Toggle(label="Play", width=100, button_type="success"))
        player_options.setdefault("stop_button", bkm.widgets.Button(label="Stop", width=100, button_type="success"))
        player_options.setdefault("download_button", bkm.widgets.Button(label="Save", width=100, button_type="success"))
        player_options.setdefault("seek_bar", bkm.widgets.Slider(start=0, end=time_steps[-1], step=TargetDuration/80, value=0, title="Time [s]", width=150, sizing_mode='scale_width'))
        player_options.setdefault("volume_bar", bkm.widgets.Slider(start=0, end=1, step=0.01, value=1, title="Volume", width=150, sizing_mode='scale_width'))
        # player_options.setdefault("sizing_mode", "scale_width")
        player_options.setdefault("sizing_mode", "fixed")
        all_widgets = [player_options["default_title"], player_options["volume_bar"], player_options["seek_bar"],
                       player_options["play_pause_button"], player_options["stop_button"], player_options["download_button"]]
        player_options.setdefault("children", all_widgets)
        player_options.setdefault('audio_source', audio_source)
        player = BokehAudioPlayer.AudioPlayerModel(**player_options)

        # Bokeh Plot setup
        source = bkm.ColumnDataSource(data={'time_steps':time_steps, 'data':data_dis})
        time_series_plot = figure(plot_width=plot_width, plot_height=plot_height, sizing_mode='scale_width',
                                  x_range=(time_steps.min(),time_steps.max()),
                                  title=title, x_axis_label=x_axis_label, y_axis_label=y_axis_label,
                                  tools=tools)
        # Add second x-axis showing true time in hours
        time_series_plot.line('time_steps', 'data', source=source)
        time_series_plot.extra_x_ranges = {"true_time": bkm.Range1d(
                                           start=time_steps_true[0]/3600,
                                           end=time_steps_true[-1]/3600)}
        time_series_plot.add_layout(bkm.LinearAxis(x_range_name="true_time",axis_label=x_axis_label_true),'below')
        # time_series_plot.xaxis[1].ticker.desired_num_ticks=24
        seek_bar_span = bkm.Span(dimension="height", line_color=seek_bar_color,
                                 line_width=seek_bar_width, line_alpha=seek_bar_alpha,
                                 tags=[time_series_start])

        # Setup interactive callback for seek bar
        cb_obj = None  # the following function is PyScript, NOT Python
        def set_span_loc(seek_bar_span=seek_bar_span, window=None):
            seek_bar_span.location = None if cb_obj.value == 0 else cb_obj.value + seek_bar_span.tags[0]
        player.seek_bar.js_on_change('value', bkm.CustomJS.from_py_func(set_span_loc))
        player.seek_bar.callback_throttle = seek_bar_throttle
        time_series_plot.add_layout(seek_bar_span)

        grid = layout([[time_series_plot, player]])
        grid.sizing_mode = 'scale_width'
        
        return grid
        
        
    # =================================
    
    def sonify_plotwfspec( data, fs,  # data to sonify
                       data_dis,  # data to plot
                       TargetDuration,  # duration of sonified waveform
                       default_title,  # will become output file name
                       title,
                       fs_resamp=44100,
                       x_axis_label='Sonified Time (seconds)',
                       x_axis_label_true='True Time (hours)',
                       ywav_axis_label='Sonified Amplitude',
                       ywav_axis_label_true='Ground Displacement (mm)',
                       yspec_axis_label='Sonified Frequency (Hz)',
                       yspec_axis_label_true='True Frequency (Hz)',
                       # plot_width=800, plot_height=250,
                       aspect_ratio=2,
                       seek_bar_color='red', 
                       seek_bar_width=3,
                       seek_bar_alpha=1,
                       seek_bar_throttle=15,  # milliseconds
                       time_series_start=0,  # offset in seconds
                       # tools=['save','box_zoom','xwheel_zoom','ywheel_zoom','reset','crosshair','pan'],
                       palette='RdYlBu11',
                       is_xtrue = True,
                       is_ytrue = True,
                       time_true_factor = 3600,  # Default to hours
                       high_res_spec = False,
                       ):
        """
        Sonify data and plot waveform as well as spectrogram.
        data vector should be numpy array
        
        """
        import numpy as np
        from scipy.io import wavfile
        import resampy
        import base64
        from io import BytesIO
        from bokeh.plotting import figure
        from bokeh.layouts import layout
        import BokehAudioPlayer
        from scipy import signal
        from scipy.interpolate import interp2d
        
        # Ensure data is normalized
        data = data / np.amax(np.abs(data))

        # Seismogram duration
        duration = len(data)/fs
        # Frequency of desired trace
        fs_sound = int(fs*duration/TargetDuration)
        
        # Build time vector
        # time_steps_sound = np.linspace(0, data.size / fs_sound, data.size)
        time_steps = np.arange(0, TargetDuration, 1./fs_sound)  # time vector for sounds
        time_steps_true = np.arange(0, duration, 1./fs)  # time vector for true data
        
        # AudioPlayerModel can only accept wav files... we can get around this by writing the
        # waveform to a binary object in memory that looks like a wav file
        # Resample only for sake of sonification (plotting resampled waveform can be very laggy...)    
        datar = resampy.resample(data, fs_sound, fs_resamp)
        # Write data array to memory
        byte_io = BytesIO(bytes())
        # Convert to 16 bit PCM (again, AudioPlayerModel is finicky)
        data_16bitPCM = (datar/np.amax(np.absolute(datar))*32767).astype(np.int16)
        wavfile.write(byte_io, fs_resamp, data_16bitPCM)
        # Create base64-encoded data URI wav string (could also be a path to a wav file or a URL)
        audio_source = 'data:audio/wav;base64,'+base64.b64encode(byte_io.read()).decode('UTF-8')  # link or base64-encoded wavefile string
        # byte_io.read()

        # Bokeh Player setup - this is from a larger project, please forgive the weird syntax that's taken out of context
        player_options = {}
        player_options.setdefault("default_title", bkm.widgets.TextInput(value=default_title, title="", width=100, sizing_mode='scale_width'))
        player_options.setdefault("play_pause_button", bkm.widgets.Toggle(label="Play", width=50, button_type="success"))
        player_options.setdefault("stop_button", bkm.widgets.Button(label="Stop", width=50, button_type="success"))
        player_options.setdefault("download_button", bkm.widgets.Button(label="Save", width=50, button_type="success"))
        player_options.setdefault("seek_bar", bkm.widgets.Slider(start=0, end=time_steps[-1], step=TargetDuration/80, value=0, title="Time [s]", width=100, sizing_mode='scale_width'))
        player_options.setdefault("volume_bar", bkm.widgets.Slider(start=0, end=1, step=0.01, value=1, title="Volume", width=100, sizing_mode='scale_width'))
        # player_options.setdefault("sizing_mode", "scale_width")
        player_options.setdefault("sizing_mode", "fixed")
        all_widgets = [player_options["default_title"], player_options["volume_bar"], player_options["seek_bar"],
                       player_options["play_pause_button"], player_options["stop_button"], player_options["download_button"]]
        player_options.setdefault("children", all_widgets)
        player_options.setdefault('audio_source', audio_source)
        player = BokehAudioPlayer.AudioPlayerModel(**player_options)

        # Bokeh Plot setup
        source = bkm.ColumnDataSource(data=dict(time_steps=time_steps, data=data))
        
        # Setup time series
        time_series_plot = figure(
                                  aspect_ratio=aspect_ratio, sizing_mode='scale_width',
                                  # plot_width=plot_width, plot_height=plot_height, sizing_mode='scale_width',
                                  x_range=(time_steps.min(),time_steps.max()),
                                  y_range=(-np.amax(np.abs(data))*1.05,np.amax(np.abs(data))*1.05),
                                  title=title, y_axis_label=ywav_axis_label,
                                  # tools=tools, toolbar_location='right',
                                  toolbar_location=None,
                                  )
        # Plot time series object
        time_series_plot.line('time_steps', 'data', source=source)
        # Add y axis showing true displacement
        if is_ytrue:
            time_series_plot.extra_y_ranges = {"data_dis": bkm.Range1d(
                                   start=-np.amax(np.abs(data_dis))*1.05,
                                   end=np.amax(np.abs(data_dis))*1.05)}
            time_series_plot.add_layout(bkm.LinearAxis(y_range_name="data_dis",axis_label=ywav_axis_label_true),'left')
        
        # Spectrogram
        if high_res_spec == True:
            nperseg = int(0.01*fs_sound*TargetDuration) # The length of each frame (should be expressed in samples)
            noverlap = int(nperseg*0.7) # The overlapping between successive frames (should be expressed in samples)
            nfft = int(nperseg*2)
            f, t, Sxx = signal.spectrogram(data_dis, fs_sound, nperseg=nperseg, noverlap=noverlap, nfft=nfft)
        else:
            f, t, Sxx = signal.spectrogram(data_dis, fs_sound)            
        # T = np.linspace(1/f[-1],1/f[1],len(f))
        # ip = interp2d(t, f, Sxx); zi = ip(t, T)
        # Sxx = zi
        # f = T
        amp_db = 10*np.log10(np.abs(Sxx))
        TOOLS = "hover,save,pan,box_zoom,reset,xwheel_zoom,ywheel_zoom,crosshair"
        spec_plot = figure(
                       aspect_ratio=aspect_ratio, sizing_mode='scale_width',
                       # plot_width=plot_width, plot_height=plot_height, sizing_mode='scale_width',
                       x_axis_label=x_axis_label, y_axis_label=yspec_axis_label,
                       # tools=TOOLS, toolbar_location='right',
                       toolbar_location=None,
                       tooltips=[('Power', '@image log(dB/Hz)')])
        spec_plot.image(image=[amp_db], x=t.min(), y=f.min(), 
                   dw=t.max(), dh=f.max(), palette=palette)
        # spec_plot.x_range.range_padding = spec_plot.y_range.range_padding = 0
        spec_plot.y_range.range_padding = 0
        spec_plot.x_range = time_series_plot.x_range
        # Add colorbar
        mapper_opts = dict(palette=palette, low=amp_db.min(), high=amp_db.max())
        color_mapper = bkm.LinearColorMapper(**mapper_opts)
        color_bar = bkm.ColorBar(color_mapper=color_mapper, 
                             ticker=spec_plot.xaxis.ticker, formatter=spec_plot.xaxis.formatter,
                             location=(0,0), orientation='vertical', padding=5, width=20)
                     # ticker=LogTicker(),
                     # label_standoff=12, border_line_color=None, location=(0,0))
        spec_plot.add_layout(color_bar, 'right')     
        if is_xtrue:
            # Add second x range from true time
            spec_plot.extra_x_ranges = {"true_time": bkm.Range1d(
                                   start=time_steps_true[0]/time_true_factor,
                                   end=time_steps_true[-1]/time_true_factor)}
            spec_plot.add_layout(bkm.LinearAxis(x_range_name="true_time",axis_label=x_axis_label_true),'below')
        # add second y range for true frequency
        if is_ytrue:
            f_tru, t_tru, Sxx_tru = signal.spectrogram(data_dis, fs)
            spec_plot.extra_y_ranges = {"true_freq": bkm.Range1d(
                                   start=f_tru[0],
                                   end=f_tru[-1])}
            spec_plot.add_layout(bkm.LinearAxis(y_range_name="true_freq",axis_label=yspec_axis_label_true),'left')
        
        # Setup seek bar
        seek_bar_span = bkm.Span(dimension="height", line_color=seek_bar_color,
                                 line_width=seek_bar_width, line_alpha=seek_bar_alpha,
                                 tags=[time_series_start])

        # Setup interactive callback for seek bar
        cb_obj = None  # the following function is PyScript, NOT Python
        def set_span_loc(seek_bar_span=seek_bar_span, window=None):
            seek_bar_span.location = None if cb_obj.value == 0 else cb_obj.value + seek_bar_span.tags[0]
        player.seek_bar.js_on_change('value', bkm.CustomJS.from_py_func(set_span_loc))
        player.seek_bar.callback_throttle = seek_bar_throttle
        time_series_plot.add_layout(seek_bar_span)
        spec_plot.add_layout(seek_bar_span)

        # Setup shared toolbar
        xwheel_zoom = bkm.tools.WheelZoomTool(dimensions='width')
        ywheel_zoom = bkm.tools.WheelZoomTool(dimensions='height')
        pan_tool = bkm.tools.PanTool()
        hover = bkm.tools.HoverTool()
        crosshair = bkm.tools.CrosshairTool()
        reset = bkm.tools.ResetTool()
        save = bkm.tools.SaveTool()
        tools = (xwheel_zoom, ywheel_zoom, pan_tool, hover, crosshair, reset, save)
        toolbar = bkm.Toolbar(
            tools=list(tools),
            active_inspect=[crosshair],
            # active_drag =                         # here you can assign the defaults
            # active_scroll =                       # wheel_zoom sometimes is not working if it is set here
            # active_tap 
        )
        toolbar_box = bkm.ToolbarBox(
            toolbar=toolbar,
            toolbar_location='above'
        )
        time_series_plot.add_tools(*tools)
        spec_plot.add_tools(*tools)    
            
        grid = layout(
                      # [[time_series_plot, player], spec_plot],
                      [[[toolbar_box, time_series_plot, spec_plot], player]],
                      sizing_mode='scale_width')
        
        return grid