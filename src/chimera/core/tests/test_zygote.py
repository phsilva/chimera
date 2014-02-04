from chimera.core.location import Location
from chimera.core.proxy import Proxy
from chimera.core.zygote import Zygote
from chimera.core.exceptions import ChimeraException

import time
import sys

class TestZygote(object):

	def test_messaging(self):
		z1 = Zygote(Location("/ZygoteHelper/z1"))
		z1.start()

		z2 = Zygote(Location("/ZygoteHelper/z2"))
		z2.start()

		p1 = Proxy(Location("/ZygoteHelper/z1"))
		p1.resolved = True

		p2 = Proxy(Location("/ZygoteHelper/z2"))
		p2.resolved = True

		# FIXME: control starts before __start__
		p1.__start__()
		p2.__start__()

		# sync call
		l1 = p1.getLocation()
		l2 = p2.getLocation()
		assert l1 == "/ZygoteHelper/z1"
		assert l2 == "/ZygoteHelper/z2"

		p1.callOtherProxy()

		# non existing methods
		try:
			p1.nonExistingMethod()
		except ChimeraException, e:
			e.printStackTrace()

		try:
			p1.raiseException()
		except ChimeraException, e:
			e.printStackTrace()

		# event handling
		p1.someEvent += p1.someEventCallback

		# proxy initiated
		p1.someEvent(42)

		# let control push some events too
		time.sleep(5)

		p1.someEvent -= p1.someEventCallback

		p1.__stop__()
		p2.__stop__()

		z1.stop()
		z2.stop()
