#!/bin/bash
#SBATCH -J LUPJ_WU_1440_mesh_NEW
#SBATCH -p kshcnormal 
#SBATCH -n 32
#SBATCH -N 1
#SBATCH --ntasks-per-node=32
#SBATCH --cpus-per-task=1
#SBATCH --exclusive
#SBATCH -o job_%x.out
#SBATCH -e job_%x.err
module purge
module load compiler/gnu/9.3.0
module load compiler/intel/2017.5.239
module load mpi/hpcx/2.11.0/intel-2017.5.239
export MPI_ROOT=/opt/hpc/software/mpi/hpcx/v2.11.0/intel-2017.5.239
source /public/home/chenzhi/dftorch/OpenFOAM-7/etc/bashrc
source /public/home/chenzhi/dftorch/deepflame-dev/bashrc

##decomposePar  -latestTime -force
#mpirun -np 2560 checkMesh -parallel > log.checkMesh
# mpirun -np 128 /public/home/chenzhi/mzhang/of7/deepflame-cpu/deepflame-dev-master/bin/dfLowMachFoam -parallel
# # /public/software/compiler/intel/onepai-2021.3/vtune/2021.5.0/bin64/vtune  -trace-mpi -collect hotspots -r result mpirun -np 640 /public/home/chenzhi/OpenFOAM/chenzhi-7/platforms/linux64GccDPInt32Opt/bin/df0DFoam -parallel

setFields
decomposePar -force
mpirun -np 32 /public/home/chenzhi/dftorch/deepflame-dev/platforms/linux64GccDPInt32Opt/bin/dfLowMachFoam -parallel
##mpirun -np 512 /public/home/chenzhi/dftorch/deepflame-dev/platforms/linux64GccDPInt32Opt/bin/dfLowMachFoam-limitTP -parallel
./recon
