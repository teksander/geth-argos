source experimentconfig.sh

EXPERIMENT="G9"

export NUMROBOTS=120
export robots=120
export num_byzantines=30
export byzantine_swarm_style=1
export FLOORFILE=85.png
export ARENADIM=4.25
export ARENADIMH=2.125

source run_experiment.sh
