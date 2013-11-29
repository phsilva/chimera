from chimera.core.manager import Manager
from chimera.core.proxy import Proxy
from chimera.core.callback import callback
from chimera.util.position import Position

if __name__ == "__main__":
    manager = Manager()

    tel = Proxy("/FakeTelescope/0")
    print "[current position]", tel.getPositionRaDec()

    @callback(manager)
    def slewBegin(target):
        print "[slew begin]", target

    @callback(manager)
    def slewComplete(position, status):
        print "[slew complete] ", position, status

    tel.slewBegin += slewBegin
    tel.slewComplete += slewComplete

    tel.slewToRaDec(Position.fromRaDec(10,10))

    manager.wait()

