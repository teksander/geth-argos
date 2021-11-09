source experimentconfig.sh

EXPERIMENT="G6"

export NUMROBOTS=16
export robots=16
export num_byzantines=(4)
export byzantine_swarm_style=1
export FLOORFILE=38.png
export ARENADIM=1.90
export ARENADIMH=0.95

source run_experiment.sh
