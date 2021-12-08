source experimentconfig.sh


EXPERIMENT="G10"

export repetitions=1
export LOOPFUNCTION="floor_estimation_no_convergence_loop.py"
export LENGTH=36000
export NUMROBOTS=16
export robots=16
export num_byzantines=4
export byzantine_swarm_style=1
export FLOORFILE=31.png
export ARENADIM=1.55
export ARENADIMH=0.775

source run_experiment.sh
