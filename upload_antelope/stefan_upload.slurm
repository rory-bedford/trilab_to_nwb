#!/bin/bash -l

#SBATCH --job-name=upload_antelope
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=40
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --error=logs/upload_nwb_%j.err
#SBATCH --output=logs/upload_nwb_%j.out

mamba activate antelope
python upload_antelope/stefan_upload.py
