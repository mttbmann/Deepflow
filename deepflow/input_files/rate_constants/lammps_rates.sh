#!/usr/bin/zsh

#SBATCH --gres=gpu:1


#SBATCH --job-name=lammps



### The time limit for the job in minutes (reaching this time limit, the process is signaled and killed)
#SBATCH --time=0:10:00

#SBATCH --account=rwth1622

# declare the merged STDOUT/STDERR file
#SBATCH --output=output.%J.txt

#SBATCH --partition=c23g


### end of Slurm SBATCH definitions

### beginning of executable commands

### load the necessary module files

export DEEPMD_KIT_PATH=~/deepmd-kit/bin/activate
source $DEEPMD_KIT_PATH

lmp -i input.lammps