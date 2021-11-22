source experimentconfig.sh

<<<<<<< HEAD
EXPERIMENT="debug"

export NUMROBOTS=2
export robots=2
=======
EXPERIMENT="G1"

export NUMROBOTS=8
export robots=8
>>>>>>> 1d39a74493ed66d468197aad224873b02df9e4ce
export num_byzantines=(0)
export byzantine_swarm_style=1
export FLOORFILE=38.png
export ARENADIM=1.90
export ARENADIMH=0.95

source run_experiment.sh
