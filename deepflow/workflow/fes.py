import glob
import os
import shutil
import re
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

class FreeEnergySurface:
    @staticmethod
    def run():
        colvar_list = sorted(glob.glob('lammps_test_run/**/task.000.000000'))
        current_wd = os.getcwd()
        

        for colvar in colvar_list:
            path_colvar = os.path.dirname(colvar)
            folder_name_colvar = os.path.basename(path_colvar)

            os.makedirs(f'fes/{folder_name_colvar}',exist_ok=True)
            shutil.copyfile('input_files/fes/reweighting.py',f'fes/{folder_name_colvar}/reweighting.py')
            shutil.copyfile('input_files/fes/reweighting.sh',f'fes/{folder_name_colvar}/reweighting.sh')
            shutil.copyfile(f'{colvar}/COLVAR',f'fes/{folder_name_colvar}/COLVAR')
            with open(f'lammps_test_run/{folder_name_colvar}/task.000.000000/input.lammps') as f1:
                lines = f1.readlines()
            
            temperature = None

            
            for line in lines:
                if 'variable' in line and 'TEMP' in line:
                    # Split the line and extract the last element which should be the temperature
                    temperature = line.split()[-1]
                    break   
            
            search_string = "python3 reweighting.py"

            replacement_line = f"python3 reweighting.py --colvar COLVAR --sigma 0.025 --temp {temperature} --cv t --bias metad.rbias --stride 1000 --deltaFat 0.0 --skiprows 20000"
            with open(f"fes/{folder_name_colvar}/reweighting.sh") as f1:
                lines = f1.readlines()
            with open(f"fes/{folder_name_colvar}/reweighting.sh", 'w') as f1:
                for line in lines:
                    if line.startswith(search_string):
                        f1.write(replacement_line)
                    else:
                        f1.write(line)



            os.chdir(f'fes/{folder_name_colvar}')
            os.system('sbatch reweighting.sh')
            os.chdir(current_wd)
    
    @staticmethod
    def extract_data(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        # Extract DeltaF
        delta_f = None
        for line in lines:
            if line.startswith('#! SET DeltaF'):
                delta_f = float(line.split()[-1])
                break
        
        # Extract data for plotting
        data_start_index = next(i for i, line in enumerate(lines) if not line.startswith('#!'))
        data = pd.read_csv(file_path, delim_whitespace=True, comment='#', header=None, skiprows=data_start_index)
        return data, delta_f

    @staticmethod
    def plot_every_30th_file(file_list):
        plt.figure(figsize=(10, 6))
        for i, file in enumerate(file_list[49:], start=50):  # Start from the 10th file and adjust the index
            if (i - 50) % 30 == 0:  # Adjust the index check to match every 30th file after skipping the first 9
                data, _ = FreeEnergySurface.extract_data(file)
                plt.plot(data[0], data[1],alpha=0.5,zorder=1)
                plt.scatter(data[0], data[1], label=f'fes-rew_{i}',marker='x',s=3,zorder=2)

        data, _ = FreeEnergySurface.extract_data(file_list[-1])
        plt.plot(data[0], data[1],alpha=0.5,zorder=1)
        plt.scatter(data[0], data[1], label=f'fes-rew_last',marker='x',s=3,zorder=2)
        
        plt.xlabel('t')
        plt.ylabel('F')
        plt.legend()
        plt.savefig('fes_30.png', dpi=300)
        plt.close()

    @staticmethod
    def plot_delta_f_values(file_list):
        delta_f_values = []
        for i, file in enumerate(file_list):
            _, delta_f = FreeEnergySurface.extract_data(file)
            delta_f_values.append(delta_f)
        
        plt.figure(figsize=(10, 6))
        plt.scatter(range(len(delta_f_values)), delta_f_values, marker='o',s=3)
        plt.xlabel('fes-rew.dat file number')
        plt.ylabel('DeltaF')
        plt.title('DeltaF Values')
        plt.savefig('deltaF.png', dpi=300)
        plt.close()

    @staticmethod
    def plot():
        # Get the current working directory
        current_wd = Path.cwd()
        
        # Find all directories under 'fes'
        directories = [d for d in Path('fes').rglob('*') if d.is_dir()]

        # Function to extract number from filenames
        def extract_number(filename):
            match = re.search(r'_(\d+)\.dat$', filename.name)
            return int(match.group(1)) if match else 0

        for directory in directories:
            # Change to the directory
            os.chdir(directory)

            # Find all files matching 'fes_rew_*.dat'
            fes_rew_files = sorted(Path('.').glob('fes-rew_*.dat'), key=extract_number)
            
            # Ensure there are files to process
            if fes_rew_files:
                FreeEnergySurface.plot_every_30th_file(fes_rew_files)
                FreeEnergySurface.plot_delta_f_values(fes_rew_files)
            
            # Change back to the original working directory
            os.chdir(current_wd)
