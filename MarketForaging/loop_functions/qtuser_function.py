
import json
from types import SimpleNamespace

global resource_list
resource_list = []
resource_file = 'resources.txt'
market = json.loads('{"x": 0, "y": 0, "quality": 0.1, "quantity": 1, "timeStamp": 0.0}', object_hook=lambda d: SimpleNamespace(**d))

def init():
	# environment.qt_draw.circle([market.x, market.y, 0.01],[], market.quality, 'blue')
	pass
	# print('TESTING THE PYTHON PART OF QT USER')

global step 
step = 1

def DrawInWorld():
	global step, resource_list
	environment.qt_draw.circle([market.x, market.y, 0.01],[], market.quality, 'green')
	
	step += 1
	resource_list = []

	with open(resource_file, 'r') as f:
		for line in f:
			res = json.loads(line, object_hook=lambda d: SimpleNamespace(**d))
			resource_list.append(res)

	for res in resource_list:
		environment.qt_draw.circle([res.x, res.y, 0.01],[], res.quality, 'red')


	# print('TESTING THE PYTHON PART OF QT USER22')