source experimentconfig.sh

# 1008 robots (42 * 24)

EXPERIMENT="G9"

export NUMROBOTS=1008
export robots=1008
export num_byzantines=254
export byzantine_swarm_style=1
export FLOORFILE=247.png
export ARENADIM=12.35
export ARENADIMH=6.175

source run_experiment.sh
