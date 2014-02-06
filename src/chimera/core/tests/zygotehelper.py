from chimera.core.chimeraobject import ChimeraObject
from chimera.core.proxy import Proxy
from chimera.core.event import event

import random


class ZygoteHelper(ChimeraObject):

	def __init__(self):
		ChimeraObject.__init__(self)

	def __start__(self):
		print "[start]", self.getLocation()
		self.someEvent += self.someEventCallback
		return True

	def __stop__(self):
		print "[stop]", self.getLocation()
		self.someEvent -= self.someEventCallback		
		return True

	def control(self):
		print "[control]", self.getLocation()
		self.log.info("[control]" + str(self.getLocation()))
		self.someEvent(random.randint(0, 4096))
		return True

	def callOtherProxy(self):
		p = Proxy("/ZygoteHelper/z2")
		p.resolved = True
		p.work()

	def work(self):
		print "this was called using a proxy to z1 that got a proxy to z2 (me %s)" % self.getLocation()

	def callMe(self, a, b):
		print "callMe: %d %d" % (a,b)
		self.log.info("callMe: %d %d" % (a,b))
		return a + b

	def raiseException(self):
		raise Exception("Something wrong.")

	def someEventCallback(self, status):
		print "[event received]", self.getLocation(), status

	@event
	def someEvent(self, status):
		pass

