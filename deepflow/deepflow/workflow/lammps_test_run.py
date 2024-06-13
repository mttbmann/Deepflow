import os
import glob
import shutil
import json
import re
import subprocess
import dpdata
import subprocess
import csv


class LammpsTestRun:
    @staticmethod
    def setup(steps=10000000,temperature=310):
        folder_number=len(glob.glob(os.path.join("lammps_run","**")))
        os.mkdir(f"lammps_run/{folder_number}")

        files_to_copy=glob.glob("input_files/lammps_run/*")
        active_learning_itterations=sorted(glob.glob("dpgen_active_learning/iter.*"))

        model_file = os.path.join(active_learning_itterations[-1],"00.train","000","frozen_model.pb")
        conf_file = os.path.join(active_learning_itterations[-1],"01.model_devi","confs/","000.0000.lmp")

        files_to_copy.append(model_file)
        files_to_copy.append(conf_file)

        # Copy files to the destination directory
        destination_dir = f"lammps_run/{folder_number}"
        for files in files_to_copy:
            shutil.copy(files, destination_dir)

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

        # Create a list to store atomic weights corresponding to elements
        element_atomic_weights = []
        # Iterate over elements and get their atomic weights
        for element in elements:
            # Check if the element exists in the atomic_weights dictionary
            if element in atomic_weights:
                element_atomic_weights.append(atomic_weights[element])
            else:
                element_atomic_weights.append(None)

        # Read the content of the LAMMPS input file
        with open(f"lammps_run/{folder_number}/input.lammps","r") as f1:
            data = f1.read()

        # Split the content into two parts: before and after the "read_data" line
        before_read_data, after_read_data = data.split("read_data       000.0000.lmp\n")

        # Replace placeholders with actual values in the first part
        before_read_data = before_read_data.replace("{steps}", str(steps))
        before_read_data = before_read_data.replace("{elements}", elements_str)
        before_read_data = before_read_data.replace("{temp}", str(temperature))

        # Write the modified content back to the file
        with open(f"lammps_run/{folder_number}/input.lammps","w") as f:
            f.write(before_read_data)

        # Write atomic masses for each element after the "read_data" line
        with open(f"lammps_run/{folder_number}/input.lammps","a") as f:
            counting_number = 0
            f.write("read_data       000.0000.lmp\n")
            for element in elements:
                f.write(f"mass {(counting_number+1)} {element_atomic_weights[counting_number]}\n")
                counting_number += 1
            f.write(after_read_data)  # Write the second part after the loop

        print(f"Lammps MD run with {steps} Steps at {temperature} K initialized.\n Model taken from:\t {active_learning_itterations[-1]}")

    @staticmethod
    def run(steps=10000000,temperature=310):
        os.system("sbatch lammps.sh")

        print(f"Lammps MD run with submitted.\n")

    @staticmethod
    def clear():
        directory = "lammps_test_run/"
        contents = glob.glob(os.path.join(directory, "*"))
        for item in contents:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)
        print(f"All files in 'lammps_test_run' deleted.")
