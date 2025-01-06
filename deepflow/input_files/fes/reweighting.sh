#!/usr/bin/zsh

#SBATCH --nodes=1
#SBATCH --ntasks=1



#SBATCH --job-name=reweighting

### Limit for maximum memory per slot (in MB)
#SBATCH --mem-per-cpu=3900

### The time limit for the job in minutes (reaching this time limit, the process is signaled and killed)
#SBATCH --time=48:00:00

#SBATCH --account=simcat

# declare the merged STDOUT/STDERR file
#SBATCH --output=output.%J.txt



### end of Slurm SBATCH definitions

### beginning of executable commands

### load the necessary module files




export CONDA_ROOT=$HOME/miniconda3
. $CONDA_ROOT/etc/profile.d/conda.sh
export PATH="$CONDA_ROOT/bin:$PATH"

conda activate seaborn

python3 reweighting.py --colvar COLVAR --sigma 0.1 --temp 310 --cv t --bias metad.rbias --reverse --stride 1 --deltaFat 0.0 --skiprows 1000
