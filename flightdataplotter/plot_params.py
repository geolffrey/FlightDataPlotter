#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
This application plots LFL parameters and is intended to provide quick feedback
to people altering LFL definitions.
'''

from __future__ import print_function

import argparse
import configobj
import itertools
import logging
import matplotlib

import os
import sys
import tempfile
import threading
import time
import traceback
import wx

import numpy as np

from datetime import datetime
from past.builtins import basestring
from argparse import RawTextHelpFormatter

from analysis_engine.library import align

import compass
from compass.compass_cli import configobj_error_message
from compass.arinc717.data_frame_parser import parse_lfl
from compass.arinc717.hdf import create_hdf

from hdfaccess.file import hdf_file

matplotlib.use('WXAgg')

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from pylab import setp


CSV_FUNCTIONS = {
    'hfdm': compass.process_hfdm_csv_data,
    'latitude': compass.process_latitude_data,
    'chinook': compass.process_chinook_data,
    'dash8': compass.process_dash8_data,
    'g1000': compass.process_garmin1000_data,
}


app = wx.App()


# Argument parsing.
###############################################################################

def create_parser():
    parser = argparse.ArgumentParser(
        description='Plot parameters when an LFL file changes.', formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        '-l', '--lfl', dest='lfl_path', nargs='?',
        help='Path of LFL file. If not provided, GUI File Browser will appear.')
    parser.add_argument('-r', '--raw-data', dest='data_path', nargs='?', help='Path of raw data file.')
    #parser.add_argument('--read-percent') # TODO!! 0 to 100
    parser.add_argument(
        '-o', '--output-path', dest='output_path',
        action='store',
        help='Output file path (default will be a temporary location).')
    parser.add_argument(
        '-c', dest='cli', action='store_true',
        help='Use command line arguments rather than file dialogs.')
    help_message_superframes = "Number of superframes stored in memory before writing \n" \
        "to HDF5 file. A value of 0 will cause all superframes to be \n" \
        "stored in memory. Default is 100 superframes."
    parser.add_argument(
        '--superframes-in-memory',
        dest='superframes_in_memory', action='store', type=int, default=-1,
        help=help_message_superframes)
    parser.add_argument(
        '-d', '--frame-doubled',
        dest='frame_doubled', default=False, action='store_true',
        help="The input raw data is frame doubled.")
    parser.add_argument(
        '--plot-changed', dest='plot_changed', default=False,
        action='store_true',
        help="Plot parameters which have changed since the last processing.")
    parser.add_argument(
        '--start', dest='percent_start', type=int, default=0,
        help='Percentage into the file to start inspecting.')
    parser.add_argument(
        '--stop', dest='percent_stop', type=int, default=100,
        help='Percentage into the file to inspect up until.')
    parser.add_argument(
        '--tail', dest='tail_number',
        help='Aircraft tail number.')
    parser.add_argument(
        '--aircraft-model', dest='aircraft_model',
        help='Aircraft model.')
    parser.add_argument(
        '--aircraft-family', dest='aircraft_family',
        help='Aircraft family.')
    parser.add_argument(
        '--aircraft-series', dest='aircraft_series',
        help='Aircraft series.')
    parser.add_argument(
        '--engine-series', dest='engine_series',
        help='Engine series.')
    parser.add_argument(
        '--engine-manufacturer', dest='engine_manufacturer',
        help='Engine manufacturer.')
    parser.add_argument(
        '--engine-type', dest='engine_type',
        help='Engine type.')
    parser.add_argument(
        '-s', '--stretched', dest='stretched',
        help="Name of frame Stretched definition to apply.")
    parser.add_argument(
        '-m', '--show-masked', dest='mask_flag', action='store_true',
        help="Show masked data.")
    parser.add_argument(
        '--csv', dest='csv_type',
        help="Process CSV file, options are: \n" \
             "hfdm, g1000, dash8, latitude, chinook \n" \
             "Example: --csv hfdm; --csv g1000; --csv dash8")
    parser.add_argument(
        '--hdf', dest='hdf_flag', action='store_true',
        help="Process HDF5 file")
    help_message_axis = "Specify a list of parameters to display on axis 1. \n" \
                        "To display more, use --axis2 and so on (limited to 6). \n" \
                        "Only available for csv and hdf5 formats. \n" \
                        "If displaying multiple parameters put them in quotes and separate by spaces,. \n"\
                        "For example: --axis2 \"Airspeed\" \"Altitude AGL\""
    parser.add_argument(
        '--axis2', dest='axis2', nargs="*",
        help=help_message_axis)
    parser.add_argument(
        '--axis3', dest='axis3', nargs="*",)
    parser.add_argument(
        '--axis4', dest='axis4', nargs="*",)
    parser.add_argument(
        '--axis5', dest='axis5', nargs="*",)
    parser.add_argument(
        '--axis6', dest='axis6', nargs="*",)

    return parser


def copy_file_part(src_path, percent_start=0, percent_stop=100):
    '''
    Copies percentage of the source path to a new destination file. If source
    is compressed, output is read out into a decompressed file.

    src_path can be either a zip (.SAC), bz2 or uncompressed data file

    NOTE: Reads data into memory
    TODO: Move to flightdatautilities.filesystem_tools ?
    '''

    from flightdatautilities.filesystem_tools import open_raw_data
    ext = '_%d-%d.dat' % (percent_start, percent_stop)
    dest_path = os.path.splitext(src_path)[0] + ext
    if os.path.isfile(dest_path) and os.path.getsize(dest_path):
        print('Partial file already exists; using: %s' % dest_path)
        return dest_path
    try:
        src = open_raw_data(src_path)
        src.seek(0, 2)
        size = src.tell()
        src.seek(0)
        offset = int(percent_start * size / 100.0)
        if offset % 2:
            offset += 1  # make sure the start is even
        read_end = int(percent_stop * size / 100.0)
        amount = read_end - offset
        if amount % 2:
            amount -= 1  # make multiple of np.short (2 bytes)
        src.seek(offset)
        data = src.read(amount)
    finally:
        src.close()
    with open(dest_path, 'wb') as dest:
        dest.write(data)
    return dest_path


def validate_args(parser):
    '''
    Validate arguments provided to argparse.
    '''
    args = parser.parse_args()
    if not (args.csv_type or args.hdf_flag) and not args.lfl_path:
        args.lfl_path = lfl_file_dialog()
    if not (args.csv_type or args.hdf_flag) and not os.path.isfile(args.lfl_path):
        parser.error('LFL file path not valid: %s' % args.lfl_path)

    if not args.data_path:
        args.data_path = data_file_dialog()
    if not os.path.isfile(args.data_path):
        parser.error('Data file path not valid: %s' % args.data_path)

    if args.percent_start > 0 or args.percent_stop < 100:
        args.data_path = copy_file_part(
            args.data_path, args.percent_start, args.percent_stop)
        print("Read data chunk into new file: %s" % args.data_path)

    if not args.output_path:
        args.output_path = os.path.join(
            tempfile.gettempdir(),
            os.path.splitext(os.path.basename(args.data_path))[0] + '.hdf5')

    if args.superframes_in_memory == 0 or args.superframes_in_memory < -1:
        parser.error('Superframes in memory argument must be -1 or positive. '
                     'Found %s' % args.superframes_in_memory)

    aircraft_info = {
        'Frame Doubled': args.frame_doubled,
        'Stretched': args.stretched,
    }
    if args.tail_number:
        aircraft_info['Tail Number'] = args.tail_number
    if args.aircraft_family:
        aircraft_info['Aircraft Family'] = args.aircraft_family
    if args.aircraft_series:
        aircraft_info['Aircraft Series'] = args.aircraft_series
    if args.aircraft_model:
        aircraft_info['Aircraft Model'] = args.aircraft_model
    if args.engine_manufacturer:
        aircraft_info['Engine Manufacturer'] = args.engine_manufacturer
    if args.engine_series:
        aircraft_info['Engine Series'] = args.engine_series
    if args.engine_type:
        aircraft_info['Engine Type'] = args.engine_type

    return (
        args.lfl_path,
        args.data_path,
        args.output_path,
        args.superframes_in_memory,
        args.plot_changed,
        args.mask_flag,
        args.csv_type,
        args.hdf_flag,
        args.axis2,
        args.axis3,
        args.axis4,
        args.axis5,
        args.axis6,
        aircraft_info,
    )


# Processing and plotting functions
###############################################################################


def plot_parameters(params, axes, mask_flag, title=''):
    '''
    Plot resulting parameters.
    '''
    print('Plotting parameters.')
    max_freq = 0
    min_freq = float('inf')

    for name, param in params.items():
        max_freq = max(max_freq, param.frequency)
        min_freq = min(min_freq, param.frequency)

    for param_name, param in params.items():
        if max_freq == param.frequency:
            param_max_freq = param
        if param.frequency == min_freq:
            param_min_freq_len = len(param.array)

    # Truncate parameter arrays to successfully align them since the file
    # has not been through split sections.
    for param_name, param in params.items():
        array_len = param_min_freq_len * (param.frequency / min_freq)
        if array_len != len(param.array):
            print('Truncated %s from %d to %d for display purposes' % (
                param_name, len(param.array), array_len))
            param.array = param.array[:array_len]

    #==========================================================================
    # Plot Preparation
    #==========================================================================

    # Invariant parameters are identified here. They could be inserted into
    # the plot configuration file, but this is more straightforward.
    plt.rc('axes', grid=True)
    plt.rc('grid', color='0.75', linestyle='-', linewidth=0.5)

    # These items are altered during the plot, so not suited to plt.rc setup
    prop = fm.FontProperties(size=10)
    legendprops = dict(shadow=True, fancybox=True, markerscale=0.5, prop=prop)

    # Start by making a big clean canvas
    fig = plt.figure(facecolor='white', figsize=(8, 6))
    fig.canvas.set_window_title("%s %s" % (
        title, datetime.now().strftime('%A, %d %B %Y at %X')))

    # Add the "reference" altitude plot, and title this
    # (If we title the empty plot, it acquires default 0-1 scales)
    param_name = axes[1][0]
    param = params[param_name]
    array = align(param, param_max_freq)
    first_axis = fig.add_subplot(len(axes), 1, 1)
    if mask_flag:
        first_axis.plot(array.data, label=param_name)
    else:
        first_axis.plot(array, label=param_name)

    ####plt.title("Processed on %s" %
    ####          datetime.now().strftime('%A, %d %B %Y at %X'))
    setp(first_axis.get_xticklabels(), visible=False)

    # Now plot the additional data from the AXIS_N lists at the top of the lfl
    for index, param_names in axes.items():
        if index == 1:
            continue
        axis = fig.add_subplot(len(axes), 1, index, sharex=first_axis)
        # Avoid iterating over string
        if isinstance(param_names, basestring):
            param_names = [param_names]
        for param_name in param_names:
            param = params[param_name]
            # Data is aligned in time but the samples are not interpolated so
            # that scaling issues can be easily addressed
            label_text = param.name
            args = []
            if np.ma.all(param.array.mask):
                args.append([])
                label_text += ' <ALL MASKED>'
            elif param.data_type == 'ASCII' or param.array.dtype.char == 'S':
                print("Warning: ASCII not supported. Param '%s'" % param)
                args.append([])
                label_text += ' <ASCII NOT DRAWN>'
            elif param.hz != max_freq:
                # Data is aligned in time but the samples are not
                # interpolated so that scaling issues can be easily addressed
                args.append(np.arange(len(param.array)) * (max_freq / param.hz))
                args.append(param.array)
            else:
                args.append(param.array)

            if param.units is None:
                label_text += " [No units]"
            else:
                label_text += " : " + param.units.decode()
            values_mapping = getattr(param.array, 'values_mapping', None)
            if values_mapping:
                label_text += '\n%s' % values_mapping
            if mask_flag:
                param.array.mask = False
            axis.plot(*args, label=label_text)
            axis.legend(loc='upper right', **legendprops)
            if index < len(axes):
                setp(axis.get_xticklabels(), visible=False)
        plt.legend(prop={'size': 10})
    plt.show()


def process_raw_hdf(hdf, axes):
    with hdf_file(hdf) as h:
        params = h.get_params()

    params_to_plot = {}
    for axis in axes:
        if axis is not None:
            for param in axis:
                try:
                    params_to_plot[param] = params[param]
                except KeyError:
                    print('Parameter %s was not found in the HDF file.' % param)

    filtered_axes = dict(enumerate(filter(None, axes), start=1))
    return params_to_plot, filtered_axes


# Processing and plotting loops
###############################################################################


class ProcessError(Exception):
    pass


class ProcessAndPlotLoops(threading.Thread):
    def __init__(self, hdf_path, plot_changed, lfl_path, function):
        '''
        :param hdf_path: Output path for HDF file.
        :type hdf_path: str
        '''
        self._hdf_path = hdf_path
        self._lfl_path = lfl_path
        self._function = function

        self._changed_params = set()
        self._plot_changed = plot_changed

        self.__error_lock = threading.Lock()
        self.__error_messages = []

        self.exit_loop = threading.Event()
        self._ready_to_plot = threading.Event()

        self._axes = None

        self._last_config = None

        super(ProcessAndPlotLoops, self).__init__()

    def _queue_error_message(self, title, message):
        self.__error_lock.acquire()
        self.__error_messages.append((title, message))
        self.__error_lock.release()

    def _get_error_message(self):
        self.__error_lock.acquire()
        if self.__error_messages:
            message = self.__error_messages.pop()
        else:
            message = None
        self.__error_lock.release()
        return message

    def process_data(self, lfl_path, data_path, output_path,
                     superframes_in_memory, plot_changed, mask_flag, aircraft_info):
        '''
        :param lfl_path: Path of LFL file.
        :type lfl_path: str
        :param output_path: Output path of HDF file.
        :type output_path: str
        :param superframes_in_memory: Number of superframes to process in
            memory.
        :type superframes_in_memory: int
        :param plot_changed: Whether or not to plot parameters which change
            within the LFL.
        :type plot_changed: bool
        '''
        # Load config to read AXIS groups.
        try:
            config = configobj.ConfigObj(lfl_path)
        except configobj.ConfigObjError as err:
            message = configobj_error_message(err)
            self._queue_error_message('Error while parsing LFL!', message)
            raise ValueError(message)

        if self._last_config:
            for param_name, param_conf in config['Parameters'].items():
                # TODO: Param added, not only changed.
                if param_name in self._last_config['Parameters'] and \
                   param_conf != self._last_config['Parameters'][param_name]:
                    self._changed_params.add(param_name)

        self._last_config = dict(config)

        axes = {1: ['Altitude STD']}
        if plot_changed and self._changed_params:
            # Add an axis for parameters which have changed.
            axes[2] = list(self._changed_params)

        # Read AXIS_* parameter groups.
        axis_offset = len(axes)
        group_index = 1
        while True:
            group_name = 'AXIS_%d' % group_index
            try:
                axis = config['Parameter Group'][group_name]
                # Force a single entry to look like a list.
                if hasattr(axis, "__iter__"):
                    axes[group_index + axis_offset] = axis
                else:
                    axes[group_index + axis_offset] = [axis]
            except KeyError:
                break
            group_index += 1

        if len(axes) == 1:
            message = 'AXIS_1 parameter group is not defined! Please define ' \
                      'a parameter group within the LFL named AXIS_1. ' \
                      'Subsequent axes can be defined with groups named ' \
                      'AXIS_2, AXIS_3, etc.'
            self._queue_error_message('AXIS_1 group missing', message)
            raise ValueError(message)

        # Create a list of all parameters within the groups.
        param_names = set(itertools.chain.from_iterable(axes.values()))
        if 'Superframe Counter' in param_names:
            param_names.remove('Superframe Counter')

        try:
            lfl_parser, param_list = parse_lfl(
                lfl_path, param_names=param_names, aircraft_info=aircraft_info, required=False)
        except configobj.ConfigObjError as err:
            message = configobj_error_message(err)
            self._queue_error_message('Error while parsing LFL!', message)
            raise ValueError(message)

        param_errors = lfl_parser.format_errors()
        if param_errors:
            self._queue_error_message('Parameter Errors', param_errors)

        print('Processing params: %s' % ', '.join([p.name for p in param_list]))
        try:
            create_hdf(data_path, output_path, lfl_parser.frame, param_list,
                       superframes_in_memory=superframes_in_memory)
        except Exception as err:
            message = 'Error occurred during processing. Please ensure the ' \
                'frame doubling is declared if applicable as well as both ' \
                'the LFL and raw data file are correct. Exception:\n%s' % err
            self._queue_error_message('Processing failed!', message)
            traceback.print_exc()
            raise ProcessError(message)

        print('Finished processing, output: %s' % output_path)
        return axes

    def run(self):
        '''
        The processing loop.
        '''
        prev_mtime = None
        while True:
            mtime = os.path.getmtime(self._lfl_path)
            if not prev_mtime or mtime > prev_mtime:
                if self._ready_to_plot.is_set():
                    self._ready_to_plot.clear()
                try:
                    self._axes = self._function()
                except ValueError:
                    continue
                except ProcessError as err:
                    print(err)
                    self.exit_loop.set()
                    return
                else:
                    self._ready_to_plot.set()
                finally:
                    prev_mtime = mtime
            else:
                time.sleep(1)

    def process_hdf_axis(self, hdf_file, axis1, axis2, axis3, axis4, axis5, axis6):
        pass

    def plot_loop(self, mask_flag):
        '''
        The plotting loop.
        '''
        while True:
            # For some strange reason it appears that printing the following
            # line affects the plotting window being shown on windows.
            if self.exit_loop.is_set():
                return
            error_message = self._get_error_message()
            if error_message:
                show_error_dialog(*error_message)
                continue
            if self._ready_to_plot.is_set():
                self._ready_to_plot.clear()
                try:
                    with hdf_file(self._hdf_path) as hdf:
                        # iterate over whole file as only those params
                        # required were converted earlier into the HDF file
                        params = hdf.get_params()
                    title = os.path.basename(self._hdf_path)
                    plot_parameters(params, self._axes, mask_flag, title=title)
                except ValueError as err:
                    print('Waiting for you to fix this error: %s' % err)
                except Exception as err:
                    # traceback required?
                    print('Exception raised! %s: %s' % (err.__class__.__name__,
                                                        err))
            else:
                time.sleep(1)


class Frame(wx.Frame):
    '''
    There a built-in message dialogs which display a message, but they were
    freezing due to the application's threading model.
    '''
    def __init__(self, title, message):
        wx.Frame.__init__(self, None, title=title)
        #self.Bind(wx.EVT_CLOSE, self.OnClose)
        panel = wx.Panel(self)
        box = wx.BoxSizer(wx.VERTICAL)

        m_text = wx.StaticText(panel, -1, message, size=(340, 100),
                               style=wx.TE_MULTILINE)
        m_text.SetSize(m_text.GetBestSize())
        button = wx.Button(panel, label='OK')
        button.SetDefault()
        button.Bind(wx.EVT_BUTTON, self.OnClose)
        box.Add(m_text, flag=wx.ALL)
        box.Add(button, flag=wx.EXPAND)

        panel.SetSizerAndFit(box)
        self.Layout()
        self.Fit()

    def OnClose(self, event):
        self.Destroy()


def show_error_dialog(title, message):
    '''
    Show error.
    '''
    frame = Frame(title, message)
    frame.Show()
    app.MainLoop()


def lfl_file_dialog():
    #TOOD: Remember last directory accessed!
    lfl_dialog = wx.FileDialog(None, message="Please choose an LFL file",
                               defaultDir='',
                               wildcard="*.lfl")
    if lfl_dialog.ShowModal() == wx.ID_OK:
        lfl_path = lfl_dialog.GetPath()
    else:
        show_error_dialog('Error!', 'An LFL file must be selected.')
        sys.exit(1)
    return lfl_path


def data_file_dialog():
    data_dialog = wx.FileDialog(None, message="Please choose a raw data file",
                                defaultDir='',
                                wildcard="*.*")
    if data_dialog.ShowModal() == wx.ID_OK:
        data_path = data_dialog.GetPath()
    else:
        show_error_dialog('Error!', 'A raw data file must be selected.')
        sys.exit(1)
    return data_path


def main():
    print('FlightDataPlotter (c) Copyright 2019 Flight Data Services, Ltd.')
    print('  - Powered by POLARIS')
    print('  - http://www.flightdatacommunity.com')
    print('')

    parser = create_parser()
    plot_args = validate_args(parser)

    lfl_path = plot_args[0]
    data_path = plot_args[1]
    hdf_path = plot_args[2]
    superframes_in_memory=plot_args[3]
    plot_changed = plot_args[4]
    mask_flag = plot_args[5]
    csv_type = plot_args[6]
    hdf_flag = plot_args[7]
    axes = [['Altitude STD'], plot_args[8], plot_args[9], plot_args[10], plot_args[11], plot_args[12]]
    aircraft_info = plot_args[13]

    if hdf_flag:
        params, axes = process_raw_hdf(data_path, axes)
        plot_parameters(params, axes, mask_flag)
        pass
    elif csv_type:
        parameters = [item for sublist in filter(None, axes) for item in sublist]
        CSV_FUNCTIONS[csv_type](data_path, hdf_path, parameters=parameters)
        params, axes = process_raw_hdf(hdf_path, axes)
        plot_parameters(params, axes, mask_flag)
    else:
        plot_func = lambda: process_thread.process_data(lfl_path, data_path, hdf_path, superframes_in_memory,
                                                        plot_changed, mask_flag, aircraft_info)
        process_thread = ProcessAndPlotLoops(hdf_path, plot_changed,
                                             lfl_path, plot_func)
        process_thread.start()
        try:
            process_thread.plot_loop(mask_flag)
        except KeyboardInterrupt:
            print('Setting exit_loop event.')
            process_thread.exit_loop.set()
        finally:
            # If the file is in a temporary location, remove it.
            if hdf_path.startswith(tempfile.gettempdir()) \
               and os.path.isfile(hdf_path):
                try:
                    os.remove(hdf_path)
                    print('Removed temporary HDF file: %s.' % hdf_path)
                except (OSError, IOError):
                    print('Could not remove temporary HDF file: %s.' % hdf_path)


if __name__ == '__main__':
    logging.basicConfig()
    main()
