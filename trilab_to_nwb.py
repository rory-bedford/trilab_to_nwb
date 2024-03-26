from pynwb import NWBHDF5IO, NWBFile, TimeSeries
from pynwb.misc import IntervalSeries
from pynwb.file import Subject
from pynwb.image import ImageSeries

from datetime import datetime
from dateutil import tz
from uuid import uuid4
import numpy as np
from pathlib import Path
import json
import shutil


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

# fuunction converts intervals to digital events with length of time
def intervals_to_digital_events(intervals, interval_timestamps):
    """
    Convert intervals to digital events
    :param intervals: intervals (np.array)
    :param interval_timestamps: timestamps of intervals (np.array)
    :return: digital events (np.array)
    :return: timestamps (np.array)
    """

    # make sure it starts with an on time and ends with and off time
    if intervals.shape[0] > 0:
        if intervals[0] == -1:
            intervals = intervals[1:]
            interval_timestamps = interval_timestamps[1:]
        if intervals[-1] == 1:
            intervals = intervals[:-1]
            interval_timestamps = interval_timestamps[:-1]

    # find lengths of on times
    digital_events = interval_timestamps[intervals == -1] - interval_timestamps[intervals == 1]
    timestamps = interval_timestamps[intervals == 1]
    
    return digital_events, timestamps


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

    for i in ['SPOT','BUZZER','LED_']:

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

    # valve reqard data
    for j in range(1,7):

        # load data
        array = np.array(data['VALVE' + str(j)], dtype=np.int8)

        # load epochs and epoch timestamps
        intervals, interval_timestamps = timeseries_to_intervals(timestamps, array)
        digital_events, digital_event_timestamps = intervals_to_digital_events(intervals, interval_timestamps)

        # create timeseries
        timeseries = TimeSeries(
            name='VALVE' + str(j),
            data=digital_events,
            timestamps=digital_event_timestamps,
            unit='s',
            comments='Reward amounts are measured by how long the valve is open for',
            description='Reward amount at VALVE' + str(j)
        )

        # add to NWB file
        nwbfile.add_stimulus(timeseries)

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

    # load video data
    videofile = directory / (directory.stem + '_raw_MP.avi')
    if not videofile.exists():
        raise FileNotFoundError(f'Video file {videofile} not found')
    video_timestamps = directory / ('_'.join(directory.stem.split('_')[:2]) + '_video_frame_times.json')
    if not video_timestamps.exists():
        raise FileNotFoundError(f'Video timestamps file {video_timestamps} not found')

    # load video timestamps
    with open(video_timestamps, 'r') as f:
        video_timestamps = json.load(f)

    # make numpy array of timestamps
    numeric_keys = [key for key in video_timestamps.keys() if key.isdigit()]
    sorted_keys = sorted(numeric_keys, key=lambda x: int(x))
    timestamps = np.array([video_timestamps[key] for key in sorted_keys], dtype=np.float64)

    # create ImageSeries
    behaviour_video = ImageSeries(
        name='behaviour_video',
        external_file=['./' + videofile.name],
        starting_frame=[0],
        format='external',
        timestamps=timestamps,
        unit='s',
        description='Behaviour video of mouse during trial'
    )

    # add to NWB file
    nwbfile.add_acquisition(behaviour_video)

    # save NWB file
    outdir.mkdir(parents=True, exist_ok=True)
    savepath = outdir / (directory.stem + '.nwb')
    with NWBHDF5IO(savepath, 'w') as io:
        io.write(nwbfile)

    # copy video
    videopath = outdir / videofile.name
    shutil.copy(videofile, videopath)
