import sys
import time

from chimera.core.manager import Manager
from chimera.core.proxy import Proxy

if __name__ == "__main__":
    manager = Manager()

    tel = Proxy("/FakeTelescope/0")

    for i in range(1000):
        t0 = time.time()
        pos = tel.getPositionRaDec()

        print "# %.3f" % (time.time() - t0)
        sys.stdout.flush()

