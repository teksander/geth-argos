source experimentconfig.sh

EXPERIMENT="G3"

export NUMROBOTS=24
export robots=24
export num_byzantines=(0 3 6 9 12)
export byzantine_swarm_style=3
export FLOORFILE=38.png
export ARENADIM=1.90
export ARENADIMH=0.95

source run_experiment.sh