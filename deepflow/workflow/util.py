import numpy as np
import glob
import csv
import os
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

class UtilizationTools:
    @staticmethod
    def distance_with_pbc(point1, point2, pbc_length):
        """
        Calculate the distance between two points with periodic boundary conditions.

        Args:
        - point1 (tuple or list): Coordinates of the first point (x, y, z).
        - point2 (tuple or list): Coordinates of the second point (x, y, z).
        - pbc_length (tuple or list): Lengths of the periodic boundary conditions in each dimension (x, y, z).

        Returns:
        - float: The distance between the two points with PBC.
        """
        num_atom_1 = point1[0]
        xyz_1 = point1[1:]

        num_atom_2 = point2[0]
        xyz_2 = point2[1:]

        # Convert inputs to numpy arrays for easier calculations
        point1 = np.array(xyz_1)
        point2 = np.array(xyz_2)
        pbc_length = np.array(pbc_length)

        # Calculate the distance between the points in each dimension
        delta = np.abs(point1 - point2)

        # Apply periodic boundary conditions
        delta = np.where(delta > 0.5 * pbc_length, pbc_length - delta, delta)

        # Calculate the Euclidean distance
        distance = np.sqrt(np.sum(delta ** 2))


        return num_atom_1, num_atom_2, distance

    @staticmethod
    def find_bonds(atoms, pbc_length, min_dist=1.0, max_dist=1.85):
        """
        Find bonds between atoms based on distance thresholds.

        Args:
        - atoms (list): List of atom coordinates.
        - pbc_length (tuple or list): Lengths of the periodic boundary conditions in each dimension (x, y, z).
        - min_dist (float): Minimum distance threshold for a bond.
        - max_dist (float): Maximum distance threshold for a bond.

        Returns:
        - list: List of bonded atom pairs.
        """
        bonds = []
        num_atoms = len(atoms)
        for i in range(num_atoms):
            for j in range(i + 1, num_atoms):
                num_atom_1, num_atom_2, dist = UtilizationTools.distance_with_pbc(atoms[i], atoms[j], pbc_length)
                if min_dist <= dist <= max_dist:
                    bonds.append([num_atom_1,num_atom_2,dist])  # Using 1-based indexing for atom numbers
        return bonds

    @staticmethod
    def read_lmp_format(file_path):
        """
        Read a lmp file format and extract atomic coordinates and PBC lengths.

        Args:
        - file_path (str): Path to the file.

        Returns:
        - tuple: (list of atom coordinates, tuple of PBC lengths)
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()

            # Read number of atoms (first line) and number of atom types (second line)
            num_atoms_tmp = lines[1].split()
            num_atoms = int(num_atoms_tmp[0])

            num_types_tmp = lines[2].split()
            num_types = int(num_types_tmp[0])

            # Read PBC lengths
            xlo, xhi = map(float, lines[3].split()[:2])
            ylo, yhi = map(float, lines[4].split()[:2])
            zlo, zhi = map(float, lines[5].split()[:2])
            pbc_length = (xhi - xlo, yhi - ylo, zhi - zlo)

            # Read atoms starting from line 8 (index 7)
            atoms = []
            for line in lines[10:10 + num_atoms]:
                parts = line.split()
                num = float(parts[0])
                x, y, z = map(float, parts[2:5])
                atoms.append((num, x, y, z))

        return atoms, pbc_length

    @staticmethod
    def get_bonds(min_dist = 1.0, max_dist = 1.85):
        lmp_file=glob.glob("**/*.lmp")

        atoms, pbc_length = UtilizationTools.read_lmp_format(lmp_file[0])
        bonds = UtilizationTools.find_bonds(atoms, pbc_length, min_dist, max_dist)

        if not os.path.exists("Analysis"):
            os.mkdir("Analysis")

        with open('Analysis/bonds.dat','w') as f1:
            for bond in bonds:
                for atom in bond:
                    f1.write(str(atom))
                    f1.write('\t')
                f1.write('\n')

    @staticmethod
    def read_trajectory(file_path):
        """
        Read a trajectory file and extract atom coordinates for each timestep.

        Args:
        - file_path (str): Path to the trajectory file.

        Returns:
        - list: List of timesteps, each containing a list of atom coordinates.
        - tuple: The periodic boundary condition lengths (pbc_length).
        - list: List of timestep indices.
        """
        with open(file_path, 'r') as file:
            lines = file.readlines()

        timesteps = []
        pbc_length = None
        time_indices = []
        i = 0

        while i < len(lines):
            if "ITEM: TIMESTEP" in lines[i]:
                timestep = []
                i += 1
                time_index = int(lines[i].strip())
                time_indices.append(time_index)
                i += 2  # Skip "ITEM: NUMBER OF ATOMS"
                num_atoms = int(lines[i].strip())
                i += 1
                i += 1  # Skip "ITEM: BOX BOUNDS xy xz yz pp pp pp"
                pbc_length = (float(lines[i].split()[1]),
                              float(lines[i+1].split()[1]),
                              float(lines[i+2].split()[1]))
                i += 3
                i += 1  # Skip "ITEM: ATOMS id type x y z"
                for _ in range(num_atoms):
                    parts = lines[i].split()
                    num = int(parts[0])
                    x, y, z = map(float, parts[2:5])
                    timestep.append((num, x, y, z))
                    i += 1
                timesteps.append(timestep)
            else:
                i += 1

        return timesteps, pbc_length, time_indices

    @staticmethod
    def avg_bond_length(iteration=all, min_dist_thresh=1.0, max_dist_thresh=1.85, stride=1, lammpstrj_loc = None):
        """
        Calculate the average bond length for each timestep and append to a CSV file.

        Args:
        - output_file (str): Path to the output CSV file.
        - min_dist_thresh (float): Minimum distance threshold for bond detection.
        - max_dist_thresh (float): Maximum distance threshold for bond detection.
        - stride (int): Stride value to process every x timesteps.
        """

        # Locate the LAMMPS file and read atoms and PBC length
        lmp_file = glob.glob("**/*.lmp")[0]
        atoms, pbc_length = UtilizationTools.read_lmp_format(lmp_file)
        bonds = UtilizationTools.find_bonds(atoms, pbc_length, min_dist=min_dist_thresh, max_dist=max_dist_thresh)

        if not os.path.exists("Analysis"):
            os.mkdir("Analysis")


        # Locate the trajectory file and read timesteps and PBC length

        if iteration==all:
            traj = sorted(glob.glob('**/iter.*/01.model_devi/**/all.lammpstrj'))

        elif iteration==latest:
            traj = sorted(glob.glob('**/iter.*/01.model_devi/**/all.lammpstrj'))
            timesteps, pbc_length, time_indices = UtilizationTools.read_trajectory(traj)[-1]
        else:
            traj = sorted(glob.glob('**/iter.*/01.model_devi/**/all.lammpstrj'))
            timesteps, pbc_length, time_indices = UtilizationTools.read_trajectory(traj)[iteration]

        if not lammpstrj_loc == None:
            traj = sorted(glob.glob(lammpstrj_loc))
            timesteps, pbc_length, time_indices = UtilizationTools.read_trajectory(traj[0])
            

        for itera in traj:
            iter_number=itera.split('/')[1]
                # Initialize the CSV file with a header
            with open(f'Analysis/avg_bond_length_{iter_number}.csv', 'w') as f:
                f.write('time,avg_bond_length\n')
            timesteps, pbc_length, time_indices = UtilizationTools.read_trajectory(itera)
            # Calculate average bond length for each timestep with the specified stride
            for idx in range(0, len(timesteps), stride):
                timestep = timesteps[idx]
                bond_length_total = 0

                for bond in bonds:
                    atom_num_1, atom_num_2, abs_dist_ref = bond
                    xyz_1, xyz_2 = None, None

                    for point in timestep:
                        num = point[0]
                        if num == atom_num_1:
                            xyz_1 = point
                        elif num == atom_num_2:
                            xyz_2 = point

                        if xyz_1 is not None and xyz_2 is not None:
                            _, _, dist = UtilizationTools.distance_with_pbc(xyz_1, xyz_2, pbc_length)
                            abs_dist = abs(dist)
                            bond_length_total += abs_dist
                            break

                bond_length_avg = bond_length_total / len(bonds)

                # Append the average bond length to the CSV file
                with open(f'Analysis/avg_bond_length_{iter_number}.csv', 'a') as f:
                    f.write(f'{time_indices[idx]},{bond_length_avg}\n')


    @staticmethod
    def plot(args='all',iteration=all):
        if not os.path.exists("Analysis"):
            os.mkdir("Analysis")

        if not os.path.exists("Analysis/plot_colvar"):
            os.mkdir("Analysis/plot_colvar")

        if not os.path.exists("Analysis/plot_avg_bond_length"):
            os.mkdir("Analysis/plot_avg_bond_length")

        if not os.path.exists("Analysis/plot_max_devi_f"):
            os.mkdir("Analysis/plot_max_devi_f")

        if iteration==all:
            colvar_files = sorted(glob.glob('**/iter.*/01.model_devi/**/COLVAR'))
            avg_bond_length_files = sorted(glob.glob('Analysis/*.csv'))
            max_devi_f_files = sorted(glob.glob('**/iter.*/01.model_devi/**/model_devi.out'))
        else:
            colvar_files = sorted(glob.glob(f'**/iter.*{iteration}/01.model_devi/**/COLVAR'))
            avg_bond_length_files = sorted(glob.glob(f'Analysis/avg_bond_length_iter.*{iteration}.csv'))
            max_devi_f_files = sorted(glob.glob(f'**/iter.*{iteration}/01.model_devi/**/model_devi.out'))


        if args == 'all' or args == 'COLVAR':
            for file in colvar_files:
                colvar_number = file.split("/")[-4]  # Extract COLVAR number
                data = pd.read_csv(file, delimiter=r'\s+', skiprows=3, comment='#', header=None)
                sns.scatterplot(x=data.iloc[:,0], y=data.iloc[:,1], s=1)
                plt.xlabel('Time [fs]')
                plt.ylabel('CV')
                plt.savefig(f'Analysis/plot_colvar/plot_colvar_{colvar_number}.png')
                plt.close()  # Close the plot without displaying

        if args == 'all' or args == 'avg_bond_length':
            for file in avg_bond_length_files:
                avg_bond_length_number = file.split("/")[-1].split(".")[1]
                data = pd.read_csv(file)
                sns.scatterplot(x=data.iloc[:,0], y=data.iloc[:,1], s=1)
                plt.xlabel('Timestep')
                plt.ylabel('Avg. Bond length')
                plt.ylim(0.5, 2.5)
                plt.savefig(f'Analysis/plot_avg_bond_length/plot_avg_bond_length_{avg_bond_length_number}.png')
                plt.close()  # Close the plot without displaying

        if args == 'all' or args == 'max_devi_f':
            for file in max_devi_f_files:

                max_devi_f_number = file.split("/")[-4]
                data = pd.read_csv(file, delimiter=r'\s+', skiprows=1, comment='#', header=None)
                sns.scatterplot(x=data.iloc[:,0], y=data.iloc[:,4], s=1)
                plt.xlabel('Timestep')
                plt.ylabel('max_devi_force')
                plt.ylim(0, 2)
                plt.savefig(f'Analysis/plot_max_devi_f/plot_max_devi_f_{max_devi_f_number}.png')
                plt.close()  # Close the plot without displaying










