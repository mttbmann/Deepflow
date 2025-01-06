import glob
import shutil
import os
import re
import random
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as stats
import warnings
import matplotlib
import csv
from statsmodels.stats.diagnostic import lilliefors
matplotlib.use('Agg')

class LammpsCalculateRateConstants:
    @staticmethod
    def generate_start(model_iter: int):
        model_iter_str = f"{model_iter:06d}"
        
        # Create directories
        os.makedirs("lammps_calculate_rate_constants/init_traj", exist_ok=True)
        os.makedirs("lammps_calculate_rate_constants/init_traj/task.000.000000", exist_ok=True)
        
        # Define paths
        md_folder = f"dpgen_active_learning/iter.{model_iter_str}/01.model_devi/"
        path_model = sorted(glob.glob(f"dpgen_active_learning/iter.{model_iter_str}/00.train/graph.*.pb"))
        
        # Copy model files
        for model in path_model:
            model_name = os.path.basename(model)
            shutil.copyfile(model, f"lammps_calculate_rate_constants/init_traj/{model_name}")
        
        # Copy other necessary files
        shutil.copyfile(f"{md_folder}/confs/000.0000.lmp", f"lammps_calculate_rate_constants/init_traj/task.000.000000/conf.lmp")
        shutil.copyfile(f"{md_folder}/task.000.000000/input.lammps", f"lammps_calculate_rate_constants/init_traj/task.000.000000/input.lammps")
        shutil.copyfile("input_files/rate_constants/lammps.sh", "lammps_calculate_rate_constants/init_traj/task.000.000000/lammps.sh")

        with open("lammps_calculate_rate_constants/init_traj/task.000.000000/input.lammps", 'r') as f1:
            modify_input_lammps = f1.read()

        # Replace the desired strings
        modify_input_lammps = re.sub(r'NSTEPS\s+equal\s+\d+', 'NSTEPS          equal 1000000', modify_input_lammps)
        modify_input_lammps = modify_input_lammps.replace(
            "dump            dpgen_dump all custom 200    all.lammpstrj id type x y z",
            "dump            dpgen_dump all custom 200    all.lammpstrj id type x y z\nrestart 1000 restart.*.equil"
        )

        modify_input_lammps = modify_input_lammps.replace("fix            dpgen_plm all plumed plumedfile input.plumed outfile output.plumed","")

        # Write the modified content back to the file
        with open("lammps_calculate_rate_constants/init_traj/task.000.000000/input.lammps", 'w') as f1:
            f1.write(modify_input_lammps)

        # Change directory and submit job
        current_dir = os.getcwd()
        try:
            os.chdir("lammps_calculate_rate_constants/init_traj/task.000.000000")
            os.system("sbatch lammps.sh")
        finally:
            os.chdir(current_dir)




    @staticmethod
    def run_rates(model_iter: int, number_parallel_md=1):
        """
        Sets up and runs multiple MD simulations in parallel using LAMMPS.

        Parameters:
        model_iter (int): The iteration number of the model.
        number_parallel_md (int): The number of parallel MD simulations to run.
        """
        
        # Determine the appropriate pattern based on the length of model_iter
        model_iter_str = f"{model_iter:06d}"

        # Define the directories
        md_folder = os.path.join("dpgen_active_learning", f"iter.{model_iter_str}", "01.model_devi")
        path_model = sorted(glob.glob(os.path.join("dpgen_active_learning", f"iter.{model_iter_str}", "00.train", "graph.*.pb")))

        # Find existing directories and determine the next available number
        existing_dirs = glob.glob(os.path.join("lammps_calculate_rate_constants", f"{model_iter}_*"))
        existing_nums = [int(dir.split('_')[-1]) for dir in existing_dirs]
        next_num = max(existing_nums, default=-1) + 1

        # Create the new directory
        new_dir = os.path.join("lammps_calculate_rate_constants", f"{model_iter}_{next_num}")
        os.makedirs(new_dir, exist_ok=True)

        # Copy model files to the new directory
        for model in path_model:
            shutil.copyfile(model, os.path.join(new_dir, os.path.basename(model)))

        # Copy the input LAMMPS file
        input_lammps_src = os.path.join(md_folder, "task.000.000000", "input.lammps")
        input_lammps_dst = os.path.join(new_dir, "input.lammps")
        shutil.copyfile(input_lammps_src, input_lammps_dst)

        # Get the list of restart files
        restart_files = sorted(glob.glob(os.path.join("lammps_calculate_rate_constants", "init_traj", "task.000.000000", "restart.*.equil")))
        current_dir = os.getcwd()

        for i in range(number_parallel_md):
            # Create subdirectory for each MD run
            sub_dir = os.path.join(new_dir, f"{i}")
            os.makedirs(sub_dir, exist_ok=True)
            restart_file = random.choice(restart_files)
            
            with open(input_lammps_dst, 'r') as f1:
                modify_input_lammps = f1.readlines()

            # Iterate over lines to find and modify the NSTEPS variable
            for j, line in enumerate(modify_input_lammps):
                if re.match(r'variable\s+NSTEPS\s+equal\s+\d+', line):
                    modify_input_lammps[j] = 'variable        NSTEPS          equal 20000000\n'

            # Replace lines starting with specific strings
            modified_lines = []
            for line in modify_input_lammps:
                if line.startswith("dump"):
                    modified_lines.append("dump            dpgen_dump all custom 1000    all.lammpstrj id type x y z\n")
                elif line.startswith("velocity"):
                    modified_lines.append("\n")
                else:
                    modified_lines.append(line)

            # Join lines into a single string
            modified_content = ''.join(modified_lines)
            
            # Replace 'read_data' with 'read_restart' and the new restart file name
            modified_content = modified_content.replace('read_data       conf.lmp', f'read_restart       {os.path.basename(restart_file)}\nreset_timestep 0')
            
            # Add 'write_restart' command after 'run' command
            modified_content = modified_content.replace('run             ${NSTEPS}', 'run             ${NSTEPS}\nwrite_restart restart.equil')

            # Define the output file path
            output_file_path = os.path.join(sub_dir, "input.lammps")
            
            # Write the modified content to the new file
            with open(output_file_path, 'w') as f1:
                f1.write(modified_content)

            # Copy other necessary files
            shutil.copyfile(os.path.join("input_files", "rate_constants", "lammps_rates.sh"), os.path.join(sub_dir, "lammps.sh"))
            shutil.copyfile(os.path.join("input_files", "rate_constants", "plumed.dat"), os.path.join(sub_dir, "input.plumed"))
            shutil.copyfile(restart_file, os.path.join(sub_dir, os.path.basename(restart_file)))

            # Submit the job
            try:
                os.chdir(sub_dir)
                os.system("sbatch lammps.sh")
            finally:
                os.chdir(current_dir)

    @staticmethod
    def restart_rates(model_iter: int, number_folder=0):
        # Determine the appropriate pattern based on the length of model_iter
        model_iter_str = f"{model_iter:06d}"

        lammps_input_files = glob.glob(os.path.join("lammps_calculate_rate_constants", f"{model_iter}_{number_folder}", "**", "input.lammps"))
        plumed_input_files = glob.glob(os.path.join("lammps_calculate_rate_constants", f"{model_iter}_{number_folder}", "**", "input.plumed"))

        for lammps_input in lammps_input_files:
            with open(lammps_input, 'r') as f1:
                modify_input_lammps = f1.readlines()

            # Replace lines starting with the specific strings
            modified_lines = []
            for line in modify_input_lammps:
                if line.startswith("read_restart"):
                    modified_lines.append("read_restart       restart.equil\n")
                elif line.startswith("velocity"):
                    modified_lines.append("\n")
                elif line.startswith("reset_timestep 0"):
                    modified_lines.append("\n")
                else:
                    modified_lines.append(line)

            # Write the modified lines back to the file
            with open(lammps_input, 'w') as f1:
                f1.writelines(modified_lines)

        for plumed_input in plumed_input_files:
            with open(plumed_input, 'r') as f1:
                modify_input_plumed = f1.readlines()

            # Replace lines starting with the specific strings
            modified_lines = []
            for line in modify_input_plumed:
                if line.startswith("#RESTART"):
                    modified_lines.append("RESTART\n")
                else:
                    modified_lines.append(line)

            # Write the modified lines back to the file
            with open(plumed_input, 'w') as f1:
                f1.writelines(modified_lines)

        current_dir = os.getcwd()

        for lammps_input in lammps_input_files:
            sub_dir = os.path.dirname(lammps_input)
            try:
                os.chdir(sub_dir)
                os.system("sbatch lammps.sh")
            finally:
                os.chdir(current_dir)

        

    @staticmethod
    def calc_rates():
        def read_file(filename):
            try:
                data = np.loadtxt(filename, skiprows=3)
                if data.size == 0:
                    return None
                else:
                    return data
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
                return None

        def compute_sum(colvar_data):
            boltzmann_factor = 1 / ((8.31446261815324 / 1000) * 310)
            metad_acc = np.exp(colvar_data[1:, 3] * boltzmann_factor)         
            dt = np.diff(colvar_data[:, 0])
            total_sum = np.sum(dt * metad_acc)
            return total_sum

        folder_list = sorted(glob.glob('lammps_calculate_rate_constants/**'))
        os.makedirs("lammps_calculate_rate_constants/results", exist_ok=True)

        delete_csv = glob.glob('lammps_calculate_rate_constants/results/*.csv')
        for csv in delete_csv:
            os.remove(csv)

        for folder in folder_list:
            if folder.split('/')[-1] == 'PES':
                continue
            colvar_files_list = sorted(glob.glob(f'{folder}/**/COLVAR'))
            tau_list = []
            name_folder_list = []
            if colvar_files_list:
                try:
                    for colvar_file in colvar_files_list:
                        name_folder_list.append(colvar_file.split('/')[-2])
                        data = read_file(colvar_file)
                        if data is None:
                            continue
                        tau = compute_sum(data) * 1.e-15
                        tau_list.append(tau)

                    folder_name = folder.split('/')[-1]
                    result_file_path = f'lammps_calculate_rate_constants/results/{folder_name}.csv'

                    with open(result_file_path, 'w', newline='') as f1:
                        f1.write("colvar_folder\ttau\n")  # Write header
                        for name_folder, tau in zip(name_folder_list, tau_list):
                            f1.write(f"{name_folder}\t{tau}\n")

                except Exception as e:
                    print(f"Error processing folder {folder}: {e}")
                




    @staticmethod
    def plot_rates():
        rates_file_list = sorted(glob.glob("lammps_calculate_rate_constants/results/*.csv"))

        for rate_file in rates_file_list:
            with open(rate_file, 'r') as f1:
                reader = csv.reader(f1, delimiter='\t')
                next(reader)
                data = np.array([float(row[1]) for row in reader])
            data_sorted = np.sort(data)

            # Estimate the rate parameter (lambda) for Poisson distribution
            mu_poisson = np.mean(data)
            sigma_normal = np.std(data_sorted)

            ks_stat_poisson, p_value_poisson = stats.kstest(data_sorted, 'poisson', args=(mu_poisson,))
            ks_stat_normal, p_value_normal = stats.kstest(data_sorted, 'norm', args=(mu_poisson, sigma_normal))

            # Calculate theoretical CDF for Poisson distribution
            cdf_poisson = stats.poisson.cdf(data_sorted, mu_poisson)
            #cdf_normal = stats.norm.cdf(data_sorted, loc=mu_poisson, scale=sigma_normal)


            # Plot ECDF and theoretical CDF
            plt.step(data_sorted, np.arange(1, len(data_sorted) + 1) / len(data_sorted), label='Empirical CDF')
            plt.plot(data_sorted, cdf_poisson, label=f'Theoretical CDF (Poisson, λ={mu_poisson:.2f})', color='red')
            #plt.plot(data_sorted, cdf_normal, label=f'Theoretical CDF (Normal, μ={mu_poisson:.2f}, σ={sigma_normal:.2f})', color='blue')

            # Add logarithmic scale to x-axis
            plt.xscale('log')

            # Add labels and annotations
            plt.xlabel(r'$\tau$ / s')
            plt.ylabel('CDF')

            # Save the plot
            plt.legend()
            plt.tight_layout()
            plt.savefig(f'{rate_file}_plot.png', dpi=300)
            plt.close()


            print(f"Poisson Distribution: KS Statistic = {ks_stat_poisson:.4f}, p-value = {p_value_poisson:.4f}")
            print(f"Normal Distribution: KS Statistic = {ks_stat_normal:.4f}, p-value = {p_value_normal:.4f}")



    @staticmethod
    def delete():
        print("LammpsCalculateRateConstants delete function")
