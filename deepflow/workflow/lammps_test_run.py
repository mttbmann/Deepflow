import os
import glob
import shutil
import re
import pandas as pd


class LammpsTestRun:
    @staticmethod
    def setup(model_iter : int,steps=20000000,temperature=310):
        model_iter_str = f"{model_iter:06d}"

        try:
            shutil.rmtree(f'lammps_test_run/{model_iter}_{temperature}')
        except:
            pass    


        # Define paths
        md_folder = f"dpgen_active_learning/iter.{model_iter_str}/01.model_devi/"
        print(md_folder)
        path_model = sorted(glob.glob(f"dpgen_active_learning/iter.{model_iter_str}/00.train/graph.*.pb"))
        

        # Copy folder to directory

        shutil.copytree(md_folder,f'lammps_test_run/{model_iter}_{temperature}')
        
        # Copy model files
        for model in path_model:
            model_name = os.path.basename(model)
            shutil.copyfile(model, f"lammps_test_run/{model_iter}_{temperature}/{model_name}")
        try:
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/all.lammpstrj')
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/COLVAR')
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/output.plumed')
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/model_devi.log')
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/model_devi.out')
            os.remove(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/job.json')
        except:
            pass

        shutil.copy('input_files/lammps_run/lammps.sh',f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/lammps.sh')
        shutil.copy('input_files/lammps_run/plumed.dat',f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/input.plumed')

        with open(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/input.lammps') as f1:
            modify_input_lammps = f1.read()

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

        # Replace the desired strings
        modify_input_lammps = re.sub(r'NSTEPS\s+equal\s+\d+', f'NSTEPS          equal {steps}', modify_input_lammps)
        modify_input_lammps = modify_input_lammps.replace(
            "dump            dpgen_dump all custom 10    all.lammpstrj id type x y z",
            "dump            dpgen_dump all custom 200    all.lammpstrj id type x y z\ndump            1 all xyz ${DUMP_FREQ} dump.0.xyz\ndump_modify     1 append yes element "+str(elements_str)
        )
        modify_input_lammps = modify_input_lammps.replace("run             ${NSTEPS}","restart 1000000 restart.*.equil\nrun             ${NSTEPS}")
        modify_input_lammps = modify_input_lammps.replace("variable        TEMP            equal 310",f"variable        TEMP            equal {temperature}")

        # Write the modified content back to the file
        with open(f"lammps_test_run/{model_iter}_{temperature}/task.000.000000/input.lammps", 'w') as f1:
            f1.write(modify_input_lammps)

        with open(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/input.plumed') as f1:
            modify_input_plumed = f1.read()
        
        modify_input_plumed = modify_input_plumed.replace("TEMP=xxx",f"TEMP={temperature}")

        with open(f'lammps_test_run/{model_iter}_{temperature}/task.000.000000/input.plumed','w') as f1:
            f1.write(modify_input_plumed)


    @staticmethod
    def restart():
        model_devi_files = glob.glob(f'lammps_test_run/**/task.000.000000/model_devi.out')
        
        for model_devi in model_devi_files:
            md_folder = model_devi.split('/')[-3]
            df = pd.read_csv(model_devi, delim_whitespace=True)


            column_name = 'avg_devi_v'


            segment_size = 1000
            threshold = 0.50

            averages = []

            # Loop through the dataframe in segments of 1000 rows
            for i in range(0, len(df), segment_size):
                segment = df[column_name].iloc[i:i+segment_size]
                segment_average = segment.mean()
                if segment_average > threshold:
                    restart_number_temp = (i+1)*10
                    restart_number = (restart_number_temp // 1000000) * 1000000
                    if restart_number == 0:
                        print(f"{model_devi} does not have a restart file.")
                        try:
                            job_number_temp = glob.glob(f'lammps_test_run/{md_folder}/task.000.000000/output.*.txt')
                            job_number = job_number_temp[0].split('.')[-2]
                            print(f'scancel {job_number}')
                            os.system(f'scancel {job_number}')
                            os.remove(job_number_temp[0])
                        except:
                            pass
                        break
            
                    
                    restart_file = f"restart.{restart_number}.equil"

                    print(f"Starting {model_devi} from {restart_file}.")
                    
                    try:
                        job_number_temp = glob.glob(f'lammps_test_run/{md_folder}/task.000.000000/output.*.txt')
                        job_number = job_number_temp[0].split('.')[-2]
                        print(f'scancel {job_number}')
                        os.system(f'scancel {job_number}')
                        os.remove(job_number_temp[0])
                    except:
                        pass


                    with open(f'lammps_test_run/{md_folder}/task.000.000000/input.lammps') as f1:
                        lines = f1.readlines()

                    search_string = "read_data"
                    search_string_2 = "read_restart"
                    replacement_line = f"read_restart       {restart_file}\n"

                    with open(f"lammps_test_run/{md_folder}/task.000.000000/input.lammps", 'w') as f1:
                        for line in lines:
                            if line.startswith(search_string):
                                f1.write(replacement_line)
                            elif line.startswith(search_string_2):
                                f1.write(replacement_line)
                            else:
                                f1.write(line)

                    with open(f'lammps_test_run/{md_folder}/task.000.000000/input.plumed') as f1:
                        modify_input_plumed = f1.read()
                    
                    stride_match = re.search(r'STRIDE=(\d+)', modify_input_plumed)
                    if stride_match:
                        stride_value = stride_match.group(1)      

                    modify_input_plumed = modify_input_plumed.replace("#RESTART",f"RESTART")

                    with open(f'lammps_test_run/{md_folder}/task.000.000000/input.plumed','w') as f1:
                        f1.write(modify_input_plumed)
                    shutil.copy('input_files/lammps_run/lammps.sh',f'lammps_test_run/{md_folder}/task.000.000000/lammps.sh')

                    
                    
                    def delete_lines_after(file_path, line_number):
                        with open(file_path, 'r') as f:
                            lines = f.readlines()
                        with open(file_path, 'w') as f:
                            f.writelines(lines[:line_number])

                    def count_valid_fields(colvar_file, restart_number_2):
                        with open(colvar_file, 'r') as f:
                            lines = f.readlines()

                        # Count total 'FIELDS' in the entire file
                        total_fields_count = sum(1 for line in lines if 'FIELDS' in line)

                        # Determine the lines to keep after the restart
                        lines_to_keep = lines[:3+restart_number_2]

                        # Count 'FIELDS' occurrences in the lines that will be kept
                        valid_fields_count = sum(1 for line in lines_to_keep if 'FIELDS' in line)

                        # The count of valid FIELDS occurrences
                        return valid_fields_count


                    colvar_file = f'lammps_test_run/{md_folder}/task.000.000000/COLVAR'
                    hills_file = f'lammps_test_run/{md_folder}/task.000.000000/HILLS'

                    number_restarts = count_valid_fields(colvar_file,restart_number)

                    delete_lines_after(colvar_file, number_restarts*3+(restart_number//stride_value))
                    delete_lines_after(hills_file,number_restarts*5+(restart_number//50))
                    delete_lines_after(model_devi,1+restart_number//10)

                    break
            else:
                job_number_temp = glob.glob(f'lammps_test_run/{md_folder}/task.000.000000/output.*.txt')
                job_number = job_number_temp[0].split('.')[-2]

                if job_number_temp:  # Check if the glob found any files
                    job_number = job_number_temp[0].split('.')[-2]

                    with open(job_number_temp[0], 'r') as f1:  # Open the file
                        output_lines = f1.readlines()  # Read all lines in the file

                    # Check the last 10 lines in reverse order
                    for line in reversed(output_lines[-10:]):
                        if 'Total wall time:' in line:
                            print(f'{md_folder} MD run finished without breaking. Restarting from last checkpoint.')
                            with open(f'lammps_test_run/{md_folder}/task.000.000000/input.lammps') as f1:
                                lines = f1.readlines()

                            restart_files = glob.glob(f'lammps_test_run/{md_folder}/task.000.000000/restart.*.equil')
                            if restart_files:
                                numbered_files = [(int(re.search(r'restart\.(\d+)\.equil', file).group(1)), file) for file in restart_files]
                                max_number, max_file = max(numbered_files, key=lambda x: x[0])
                                restart_file_2 = max_file.split('/')[-1]
                            
                            search_string = "read_data"
                            search_string_2 = "read_restart"
                            replacement_line = f"read_restart       {restart_file_2}\n"

                            with open(f"lammps_test_run/{md_folder}/task.000.000000/input.lammps", 'w') as f1:
                                for line in lines:
                                    if line.startswith(search_string):
                                        f1.write(replacement_line)
                                    elif line.startswith(search_string_2):
                                        f1.write(replacement_line)
                                    else:
                                        f1.write(line)

                            with open(f'lammps_test_run/{md_folder}/task.000.000000/input.plumed') as f1:
                                modify_input_plumed = f1.read()
                            
                            modify_input_plumed = modify_input_plumed.replace("#RESTART",f"RESTART")

                            with open(f'lammps_test_run/{md_folder}/task.000.000000/input.plumed','w') as f1:
                                f1.write(modify_input_plumed)
                            shutil.copy('input_files/lammps_run/lammps.sh',f'lammps_test_run/{md_folder}/task.000.000000/lammps.sh')
                            os.remove(job_number_temp[0])
                            break
                    else:

                        pass






    @staticmethod
    def run():
        cwd = os.getcwd()

        sub_sh_list = glob.glob('lammps_test_run/**/**/*.sh')

        for sh in sub_sh_list:
            try:
                sub_dir = os.path.dirname(sh)
                os.chdir(sub_dir)
                os.system("sbatch lammps.sh")
                
                os.chdir(cwd)
                os.remove(sh)
            except:
                os.chdir(cwd)
                pass



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
