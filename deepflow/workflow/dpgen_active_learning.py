from .deepmd_train_model import DeepMDTrainModel
import os
import glob
import shutil
import json
import re
import dpdata
import subprocess
import csv

class DpGenActiveLearning:
    @staticmethod
    def setup():
        # Copy and replace output_for_conv.py to dpdata/cp2k/output.py
        with open('input_files/update_input.json', 'r') as file:
            config_data = json.load(file)
            dpdata_location = os.path.expanduser(config_data["dpdata_conversion_settings"]["dpdata_path"])
            dpdata_output_path = os.path.join(dpdata_location, "cp2k/output.py")
            if os.path.exists(dpdata_output_path):
                shutil.copy("input_files/deepmd_train_model/output_for_dpgen.py", dpdata_output_path)

        DeepMDTrainModel.update_json()

        input_files=["input_files/dpgen_active_learning/plumed.dat","input_files/dpgen_active_learning/input.lammps","input_files/dpgen_active_learning/env_setup"]
        # Copy files to the destination directory
        destination_dir = "dpgen_active_learning"
        for file_path in input_files:
            shutil.copy(file_path, destination_dir)

        dsys = dpdata.LabeledSystem("dpgen_data_conversion/training_data",fmt='deepmd/npy')
        dsys.to("lammps/lmp", "dpgen_active_learning/1.lmp", frame_idx=0)

        # Get a list of all .pb files with their relative paths
        deepmd_models = glob.glob("deepmd_train_model/**/")

        # Convert relative paths to absolute paths
        deepmd_models_full_paths = [os.path.abspath(path) for path in deepmd_models]

        with open('dpgen_active_learning/param.json', 'r') as json_file:
            data_2 = json.load(json_file)

        data_2["training_iter0_model_path"] = deepmd_models_full_paths

        with open('dpgen_active_learning/param.json', 'w') as json_file:
            json.dump(data_2, json_file, indent=4)





    @staticmethod
    def run(dpdata_location = os.path.expanduser("~/.local/lib/python3.10/site-packages/dpdata")):
        # Copy and replace output_for_conv.py to dpdata/cp2k/output.py
        dpdata_output_path = os.path.join(dpdata_location, "cp2k/output.py")
        if os.path.exists(dpdata_output_path):
            shutil.copy("input_files/deepmd_train_model/output_for_dpgen.py", dpdata_output_path)
        # Path to your shell script
        cwd=os.getcwd()
        script_path = os.path.join(cwd,"dpgen_active_learning","env_setup")
        # Command to run the script
        command = f"source {script_path} && cd dpgen_active_learning/ && dpgen run param.json machine.json"

        # Execute the command using subprocess
        result = subprocess.run(command, shell=True, executable='/bin/bash')

    @staticmethod
    def clear():
        directory = "dpgen_active_learning/"
        contents = glob.glob(os.path.join(directory, "*"))
        for item in contents:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)
        print(f"All files in 'dpgen_active_learning' deleted.")


