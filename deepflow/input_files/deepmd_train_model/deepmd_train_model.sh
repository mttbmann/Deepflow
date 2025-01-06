#!/usr/bin/zsh

#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:4

#SBATCH --job-name=deepmd_train_model

#SBATCH --time=10:00:00

#SBATCH --account=PROJECT_GPU_PLACEHOLDER

#SBATCH --output=output.%J.txt

#SBATCH --partition=c23g

#SBATCH --mem=150G

export DEEPMD_KIT_PATH=DEEP_MD_CONDA_PATH_PLACEHOLDERbin/activate
source $DEEPMD_KIT_PATH

dp train input.json

wait

dp freeze -o fm.pb

