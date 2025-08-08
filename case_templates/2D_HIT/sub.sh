setFields
blockMesh
decomposePar -force 
mpirun --allow-run-as-root --use-hwthread-cpus -np 32 dfLowMachFoam -parallel
# sbatch run.sbatch
./recon
# reconstructPar -latestTime
