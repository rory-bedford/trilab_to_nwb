from datetime import datetime
import os
import numpy as np
from dateutil import tz
from pathlib import Path
import logging
import multiprocessing as mp
import functools

from trilab_to_nwb import convert_to_nwb

if __name__ == '__main__':

    # set data directories
    basedir = Path('/cephfs2/srogers/December_training_data')
    savedir = Path('/cephfs/rbedford/stefan_nwb')

    # set up logger
    logging.basicConfig(filename='logs/logfile.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # get list of all files to convert
    files = [f for f in basedir.iterdir() if f.is_dir() and f.stem[6] == '_']

    # create list of output directories
    outdirs = [savedir / f.stem for f in files]

    # set up multiprocessing queue for logs
    manager = mp.Manager()
    log_queue = manager.Queue()

    # zip arguments for multiprocessing
    args = list(zip(files, outdirs))

    # start multiprocessing
    with mp.Pool(processes=int(os.environ['SLURM_CPUS_PER_TASK'])-1) as pool:

        # make partial function for convert_to_nwb
        partial_convert = functools.partial(convert_to_nwb, log_queue=log_queue)

        # run conversion
        pool.starmap(partial_convert, args)

    # get logs
    logs = []
    while not log_queue.empty():
        logs.append(log_queue.get())

    # Write logs to the log file
    for log in logs:
        logging.info(log)
