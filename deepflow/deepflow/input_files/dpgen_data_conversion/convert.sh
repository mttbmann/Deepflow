#!/usr/bin/zsh

###  12 processes, all on one node
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --constraint=Rocky8
#SBATCH --job-name=data_conv
### Limit for maximum memory per slot (in MB)
#SBATCH --mem-per-cpu=3900

### The time limit for the job in minutes (reaching this time limit, the process is signaled and killed)
#SBATCH --time=40:00:00

# declare the merged STDOUT/STDERR file
#SBATCH --output=output.%J.txt

#SBATCH --account=PROJECT_CPU_PLACEHOLDER

### end of Slurm SBATCH definitions

### beginning of executable commands

### load the necessary module files

ml Python
python3 pickdata.py 

### your program goes here (a.out is an example)

