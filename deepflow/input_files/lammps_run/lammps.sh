#!/usr/bin/zsh

#SBATCH --ntasks=4
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:2


#SBATCH --job-name=lammps



### The time limit for the job in minutes (reaching this time limit, the process is signaled and killed)
#SBATCH --time=48:00:00

#SBATCH --account=rwth1622

# declare the merged STDOUT/STDERR file
#SBATCH --output=output.%J.txt

#SBATCH --partition=c18g


### end of Slurm SBATCH definitions

### beginning of executable commands

### load the necessary module files

export DEEPMD_KIT_PATH=~/deepmd_gpu/installation/bin/activate
source $DEEPMD_KIT_PATH

lmp -i input.lammps
