source experimentconfig.sh


EXPERIMENT="G10"

export repetitions=1
export LOOPFUNCTION="floor_estimation_no_convergence_loop.py"
export LENGTH=36000
export NUMROBOTS=8
export robots=8
export num_byzantines=2
export byzantine_swarm_style=1
export FLOORFILE=22.png
export ARENADIM=1.10
export ARENADIMH=0.55

source run_experiment.sh
