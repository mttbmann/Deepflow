#!/usr/bin/zsh

### 12 processes, all on one node
#SBATCH --nodes=1
#SBATCH --ntasks=24

### Limit for maximum memory per slot (in MB)
#SBATCH --mem-per-cpu=3900

#SBATCH --job-name=deepmd_get_sel

#SBATCH --time=1:00:00

#SBATCH --account=PROJECT_CPU_PLACEHOLDER

#SBATCH --output=deepmd_sel.out



export DEEPMD_KIT_PATH=DEEP_MD_CONDA_PATH_PLACEHOLDER
source $DEEPMD_KIT_PATH

wait
dp neighbor-stat -s ../dpgen_data_conversion/training_data -r R_CUT_PLACEHOLDER -t {type_map}
