source experimentconfig.sh

EXPERIMENT="G9"

export NUMROBOTS=48
export robots=48
export num_byzantines=12
export byzantine_swarm_style=1
export FLOORFILE=54.png
export ARENADIM=2.7
export ARENADIMH=1.35

source run_experiment.sh
