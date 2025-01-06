import sys
import os
import code
import argparse
import shutil
import json
import glob
import time
import pkg_resources

from deepflow.workflow.cp2k_equilibration import Cp2kEquilibration
from deepflow.workflow.cp2k_production import Cp2kProduction
from deepflow.workflow.dpgen_data_conversion import DpGenDataConversion
from deepflow.workflow.dpgen_active_learning import DpGenActiveLearning
from deepflow.workflow.lammps_test_run import LammpsTestRun
from deepflow.workflow.lammps_calculate_rate_constants import LammpsCalculateRateConstants
from deepflow.workflow.deepmd_train_model import DeepMDTrainModel
from deepflow.workflow.util import UtilizationTools
from deepflow.workflow.fes import FreeEnergySurface

def update_input_files(input_json="update_input.json"):
    # Step 1: Read the JSON file
    with open('input_files/update_input.json', 'r') as file:
        config_data = json.load(file)
    # Extracted Data
    general_settings = config_data['general_settings']
    cp2k_settings = config_data['cp2k_settings']
    dpdata_conversion_settings = config_data['dpdata_conversion_settings']
    deepmd_settings = config_data['deepmd_settings']
    active_learning_settings = config_data['active_learning_settings']

    #copy plumed_file
    plumed_dat = general_settings["plumed_dat_path"]
    try:
        shutil.copyfile(plumed_dat,"input_files/cp2k_production/plumed.dat")
        shutil.copyfile(plumed_dat,"input_files/dpgen_active_learning/plumed.dat")
        shutil.copyfile(plumed_dat,"input_files/lammps_run/plumed.dat")
    except:
        pass
    # Define file paths
    file_paths = [
        "input_files/cp2k_equilibration/cp2k_er.inp",
        "input_files/cp2k_equilibration/cp2k_slurm.sh",
        "input_files/dpgen_data_conversion/convert.sh",
        "input_files/deepmd_train_model/deepmd_train_model.sh",
        "input_files/deepmd_train_model/env_setup",
        "input_files/deepmd_train_model/deepmd_get_sel.sh",
        "input_files/deepmd_train_model/input.json",
        "input_files/dpgen_active_learning/machine.json",
        "input_files/dpgen_active_learning/param.json",
        "input_files/dpgen_active_learning/env_setup"
    ]

    # Define replacements for each file
    replacements = {
        "input_files/cp2k_equilibration/cp2k_er.inp": {
            "EQUILIBRATION_STEPS_PLACEHOLDER": cp2k_settings['equilibration_steps'],
            "LATTICE_CONSTANTS_PLACEHOLDER": f"{general_settings['lattice_constants'][0]} {general_settings['lattice_constants'][1]} {general_settings['lattice_constants'][2]}",
            "LATTICE_ANGLES_PLACEHOLDER": f"{general_settings['lattice_angles'][0]} {general_settings['lattice_angles'][1]} {general_settings['lattice_angles'][2]}",
            "TEMPERATURE_PLACEHOLDER": cp2k_settings['temperature']
        },
        "input_files/cp2k_equilibration/cp2k_slurm.sh": {
            "CPU_CORES_PLACEHOLDER": cp2k_settings['cpu_cores'],
            "PROJECT_CPU_PLACEHOLDER": general_settings['project_cpu']
        },
        "input_files/dpgen_data_conversion/convert.sh": {
            "PROJECT_CPU_PLACEHOLDER": general_settings['project_cpu']
        },
        "input_files/deepmd_train_model/deepmd_train_model.sh": {
            "PROJECT_GPU_PLACEHOLDER": general_settings['project_gpu'],
            "DEEP_MD_CONDA_PATH_PLACEHOLDER": deepmd_settings['deepmd_conda_path']
        },
        "input_files/deepmd_train_model/env_setup": {
            "DEEP_MD_CONDA_PATH_PLACEHOLDER": deepmd_settings['deepmd_conda_path'],
            "MINICONDA_PATH_PLACEHOLDER_1": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_2": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_3": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_3": general_settings['miniconda_path']
        },
        "input_files/deepmd_train_model/deepmd_get_sel.sh": {
            "PROJECT_CPU_PLACEHOLDER": general_settings['project_cpu'],
            "DEEP_MD_CONDA_PATH_PLACEHOLDER": deepmd_settings['deepmd_conda_path'],
            "R_CUT_PLACEHOLDER": active_learning_settings['r_cut']
        },
        "input_files/deepmd_train_model/input.json": {
            "R_CUT_PLACEHOLDER": active_learning_settings['r_cut'],
            "STEPS_INIT_PLACEHOLDER": deepmd_settings['steps_init']
        },
        "input_files/dpgen_active_learning/machine.json": {
            "HOSTNAME_PLACEHOLDER_1": active_learning_settings['remote_profile']['hostname'],
            "USERNAME_PLACEHOLDER_1": active_learning_settings['remote_profile']['username'],
            "PASSWORD_PLACEHOLDER_1": active_learning_settings['remote_profile']['password'],
            "KEY_FILENAME_PLACEHOLDER_1": active_learning_settings['remote_profile']['key_filename'],
            "PASSPHRASE_PLACEHOLDER_1": active_learning_settings['remote_profile']['passphrase'],
            "HOSTNAME_PLACEHOLDER_2": active_learning_settings['remote_profile']['hostname'],
            "USERNAME_PLACEHOLDER_2": active_learning_settings['remote_profile']['username'],
            "PASSWORD_PLACEHOLDER_2": active_learning_settings['remote_profile']['password'],
            "KEY_FILENAME_PLACEHOLDER_2": active_learning_settings['remote_profile']['key_filename'],
            "PASSPHRASE_PLACEHOLDER_2": active_learning_settings['remote_profile']['passphrase'],
            "HOSTNAME_PLACEHOLDER_3": active_learning_settings['remote_profile']['hostname'],
            "USERNAME_PLACEHOLDER_3": active_learning_settings['remote_profile']['username'],
            "PASSWORD_PLACEHOLDER_3": active_learning_settings['remote_profile']['password'],
            "KEY_FILENAME_PLACEHOLDER_3": active_learning_settings['remote_profile']['key_filename'],
            "PASSPHRASE_PLACEHOLDER_3": active_learning_settings['remote_profile']['passphrase'],
            "PROJECT_GPU_PLACEHOLDER_1": general_settings['project_gpu'],
            "PROJECT_GPU_PLACEHOLDER_2": general_settings['project_gpu'],
            "PROJECT_CPU_PLACEHOLDER": general_settings['project_cpu'],
            "DEEP_MD_CONDA_PATH_PLACEHOLDER_1": deepmd_settings['deepmd_conda_path']
        },
        "input_files/dpgen_active_learning/param.json": {
            "R_CUT_PLACEHOLDER": active_learning_settings['r_cut'],
            "STEPS_REUSE_PLACEHOLDER": deepmd_settings['steps_reuse'],
            "STEPS_INIT_PLACEHOLDER": deepmd_settings['steps_init'],
            "LATTICE_CONSTANTS_PLACEHOLDER": f"{general_settings['lattice_constants'][0]} {general_settings['lattice_constants'][1]} {general_settings['lattice_constants'][2]}",
            "LATTICE_ANGLES_PLACEHOLDER": f"{general_settings['lattice_angles'][0]} {general_settings['lattice_angles'][1]} {general_settings['lattice_angles'][2]}"
        },
        "input_files/dpgen_active_learning/env_setup": {
            "DEEP_MD_CONDA_PATH_PLACEHOLDER": deepmd_settings['deepmd_conda_path'],
            "MINICONDA_PATH_PLACEHOLDER_1": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_2": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_3": general_settings['miniconda_path'],
            "MINICONDA_PATH_PLACEHOLDER_3": general_settings['miniconda_path']
        }
    }

    # Read, replace and write back files
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            content = file.read()

        for placeholder, replacement in replacements.get(file_path, {}).items():
            content = content.replace(placeholder, str(replacement))

        with open(file_path, 'w') as file:
            file.write(content)





def run_workflow(project_path):
    os.chdir(project_path)
    update_input_files()
    while True:
        status = check_status_project()
        print(status)

        if status["equilibration"] == "STEP NOT STARTED":
            Cp2kEquilibration.clear()
            Cp2kEquilibration.setup()
            Cp2kEquilibration.run()

        if status["equilibration"] == "STEP COMPLETED" and status["production"] == "STEP NOT STARTED":
            Cp2kProduction.clear()
            Cp2kProduction.setup()
            Cp2kProduction.run()

        if status["production"] == "STEP COMPLETED" and status["data_conversion"] == "STEP NOT STARTED":
            DpGenDataConversion.clear()
            DpGenDataConversion.setup()
            DpGenDataConversion.run()

        if status["data_conversion"] == "STEP COMPLETED" and status["training"] == "STEP NOT STARTED":
            DeepMDTrainModel.clear()
            DeepMDTrainModel.setup()
            DeepMDTrainModel.run()

        if status["training"] == "STEP COMPLETED":
            DpGenActiveLearning.setup()
            print("Workflow and active learning setup completed.")
            break
        # Add sleep to avoid continuous tight loop and give some time for steps to update status
        time.sleep(60)  # Check every 60 seconds, adjust as needed

def load_project(project_path):
    # Logic to load the project based on the project path
    if os.path.exists(project_path):
        print(f'Project successfully loaded: {project_path}\n')
        return True
    else:
        print(f"Project path not found: {project_path}")
        return False

def create_project(project_path, structure):
    # Logic to create a new project
    if os.path.exists(structure):

        file_format = os.path.splitext(structure)[-1].lower()
        if file_format == '.pdb' or file_format == '.xyz':

            if not os.path.exists(project_path):
                print(f"Creating new project: {project_path}\n")
                print(f"Molecule Geometry: {structure}\n")
                os.mkdir(project_path)
                for subdir in ["cp2k_equilibration", "cp2k_production", "dpgen_data_conversion",
                               "dpgen_active_learning", "lammps_test_run", "lammps_calculate_rate_constants","deepmd_train_model","fes"]:
                    os.mkdir(os.path.join(project_path, subdir))
                input_files_src = pkg_resources.resource_filename('deepflow', 'input_files')
                shutil.copytree(input_files_src, os.path.join(project_path, 'input_files'))
                shutil.copyfile(pkg_resources.resource_filename('deepflow', 'input_files/update_input.json'), os.path.join(project_path, 'input_files/update_input.json'))


                xyz_name_tmp=structure.split('/')
                xyz_name=xyz_name_tmp[-1]
                xyz_dest=os.path.join(project_path,"input_files","cp2k_equilibration",xyz_name)

                shutil.copyfile(structure,xyz_dest)
                os.chdir(project_path)
                update_input_files()
                load_project_status = True
            else:
                print(f"Project already exists: {project_path}")

        else:
            print('Please provide a Molecule Geometry in either .xyz or .pdb format')
    else:
        print('File not found. Please provide a valid path to a Molecule Geometry in either xyz or pdb format')

def check_status_project():
    # Load files for each step
    equil_out = glob.glob("cp2k_equilibration/*.out")
    equil_file = ["cp2k_equilibration/JOB_SUBMITTED"]

    prod_out = glob.glob("cp2k_production/*.out")
    prod_file = ["cp2k_production/JOB_SUBMITTED"]

    data_conv_file = ["dpgen_data_conversion/JOB_SUBMITTED"]
    data_conv_folders = ["dpgen_data_conversion/training_data",
                         "dpgen_data_conversion/testing_data",
                         "dpgen_data_conversion/validation_data"]


    train_out = glob.glob("deepmd_train_model/**/output.*.txt")
    train_file = ["deepmd_train_model/JOB_SUBMITTED"]

    def search_in_files(files, search_string,job_sub):
        if not files:
            if not os.path.exists(job_sub):
                return "STEP NOT STARTED"
            else:
                return "STEP PENDING OR INTERRUPTED"
        for file in files:
            with open(file, 'r') as f:
                if search_string in f.read():
                    return "STEP COMPLETED"

        return "STEP PENDING OR INTERRUPTED"


    def check_data_conversion():
        # Check if the specific file exists
        if not any(os.path.exists(file) for file in data_conv_file):
            return "STEP NOT STARTED"

        # Check if all required folders exist
        if all(os.path.exists(folder) for folder in data_conv_folders):
            return "STEP COMPLETED"
        else:
            return "STEP PENDING OR INTERRUPTED"

    # Check the status of each step
    status = {
        "equilibration": search_in_files(equil_out, "PROGRAM ENDED AT",equil_file[0]),
        "production": search_in_files(prod_out, "PROGRAM ENDED AT",prod_file[0]),
        "data_conversion": check_data_conversion(),
        "training": search_in_files(train_out, "DEEPMD INFO    finished training",train_file[0])
    }

    return status

def main():
    workflow_classes_desc = """
Usage:

  deepflow new <project_path> <xyz_pdb_structure>
    Creates a new project at the specified path with a XYZ or PDB file as the input structure.

  deepflow run <project_path>
    Runs the workflow including equilibration MD, production MD, data conversion, and training of 4 initial models to set up active learning.

  deepflow load <project_path>
    Loads a project into a Python environment.

    Available Commands After Loading a Project:

      equil           : Cp2kEquilibration
                         - setup()   : Set up the equilibration step
                         - run()     : Execute the equilibration step
                         - clear()   : Clear the equilibration step data

      prod            : Cp2kProduction
                         - setup()   : Set up the production MD step
                         - run()     : Execute the production MD step
                         - clear()   : Clear the production MD step data

      dataconv        : DpGenDataConversion
                         - setup()   : Set up the data conversion step
                         - run()     : Execute the data conversion step
                         - clear()   : Clear the data conversion step data

      activelearning  : DpGenActiveLearning
                         - setup()   : Set up the active learning step
                         - run()     : Execute the active learning step
                         - clear()   : Clear the active learning step data

      lammps          : LammpsTestRun
                         - setup()   : Set up the LAMMPS test run step with the deep potential of the latest active learning iteration.
                         - run()     : Execute the LAMMPS test run step
                         - clear()   : Clear the LAMMPS test run step data

      rateconstants   : LammpsCalculateRateConstants
                         - setup()   : Set up the rate constants calculation step
                         - run()     : Execute the rate constants calculation step
                         - clear()   : Clear the rate constants calculation step data

      train           : DeepMDTrainModel
                         - setup()   : Set up the DeepMD training step
                         - run()     : Execute the DeepMD training step
                         - clear()   : Clear the DeepMD training step data

      util            : UtilizationTools
                         - avg_bond_length() : Calculate the average bond length
                         - plot()            : Plot COLVAR file, max_devi_force and average_bond_length of each active learning iteration.
    """
    parser = argparse.ArgumentParser(description="Deepflow",epilog=workflow_classes_desc, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('command', choices=['load', 'new','run'])
    parser.add_argument('project_path')
    parser.add_argument('structure',nargs='?')
    args = parser.parse_args()

    if args.command == 'load':
        load_project(args.project_path)
        start_python_repl(args.project_path)

    elif args.command == 'new':
        if args.structure:
            create_project(args.project_path, args.structure)
        else:
            print("Please provide a molecule geometry file for new projects.")
    elif args.command == 'run':
        run_workflow(args.project_path)

def start_python_repl(project_path):
    # Start the Python REPL within the project directory
    os.chdir(project_path)
    workflow_classes = {
        "equil": Cp2kEquilibration,
        "prod": Cp2kProduction,
        "dataconv": DpGenDataConversion,
        "activelearning": DpGenActiveLearning,
        "lammps": LammpsTestRun,
        "rateconstants": LammpsCalculateRateConstants,
        "train": DeepMDTrainModel,
        "util": UtilizationTools,
        "fes": FreeEnergySurface
    }
    #print(check_status_project())
    # Import the classes dynamically based on workflow step
    locals().update(workflow_classes)

    # Instantiate the workflow classes
    instantiated_classes = {step: cls() for step, cls in workflow_classes.items()}


    # Start the Python REPL with access to local variables
    code.interact(local=locals())




if __name__ == "__main__":
    main()
