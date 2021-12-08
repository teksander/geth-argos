source experimentconfig.sh

EXPERIMENT="G10"

export NUMROBOTS=72
export robots=72
export num_byzantines=18
export byzantine_swarm_style=1
export FLOORFILE=66.png
export ARENADIM=3.3
export ARENADIMH=1.65

source run_experiment.sh
