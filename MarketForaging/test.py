

class X(object):

	def __init__(self):
		self.x = 1

x = X()

def test():

	x.x += 2
	print(x.x)


test()
print(x.x)