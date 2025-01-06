import os
import glob
import shutil
import subprocess

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

def extract_unique_elements(file_path):
    import os

    def parse_pdb(file_path):
        elements = set()
        with open(file_path, 'r') as file:
            for line in file:
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    element = line[76:78].strip()
                    if element:
                        elements.add(element)
        return elements

    def parse_xyz(file_path):
        elements = set()
        with open(file_path, 'r') as file:
            lines = file.readlines()
            for line in lines[2:]:  # skip the first two lines
                parts = line.split()
                if parts:
                    element = parts[0]
                    elements.add(element)
        return elements

    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.pdb':
        return list(parse_pdb(file_path))
    elif file_extension.lower() == '.xyz':
        return list(parse_xyz(file_path))
    else:
        raise ValueError("Unsupported file format. Please provide a PDB or XYZ file.")


class Cp2kEquilibration:
    @staticmethod
    def setup(template_dir="input_files/cp2k_equilibration"):



        #Copy Input structure to work directory
        input_xyz = glob.glob("input_files/cp2k_equilibration/*.xyz")
        input_pdb = glob.glob("input_files/cp2k_equilibration/*.pdb")



        if input_xyz:
            xyz_file_name=input_xyz[0].split('/')
            shutil.copy(input_xyz[0],f"cp2k_equilibration/{xyz_file_name[-1]}")

        if input_pdb:
            pdb_file_name=input_pdb[0].split('/')
            shutil.copy(input_pdb[0],f"cp2k_equilibration/{pdb_file_name[-1]}")


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

                        modified_content = Cp2kEquilibration.replace_specific_variables_inp(
                            modified_content)

                    if ext == '.sh':
                        modified_content = Cp2kEquilibration.replace_specific_variables_sh(modified_content)

                    # Save modified template file
                    with open(f"cp2k_equilibration/{template_file}", 'w') as f:
                        f.write(modified_content)




    def replace_specific_variables_inp(content):
        # Replace specific variables in .inp file content
        work_dir = os.getcwd()
        work_folder_tmp = work_dir.split('/')
        work_folder = work_folder_tmp[-1]

        input_xyz = glob.glob("input_files/cp2k_equilibration/*.xyz")
        input_pdb = glob.glob("input_files/cp2k_equilibration/*.pdb")



        content = content.replace("PROJECT {cp2k_equilibrium}", f"PROJECT {work_folder}_eq")
        if input_xyz:
            elements = extract_unique_elements(input_xyz[0])
            xyz_file_name=input_xyz[0].split('/')
            content = content.replace("COORD_FILE_NAME {mod_nvt_inp.xyz/pdb}", f"COORD_FILE_NAME {xyz_file_name[-1]}")
            content = content.replace("COORDINATE {XYZ/PDB}", f"COORDINATE XYZ")
        if input_pdb:
            elements = extract_unique_elements(input_pdb[0])
            pdb_file_name=input_pdb[0].split('/')
            content = content.replace("COORD_FILE_NAME {mod_nvt_inp.xyz/pdb}", f"COORD_FILE_NAME {pdb_file_name[-1]}")
            content = content.replace("COORDINATE {XYZ/PDB}", f"COORDINATE PDB")

        if input_xyz or input_pdb:
            potentials, basis_set = find_potential("input_files/utils/POTENTIAL",elements)
            kind_cp2k_inp = []
            for element,potential,basis in zip(elements,potentials,basis_set):
                kind_cp2k_inp.append(f"&KIND {element}\n\tBASIS_SET {basis}\n\tPOTENTIAL {potential}\n&END KIND\n")
            kind_str = ''.join(kind_cp2k_inp)
            content = content.replace("{KIND}",f"{kind_str}")

        return content


    def replace_specific_variables_sh(content):
        work_dir = os.getcwd()
        work_folder_tmp = work_dir.split('/')
        work_folder = work_folder_tmp[-1]
        inp_file=glob.glob("input_files/cp2k_equilibration/*.inp")
        inp_file_tmp=inp_file[0].split('/')
        inp_file=inp_file_tmp[-1]

        content = content.replace("$MPIEXEC $FLAGS_MPI_BATCH cp2k.popt {mod_nvt.inp} > nvt.out",f"$MPIEXEC $FLAGS_MPI_BATCH cp2k.popt {inp_file} > nvt.out")
        content = content.replace("#SBATCH --job-name={job_name_eq}",f"#SBATCH --job-name={work_folder}_eq")

        return content

    @staticmethod
    def run():
        try:
            work_dir=os.getcwd()
            os.chdir('cp2k_equilibration/')
            slurm_batch=glob.glob('*.sh')
            os.system(f'sbatch {slurm_batch[0]}')
            with open("JOB_SUBMITTED",'w') as f1:
                f1.write("JOB_SUBMITTED")
            os.chdir(work_dir)
        except Exception as e:
            print(f"An error occurred while running the CP2K equilibration: {e}")

    @staticmethod
    def clear():
        directory = "cp2k_equilibration/"
        files_to_remove = glob.glob(os.path.join(directory, "*"))
        if files_to_remove:
            for file_path in files_to_remove:
                if os.path.isfile(file_path):
                    os.remove(file_path)

