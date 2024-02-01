from pynwb import NWBHDF5IO, NWBFile, TimeSeries
from pynwb.misc import IntervalSeries
from pynwb.file import Subject

from datetime import datetime
from dateutil import tz
from uuid import uuid4
import numpy as np
from pathlib import Path
import json


# define function that converts to nwb and logs
def convert_to_nwb(indir, outdir, log_queue):

    # convert to nwb
    try:
        nwb = trilab_to_nwb(indir, outdir)
        log_queue.put(f'{indir.stem} converted to nwb succesfully')

    except FileNotFoundError as e:
        log_queue.put(f'{indir.stem} unsuccessful - input data missing\n{e}')


# function takes timestamps and on/off and returns intervals for NWB
def timeseries_to_intervals(timestamps, signal):
    """
    Convert timestamps and on/off signal to NWB epochs
    :param timestamps: timestamps of signal (list)
    :param signal: on/off signal (list)
    :return: NWB intervals: 1 for on times, -1 for off times (np.array)
    :return: timestamps (np.array)
    """
    
    # compute difference array
    diff = np.diff(signal, prepend=0)

    # find indices of on and off times
    indices = np.where(diff != 0)[0]

    # load timestamps and on/off signal
    interval_timestamps = timestamps[indices]
    intervals = diff[indices]

    return intervals, interval_timestamps
    

# function to convert trilab data to NWB
def trilab_to_nwb(directory, outdir):
    """
    Convert trilab data to NWB
    :param directory: directory containing output from one preprocessed session from Stefan's rig (pathlib)
    :param trialdate: datetime object of trial datetime
    :param subject_id: subject ID (str)
    """
    
    # first extract datetime from directory name
    datestring = '_'.join(directory.stem.split('_')[:2])

    # convert to datetime object
    trialdate = datetime.strptime(datestring, '%y%m%d_%H%M%S')
    trialdate = trialdate.replace(tzinfo=tz.gettz('Europe/London'))

    # extract subject from directory name
    subject_id = directory.stem.split('_')[2]

    # open data file
    datafile = directory / ('_'.join(directory.stem.split('_')[:2]) + '_processed_DAQ_data.json')
    with open(datafile, 'r') as f:
        data = json.load(f)

    # set up NWB file
    nwbfile = NWBFile(
        session_description='training session',
        identifier=str(uuid4()),
        session_start_time=trialdate,
        experimenter='Stefan Rogers-Coltman',
        institution='MRC LMB',
        lab='Tripodi Lab',
    )

    # set up subject info
    nwbfile.subject = Subject(
        subject_id=subject_id,
        species='Mouse'
    )

    # load timestamps array
    timestamps = np.array(data['timestamps'], dtype=np.float64)

    # loop through stimulus data types

    for i in ['SPOT','BUZZER','LED_','VALVE']:

        for j in range(1,7):

            # load data
            array = np.array(data[i + str(j)], dtype=np.int8)
            
            # load epochs and epoch timestamps
            intervals, interval_timestamps = timeseries_to_intervals(timestamps, array)

            # create interval series
            interval_series = IntervalSeries(
                name=i + str(j),
                timestamps=interval_timestamps,
                data=intervals,
                description='Intervals for ' + i + str(j)
            )

            # add to NWB file
            nwbfile.add_stimulus(interval_series)

    for i in ['GO_CUE','NOGO_CUE']:

        # load data
        array = np.array(data[i], dtype=np.int8)
        
        # load epochs and epoch timestamps
        intervals, interval_timestamps = timeseries_to_intervals(timestamps, array)

        # create interval series
        interval_series = IntervalSeries(
            name=i,
            timestamps=interval_timestamps,
            data=intervals,
            description='Intervals for ' + i 
        )

        # add to NWB file
        nwbfile.add_stimulus(interval_series)

    ## loop through behaviour data types

    # sensor data
    i = 'SENSOR'
    for j in range(1,7):

        # load data
        array = np.array(data[i + str(j)], dtype=np.int8)
        
        # load epochs and epoch timestamps
        intervals, interval_timestamps = timeseries_to_intervals(timestamps, array)

        # create interval series
        interval_series = IntervalSeries(
            name=i + str(j),
            timestamps=interval_timestamps,
            data=intervals,
            description='Epochs for ' + i + str(j)
        )

        # add to NWB file
        nwbfile.add_acquisition(interval_series)

    # scales data
    # load weights
    weights = np.array(data['scales_data']['weights'], dtype=np.float64)

    # load timestamps
    timestamps = np.array(data['scales_data']['timestamps'], dtype=np.float64)

    # create timeseries
    timeseries = TimeSeries(
        name='scales',
        data=weights,
        timestamps=timestamps,
        unit='g',
        comments=f'''Threshold set to {data['scales_data']['mouse_weight_threshold']}g''',
        description='Scales data'
    )

    # add to NWB file
    nwbfile.add_acquisition(timeseries)

    # save NWB file
    outdir.mkdir(parents=True, exist_ok=True)
    savepath = outdir / (directory.stem + '.nwb')
    with NWBHDF5IO(savepath, 'w') as io:
        io.write(nwbfile)
