#!/bin/bash -l

#SBATCH --job-name=convert_nwb
#SBATCH --partition=cpu
#SBATCH --cpus-per-task=40
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --error=logs/convert_nwb_%j.err
#SBATCH --output=logs/convert_nwb_%j.out

mamba activate nwb
srun python stefan_convert.py
