source experimentconfig.sh

EXPERIMENT="debug"

export NUMROBOTS=2
export robots=2
export num_byzantines=(0)
export byzantine_swarm_style=1
export FLOORFILE=38.png
export ARENADIM=1.90
export ARENADIMH=0.95

source run_experiment.sh
