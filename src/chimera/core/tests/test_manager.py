import os.path

from nose.tools import assert_raises

from chimera.core.manager        import Manager
from chimera.core.chimeraobject  import ChimeraObject
from chimera.core.proxy          import Proxy
from chimera.core.exceptions     import InvalidLocationException
from chimera.core.exceptions     import NotValidChimeraObjectException
from chimera.core.exceptions     import ChimeraObjectException
from chimera.core.exceptions     import ClassLoaderException

class Simple (ChimeraObject):

    def __init__ (self):
        ChimeraObject.__init__(self)

    def answer (self):
        return 42


class NotValid (object): pass
             
class TestManager (object):

    def setup (self):
        self.manager = Manager()

    def teardown (self):
        self.manager.shutdown()
        del self.manager

    def test_add_start (self):

        # add by class
        assert isinstance(self.manager.addClass(Simple, "simple"), Proxy)

        # already started
        assert_raises(InvalidLocationException, self.manager.addClass, Simple, "simple")
       
        assert_raises(NotValidChimeraObjectException, self.manager.addClass, NotValid, "nonono")
        assert_raises(InvalidLocationException, self.manager.addClass, Simple, "")

        # by location
        assert isinstance(self.manager.addLocation('/ManagerHelper/h', path=[os.path.dirname(__file__)]), Proxy)
        assert_raises(ClassLoaderException, self.manager.addLocation, '/What/h')
        assert_raises(InvalidLocationException, self.manager.addLocation, 'foo')

        ## start with error
        #assert self.manager.addLocation('/ManagerHelperWithError/h')
        #assert_raises(ChimeraObjectException, self.manager.start, '/ManagerHelperWithError/h')

        # start who?
        assert_raises(InvalidLocationException, self.manager.start, "/Who/am/I")

        # exceptional cases
        # __init__
        assert_raises(ChimeraObjectException, self.manager.addLocation,
                                             "/ManagerHelperWithInitException/h",
                                             [os.path.dirname(__file__)])

        # __start__
        assert_raises(ChimeraObjectException, self.manager.addLocation,
                                             "/ManagerHelperWithStartException/h",
                                             [os.path.dirname(__file__)])

        # __main__
        #assert_raises(ChimeraObjectException, self.manager.addLocation, "/ManagerHelperWithMainException/h")
        

    def test_remove_stop (self):

        assert isinstance(self.manager.addClass(Simple, "simple"), Proxy)

        # who?
        assert_raises(InvalidLocationException, self.manager.remove, 'Simple/what')
        assert_raises(InvalidLocationException, self.manager.remove, 'foo')

        # stop who?
        assert_raises(InvalidLocationException, self.manager.stop, 'foo')

        # ok
        assert self.manager.remove('/Simple/simple') == True

        # __stop__ error
        assert isinstance(self.manager.addLocation("/ManagerHelperWithStopException/h",
                                                   path=[os.path.dirname(__file__)]), Proxy)

        assert_raises(ChimeraObjectException, self.manager.stop, '/ManagerHelperWithStopException/h')

        # another path to stop
        assert_raises(ChimeraObjectException, self.manager.remove, '/ManagerHelperWithStopException/h')

        # by index
        assert self.manager.addClass(Simple, "simple")
        assert self.manager.remove('/Simple/0') == True
