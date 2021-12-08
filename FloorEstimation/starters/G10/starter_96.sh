source experimentconfig.sh

EXPERIMENT="G9"

export NUMROBOTS=96
export robots=96
export num_byzantines=24
export byzantine_swarm_style=1
export FLOORFILE=76.png
export ARENADIM=3.8
export ARENADIMH=1.9

source run_experiment.sh
