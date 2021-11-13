source experimentconfig.sh

EXPERIMENT="G2"

export NUMROBOTS=24
export robots=24
export num_byzantines=(0 3 6 9 12)
export byzantine_swarm_style=1
export FLOORFILE=38_dynamic.png
export ARENADIM=1.90
export ARENADIMH=0.95

source run_experiment.sh
