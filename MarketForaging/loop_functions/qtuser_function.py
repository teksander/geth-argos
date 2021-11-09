
import random
import configparser
import os
import json
from types import SimpleNamespace

# General Parameters
generic_params = dict()
generic_params['arena_size'] = float(os.environ["ARENADIM"])
generic_params['num_robots'] = int(os.environ["NUMROBOTS"])

# Parameters for marketplace
market_params = dict()
market_params['position'] = 'left'
market_params['size'] = 0.1 * generic_params['arena_size'] 

resource_file = 'resources.txt'

class resource_obj(object):
    def __init__(self, x, y, quality, quantity):
        self.x = x
        self.y = y
        self.quality = quality
        self.quantity = quantity
        self.timeStamp = 0

    def getJSON(self):
        return str(vars(self)).replace("\'", "\"")


def init():
	global market, item_list

	# Create the market instance
	market = resource_obj(x = 0, y = 0, quality = market_params['size'], quantity = 1)

	# Create a list of random circles centered around (0,0)	
	item_list = []
	for i in range(0,30):
		res_diam = 0.025
		quality = 0.1
		x = random.uniform(-0.9*quality+res_diam, 0.9*quality-res_diam)
		y = random.uniform(-0.9*quality+res_diam, 0.9*quality-res_diam)
		item_list.append((x,y))


def DrawInWorld():
	
	environment.qt_draw.circle([market.x, market.y, 0.01],[], market.quality, 'yellow', True)
	
	resource_list = []

	with open(resource_file, 'r') as f:
		for line in f:
			res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			resource_list.append(res)

	for res in resource_list:
		environment.qt_draw.circle([res.x, res.y, 0.01],[], res.quality, 'red', False)

		for i in range(0,res.quantity):
			environment.qt_draw.circle([res.x+item_list[i][0], res.y+item_list[i][1], 0.01],[], 0.025, 'red', True)
			environment.qt_draw.cylinder([res.x+item_list[i][0], res.y+item_list[i][1], 0.01],[], 0.025, 0.05, 'red')

