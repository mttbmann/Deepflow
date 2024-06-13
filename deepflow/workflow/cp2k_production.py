import glob
import os
import shutil
import json

class Cp2kProduction:
    @staticmethod
    def setup(template_dir="cp2k_production"):
        #extract last geometry from equilibrium run

        equilibrium_traj=glob.glob("cp2k_equilibration/*-pos-1.xyz")
        if not equilibrium_traj:
            equilibrium_traj=glob.glob("cp2k_equilibration/*-pos-1.pdb")
            Cp2kProduction.extract_last_geometry(equilibrium_traj[0],"cp2k_production/nvt_pr_inp.pdb")
        else:
            Cp2kProduction.extract_last_geometry(equilibrium_traj[0],"cp2k_production/nvt_pr_inp.xyz")
        if not equilibrium_traj:
            return print("No finished equilibrium run found.")

        #copy cp2k input file from equilibrium running
        cp2k_eq_inp=glob.glob("cp2k_equilibration/*.inp")
        shutil.copy(cp2k_eq_inp[0],"cp2k_production/cp2k_pr.inp")
        #copy submission script from equilibrium running
        cp2k_eq_inp=glob.glob("cp2k_equilibration/*.sh")
        shutil.copy(cp2k_eq_inp[0],"cp2k_production/cp2k_slurm.sh")

        #copy plumed.dat to running directory
        plumed_inp=glob.glob("input_files/cp2k_production/*.dat")
        shutil.copy(plumed_inp[0],"cp2k_production/plumed.dat")

        input_file_extensions = ['.inp', '.sh']

        for ext in input_file_extensions:
            # List all files with the specified extension in the template directory
            template_files = [file for file in os.listdir(template_dir) if file.endswith(ext)]

            # Iterate over each template file
            for template_file in template_files:
                template_path = os.path.join(template_dir, template_file)
                if os.path.isfile(template_path):

                    with open(template_path, 'r') as f:
                        template_content = f.read()


                    # Modify variables marked with {}
                    modified_content = template_content
                    if ext == '.inp':

                        modified_content = Cp2kProduction.replace_specific_variables_inp(
                            modified_content)

                    if ext == '.sh':
                        modified_content = Cp2kProduction.replace_specific_variables_sh(modified_content)

                    # Save modified template file
                    with open(f"cp2k_production/{template_file}", 'w') as f:
                        f.write(modified_content)


    def replace_specific_variables_inp(content):
        # Replace specific variables in .inp file content
        work_dir = os.getcwd()
        work_folder_tmp = work_dir.split('/')
        work_folder = work_folder_tmp[-1]

        input_xyz = glob.glob("cp2k_production/*.xyz")
        input_pdb = glob.glob("cp2k_production/*.pdb")

        # Split the content into lines
        lines = content.split('\n')
        replaced_lines = []
        delete_next_line = False

        for line in lines:
            if delete_next_line:
                delete_next_line = False
                continue

            if line.startswith("  PROJECT"):
                line=f"  PROJECT {work_folder}_pr"

            if input_xyz:
                xyz_file_name=input_xyz[0].split('/')
                if line.startswith("      COORD_FILE_NAME"):
                    line = f"      COORD_FILE_NAME {xyz_file_name[-1]}"
                elif line.startswith("      COORDINATE"):
                    line = f"      COORDINATE XYZ"


            if input_pdb:
                pdb_file_name=input_pdb[0].split('/')
                if line.startswith("      COORD_FILE_NAME"):
                    line = f"      COORD_FILE_NAME {pdb_file_name[-1]}"
                elif line.startswith("      COORDINATE"):
                    line = f"      COORDINATE PDB"
            with open('input_files/update_input.json', 'r') as file:
                config_data = json.load(file)
                steps_prod = config_data['cp2k_settings']['production_steps']
            if line.startswith("    STEPS"):
                line = f"    STEPS    {steps_prod}"

            if line.startswith("  &END MD"):
                line = f"  &END MD\n  &FREE_ENERGY\n    &METADYN\n       USE_PLUMED .TRUE.\n       PLUMED_INPUT_FILE ./plumed.dat\n    &END METADYN\n  &END FREE_ENERGY"

            if line.startswith("    &TRAJECTORY"):

                line = f"    &TRAJECTORY\n      FORMAT XYZ"
                delete_next_line = True


            replaced_lines.append(line)

        # Join the lines back into a single string
        content = '\n'.join(replaced_lines)

        return content

    def replace_specific_variables_sh(content):
        work_dir = os.getcwd()
        work_folder_tmp = work_dir.split('/')
        work_folder = work_folder_tmp[-1]
        inp_file=glob.glob("cp2k_production/*.inp")
        inp_file_tmp=inp_file[0].split('/')
        inp_file=inp_file_tmp[-1]

        # Split the content into lines
        lines = content.split('\n')
        replaced_lines = []

        for line in lines:
            if line.startswith("$MPIEXEC $FLAGS_MPI_BATCH cp2k.popt"):
                # Replace the entire line with a specific string
                line = f"$MPIEXEC $FLAGS_MPI_BATCH cp2k.popt {inp_file} > nvt.out"
            if line.startswith("#SBATCH --job-name"):
                # Replace the entire line with another specific string
                line = f"#SBATCH --job-name={work_folder}_pr"
            if line.startswith("#SBATCH --time"):
                line = f"#SBATCH --time=120:00:00"
            # Append the line to the list of replaced lines
            replaced_lines.append(line)

        # Join the lines back into a single string
        content = '\n'.join(replaced_lines)

        return content

    @staticmethod
    def extract_last_geometry(input_file, output_file):
        with open(input_file, 'r') as f:
            pdb_xyz_file = f.readlines()

        if input_file.endswith('.xyz'):
            lines=[]
            # Find the line with the number of atoms
            for line in reversed(pdb_xyz_file):
                lines.append(line)
                if line.strip().isdigit():
                    break


        elif input_file.endswith('.pdb'):
            lines=[]
            # Find the line with the number of atoms
            for line in reversed(pdb_xyz_file):
                lines.append(line)
                if line.startswith('REMARK'):
                    break


        with open(output_file, 'w') as f:
            for i in reversed(lines):
                f.write(i)

    @staticmethod
    def run():
        try:
            work_dir=os.getcwd()
            os.chdir('cp2k_production/')
            slurm_batch=glob.glob('*.sh')
            os.system(f'sbatch {slurm_batch[0]}')
            with open("JOB_SUBMITTED",'w') as f1:
                f1.write("JOB_SUBMITTED")
            os.chdir(work_dir)
        except Exception as e:
            print(f"An error occurred while running the CP2K production: {e}")


    @staticmethod
    def clear():
        directory = "cp2k_production/"
        files_to_remove = glob.glob(os.path.join(directory, "*"))
        if files_to_remove:
            for file_path in files_to_remove:
                if os.path.isfile(file_path):
                    os.remove(file_path)


