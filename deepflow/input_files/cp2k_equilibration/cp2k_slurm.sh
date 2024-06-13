#!/usr/bin/zsh

#SBATCH --job-name={job_name_eq}

### 12 processes, all on one node
#SBATCH --nodes=1
#SBATCH --ntasks=CPU_CORES_PLACEHOLDER

### Limit for maximum memory per slot (in MB)
#SBATCH --mem-per-cpu=3900

#SBATCH --account=PROJECT_CPU_PLACEHOLDER

### The time limit for the job in minutes (reaching this time limit, the process is signaled and killed)
#SBATCH --time=20:00:00

### load the necessary module files
module load GCC/12.2.0
module load OpenMPI/4.1.4
module load CP2K/2023.1

### start the MPI binary
$MPIEXEC $FLAGS_MPI_BATCH cp2k.popt {mod_nvt.inp} > nvt.out
