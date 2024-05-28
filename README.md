## Trilab to NWB Conversion

This repository contains scripts to convert the processed DAQ data from the trilab behavioural rig to NWB format.

The main script is trilab_to_nwb.py, which contains the trilab_to_nwb function, which takes in a folder containing the raw rig output, and a destination folder, and performs the conversion.

The script stefan_convert.py and stefan_convert.slurm just contain wrappers to run this in parallel for all of stefan's data, with logging.

Otherwise, this repo also contains some scripts to make the custom behaviour json for importing these NWB files into Antelope (our DataJoint pipeline).

The upload_antelope scripts parse a folder of NWB files and upload them to antelope with the appropriate metadata.



The important info here is the schema for the NWB files:

Under the stimuli group, we have the following datasets:

VALVE 1 through 6: TimeSeries objects, where the data is the time the valve was open in seconds.

SPOT, BUZZER and LED 1 through 6, and GO_CUE and NOGO_CUE: IntervalSeries objects, representing the on and off times of these events

Under the acquisition group, we have the following datasets:

SENSOR 1 through 6: IntervalSeries objects, representing the on and off times of the sensor being triggered

scales: TimeSeries object, representing the scale measurements

behaviour_video: ImageSeries with an external video file
