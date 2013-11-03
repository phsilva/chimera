from chimera.core.proxy import Proxy
from chimera.util.position import Position

tel = Proxy("/FakeTelescope/0")
print tel.getPositionRaDec()

tel.slewToRaDec(Position.fromRaDec(10,10))
print tel.getPositionRaDec()
