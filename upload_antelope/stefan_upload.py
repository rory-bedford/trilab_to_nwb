from datetime import datetime
import os
import numpy as np
from dateutil import tz
from pathlib import Path
import logging
import multiprocessing as mp
import functools
from antelope import insert_nwb, upload_rig_json
from antelope.load_connection import *
from pynwb import NWBHDF5IO

def upload_trial(nwbpath, session_id, log_queue, experimenter, experiment_id, behaviourrig_id):
    """
    Function takes in an NWB file, extracts metadata according to our custom rules, and uploads to the database.
    """

    # convert to nwb
    try:

        with NWBHDF5IO(nwbpath, 'r') as io:
            nwbfile = io.read()

        # first, calculate if animal already in the database, isnert if not with metadata
        animal_name = nwbfile.subject.subject_id
        animal_key = {'experimenter':experimenter, 'experiment_id': experiment_id, 'animal_name': animal_name}

        if not (Animal & animal_key):

            animal_key['weight'] = nwbfile.subject.weight.split(' ')[0] + 'g'
            animal_key['species'] = nwbfile.subject.species

            Animal.insert1({**animal_key, 'animal_notes':''}, skip_duplicates=True) # skip duplicates in case of transaction concurrency

        # grab animal key
        animal_key = (Animal & animal_key).proj().fetch1()

        # insert new session
        session_key = {
            'experimenter': experimenter,
            'experiment_id': experiment_id,
            'session_id': session_id,
            'session_name': f'{nwbfile.session_start_time.strftime("%d %B")} session {experiment_id}',
            'session_timestamp': nwbfile.session_start_time,
            'session_notes': nwbfile.experiment_description
        }
        Session.insert1(session_key)
        session_key = (Session & session_key).proj().fetch1()

        world_key = {**session_key, 'behaviourrig_id': behaviourrig_id}
        self_key = {**animal_key, 'session_id':session_id}

        # insert nwb file
        insert_nwb(world_key, {1:self_key}, nwbpath)

    except Exception as e:
        log_queue.put(f'{nwbpath.stem} unsuccessful\n{e}')

    else:
        log_queue.put(f'{nwbpath.stem} uploaded succesfully')


if __name__ == '__main__':

    # first, we need to insert the experiment table
    experiment_key = dict(
        experimenter = 'srogers',
        experiment_name = 'March_training'
    )
    if not (Experiment & experiment_key):
        Experiment.insert1({**experiment_key, 'experiment_notes':''})
    experiment_id = (Experiment & experiment_key).proj().fetch1('experiment_id')

    # next, insert rig json
    json_path = Path('behaviour_json/stefan_rig.json')
    json_name = 'Red Hex'
    if not (BehaviourRig & {'experimenter':'srogers', 'rig_name': json_name}):
        upload_rig_json('srogers', json_name, json_path)
    behaviourrig_id = (BehaviourRig & {'experimenter':'srogers', 'rig_name': json_name}).proj().fetch1('behaviourrig_id')

    # set data directories
    basedir = Path('/cephfs2/srogers/March_training')

    # set up logger
    logging.basicConfig(filename='logs/upload_antelope.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # get list of all files to convert
    base = [f for f in basedir.iterdir() if f.is_dir()]
    files =[]
    for b in base:
        files.extend([f / f'{f.name}.nwb' for f in b.iterdir() if f.is_dir() and f.name[6] == '_'])
    files = files[:2] # just for testing

    # need to calculate session_ids now, due to multiprocessing
    max_session_id = max((Session & {'experimenter':'srogers', 'experiment_id':experiment_id}).fetch('session_id'), default=0)
    session_ids = range(max_session_id+1, max_session_id+1+len(files))

    # set up multiprocessing queue for logs
    manager = mp.Manager()
    log_queue = manager.Queue()

    args = list(zip(files, session_ids))

    # start multiprocessing
    with mp.Pool(processes=int(os.environ['SLURM_CPUS_PER_TASK'])-1) as pool:

        # make partial function for convert_to_nwb
        partial_upload = functools.partial(upload_trial, log_queue=log_queue, experimenter='srogers', experiment_id=experiment_id, behaviourrig_id=behaviourrig_id)

        # run conversion
        pool.starmap(partial_upload, args)

    # get logs
    logs = []
    while not log_queue.empty():
        logs.append(log_queue.get())

    # Write logs to the log file
    for log in logs:
        logging.info(log)
