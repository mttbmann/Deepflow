import os
import shutil
import glob
import fnmatch
import json

class DpGenDataConversion:
    @staticmethod
    def setup():
        # Copy and replace output_for_conv.py to dpdata/cp2k/output.py
        with open('input_files/update_input.json', 'r') as file:
            config_data = json.load(file)
            dpdata_location = os.path.expanduser(config_data["dpdata_conversion_settings"]["dpdata_path"])
            dpdata_output_path = os.path.join(dpdata_location, "cp2k/output.py")
            if os.path.exists(dpdata_output_path):
                shutil.copy("input_files/dpgen_data_conversion/output_for_conv.py", dpdata_output_path)

        os.makedirs("dpgen_data_conversion/data", exist_ok=True)


        cp2k_out_tmp = glob.glob("cp2k_production/nvt.out")
        cp2k_out = [file for file in cp2k_out_tmp if not (file.endswith('PLUMED.out') or fnmatch.fnmatch(file, 'P*.out'))]
        cp2k_inp = glob.glob("cp2k_production/*.inp")
        cp2k_forces = glob.glob("cp2k_production/*frc-1.xyz")
        cp2k_xyz = glob.glob("cp2k_production/*pos-1.xyz")
        cp2k_ener = glob.glob("cp2k_production/*.ener")

        pickdata = glob.glob("input_files/dpgen_data_conversion/pickdata.py")
        sh_file = glob.glob("input_files/dpgen_data_conversion/*.sh")

        # Destination directory
        destination_dir = "dpgen_data_conversion/data"
        destination_dir_2 = "dpgen_data_conversion"

        # Copy files to the destination directory
        for file_list in [cp2k_inp, cp2k_forces, cp2k_xyz, cp2k_ener]:
            for file_path in file_list:
                shutil.copy(file_path, destination_dir)

        # Copy files to the destination directory
        for file_list in [pickdata, sh_file]:
            for file_path in file_list:
                shutil.copy(file_path, destination_dir_2)

        # Copy cp2k.out files and rename them to .log
        for cp2k_out_file in cp2k_out:
            # Generate new file name with .log extension
            new_file_name = os.path.join(destination_dir, os.path.basename(cp2k_out_file).replace(".out", ".log"))
            # Copy and rename
            shutil.copy(cp2k_out_file, new_file_name)



    @staticmethod
    def run():
        try:
            work_dir=os.getcwd()
            os.chdir('dpgen_data_conversion/')
            slurm_batch=glob.glob('*.sh')
            os.system(f'sbatch {slurm_batch[0]}')
            with open("JOB_SUBMITTED",'w') as f1:
                f1.write("JOB_SUBMITTED")
            os.chdir(work_dir)
        except Exception as e:
            print(f"An error occurred while running the DPGen Data Conversion: {e}")


    @staticmethod
    def clear():
        directory = "dpgen_data_conversion/"
        contents = glob.glob(os.path.join(directory, "*"))
        for item in contents:
            if os.path.isfile(item):
                os.remove(item)
            elif os.path.isdir(item):
                shutil.rmtree(item)

