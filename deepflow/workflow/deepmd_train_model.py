import os
import glob
import shutil
import json
import re
import subprocess
import csv
import random

def find_potential(file_path, elements):
    # Initialize a dictionary to store the results
    potential_list = []
    basis_set_list = []

    # Open and read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

        # Iterate through each element
        for element in elements:
            # Create the search pattern
            search_pattern = f"{element} GTH-PBE-q"

            # Search for the line that contains the pattern
            for line in lines:
                if search_pattern in line:
                    # Split the line into parts
                    parts = line.split()
                    # Find the part that starts with 'GTH-PBE-q' and store it in the dictionary
                    for part in parts:
                        if part.startswith('GTH-PBE-q'):
                            potential_list.append(part)
                            basis_set_list.append("DZVP-MOLOPT-SR-GTH")
                            break
                    break

    return potential_list, basis_set_list


class DeepMDTrainModel:
    @staticmethod
    def setup():
        # Copy and replace output_for_conv.py to dpdata/cp2k/output.py
        with open('input_files/update_input.json', 'r') as file:
            config_data = json.load(file)
            dpdata_location = os.path.expanduser(config_data["dpdata_conversion_settings"]["dpdata_path"])
            dpdata_output_path = os.path.join(dpdata_location, "cp2k/output.py")
            if os.path.exists(dpdata_output_path):
                shutil.copy("input_files/deepmd_train_model/output_for_dpgen.py", dpdata_output_path)

        sh_file=glob.glob("input_files/deepmd_train_model/*.sh")
        input_file=glob.glob("input_files/deepmd_train_model/*.json")
        env_setup_file=glob.glob("input_files/deepmd_train_model/env_setup")

        # Copy files to the destination directory
        destination_dir = "deepmd_train_model"
        for file_list in [sh_file,input_file,env_setup_file]:
            for file_path in file_list:
                shutil.copy(file_path, destination_dir)
        DeepMDTrainModel.update_json()

    def update_json():
        # Load the CSV file and extract atomic weights
        with open('input_files/utils/iupac_atomic_weights.csv', newline='') as csvfile:
            reader = csv.reader(csvfile)
            # Skip the first line (website source)
            next(reader)
            # Get the column names from the second line (header)
            headers = next(reader)

            # Find the index of the 'AtomicWt' column
            atomic_wt_index = headers.index('AtomicWt')

            # Initialize an empty dictionary to store atomic weights by symbol
            atomic_weights = {}
            for row in reader:
                atomic_weights[row[1]] = float(row[atomic_wt_index].replace(',', ''))

        # Open the file in read mode
        with open('dpgen_data_conversion/training_data/type_map.raw', 'r') as file:
            # Read all lines from the file
            lines = file.readlines()
        # Initialize an empty list to store the extracted elements
        elements = []
        # Iterate over each line
        for line in lines:
            if line.strip() != "~":
                elements.append(line.strip())
        # Join elements with spaces
        elements_str = ' '.join(elements)

        # Create a list to store atomic weights corresponding to elements
        element_atomic_weights = []
        # Iterate over elements and get their atomic weights
        for element in elements:
            # Check if the element exists in the atomic_weights dictionary
            if element in atomic_weights:
                element_atomic_weights.append(atomic_weights[element])
            else:
                element_atomic_weights.append(None)

        with open ('input_files/dpgen_active_learning/input.lammps','r') as f1:
            input_lammps=f1.read()
        number_mass=1
        atomic_masses_str=''
        for atomic_mass in element_atomic_weights:
            atomic_masses_str+=f'mass\t{number_mass}\t{atomic_mass}\n'
            number_mass+=1

        input_lammps = input_lammps.replace('ATOMIC_MASSES_PLACEHOLDER',atomic_masses_str)

        with open('input_files/dpgen_active_learning/input.lammps', 'w') as f1:
            f1.write(input_lammps)


        # Path to your shell script
        cwd=os.getcwd()
        if os.path.exists(os.path.join(cwd,"deepmd_train_model","deepmd_sel.out"))==False:
            script_path = os.path.join(cwd,"deepmd_train_model","env_setup")
            # Command to run the script
            command = f"source {script_path} && cd deepmd_train_model/ && dp neighbor-stat -s ../dpgen_data_conversion/training_data -r 5.0 -t {elements_str}"
            # Execute the command using subprocess
            with open("deepmd_train_model/deepmd_sel.out", "w") as f1:
                result = subprocess.run(command, shell=True, executable='/bin/bash', stdout=f1, stderr=subprocess.STDOUT)


        # Read the input.json file
        with open('input_files/deepmd_train_model/input.json', 'r') as json_file:
            data = json.load(json_file)
        data["model"]["type_map"] = elements
        cwd=os.getcwd()
        training_data_tmp=os.path.join(cwd,"dpgen_data_conversion","training_data")
        training_data = [training_data_tmp]
        data["training"]["training_data"]["systems"] = training_data
        data["training"]["seed"] = random.randint(0,10000000)
        data["model"]["descriptor"]["seed"] = random.randint(0,10000000)
        data["model"]["fitting_net"]["seed"] = random.randint(0,10000000)
        # Write the updated data back to input.json
        with open('deepmd_train_model/input.json', 'w') as json_file:
            json.dump(data, json_file, indent=4)

        if os.path.exists("deepmd_train_model/deepmd_sel.out"):
            # Read the file and find the line containing "max_nbor_size"
            with open("deepmd_train_model/deepmd_sel.out", "r") as f:
                lines = f.readlines()
                for line in lines:
                    if "max_nbor_size" in line:
                        # Extract numbers from the line using regular expressions
                        numbers = re.findall(r'\d+', line)
                        # Convert the extracted numbers to integers
                        numbers = [int(num) for num in numbers]
                        numbers = [int(1.3*num+2) for num in numbers]
                        break


            # Load the existing JSON file
            with open("deepmd_train_model/input.json", "r") as json_file:
                existing_data = json.load(json_file)
            # Replace the existing 'sel' key with the extracted numbers
            existing_data["model"]["descriptor"]["sel"] = numbers
            # Write the modified JSON back to the file
            with open("deepmd_train_model/input.json", "w") as json_file:
                json.dump(existing_data, json_file, indent=4)

            # Read the param.json file
            with open('input_files/dpgen_active_learning/param.json', 'r') as json_file:
                data_2 = json.load(json_file)
            # Get current working directory
            work_dir = os.getcwd()
            # Define paths
            dpgen_active_learning_path_lmp = os.path.join(work_dir, "dpgen_active_learning", "1.lmp")
            dpgen_data_conversion_path = os.path.join(work_dir, "dpgen_data_conversion")
            lammps_input_geometry = [[str(dpgen_active_learning_path_lmp)]] # No need for f-string here
            data_2["type_map"] = elements
            data_2["mass_map"] = element_atomic_weights
            data_2["init_data_prefix"] = str(dpgen_data_conversion_path)
            data_2["sys_configs"] = lammps_input_geometry
            data_2["default_training_param"]["model"]["descriptor"]["sel"] = numbers
            potentials,basis_set = find_potential("input_files/utils/POTENTIAL",elements)
            data_2["user_fp_params"]["FORCE_EVAL"]["SUBSYS"]["KIND"]["_"] = elements
            data_2["user_fp_params"]["FORCE_EVAL"]["SUBSYS"]["KIND"]["BASIS_SET"] = basis_set
            data_2["user_fp_params"]["FORCE_EVAL"]["SUBSYS"]["KIND"]["POTENTIAL"] = potentials

            # Write the updated data back to param.json
            with open('dpgen_active_learning/param.json', 'w') as json_file:
                json.dump(data_2, json_file, indent=4)

        else:
            pass

        # Read the machine.json file
        with open('input_files/dpgen_active_learning/machine.json', 'r') as json_file:
            data_3 = json.load(json_file)
        # Get current working directory
        work_dir = os.getcwd()
        # Define paths
        dpgen_active_learning_path = os.path.join(work_dir, "dpgen_active_learning")
        data_3["train"][0]["machine"]["remote_root"] = dpgen_active_learning_path
        data_3["model_devi"][0]["machine"]["remote_root"] = dpgen_active_learning_path
        data_3["fp"][0]["machine"]["remote_root"] = dpgen_active_learning_path
        # Write the updated data back to machine.json
        with open('dpgen_active_learning/machine.json', 'w') as json_file:
            json.dump(data_3, json_file, indent=4)

        with open("input_files/deepmd_train_model/deepmd_get_sel.sh", "r") as f1:
            sh_file = f1.read()
        sh_file = sh_file.replace("{type_map}", elements_str)
        with open("input_files/deepmd_train_model/deepmd_get_sel.sh", "w") as f2:
            f2.write(sh_file)


    @staticmethod
    def run(number_models=4):
        DeepMDTrainModel.update_json()

        try:
            work_dir=os.getcwd()

            os.chdir('deepmd_train_model/')

            for num_mod in range(0, number_models):
                os.mkdir(str(num_mod))
                shutil.copy('deepmd_train_model.sh', f"{num_mod}/deepmd_train_model.sh")
                shutil.copy('input.json', f"{num_mod}/input.json")
                os.chdir(str(num_mod))
                slurm_batch = glob.glob('deepmd_train_model.sh')[0]  # Assuming only one file
                os.system(f'sbatch {slurm_batch}')
                os.chdir("..")
            with open("JOB_SUBMITTED",'w') as f1:
                f1.write("JOB_SUBMITTED")

            os.chdir(work_dir)
        except Exception as e:
            print(f"An error occurred while running the DeepMD Train Model: {e}")

    @staticmethod
    def clear():
        directory = "deepmd_train_model/"
        contents = glob.glob(os.path.join(directory, "*"))
        for item in contents:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)





