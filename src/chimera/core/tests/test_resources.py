import os

from nose.tools import assert_raises

from chimera.core.resources import Resource, ResourceManager
from chimera.core.exceptions import InvalidLocationException, ObjectNotFoundException


class TestResources(object):

    def __init__(self):
        self.res = None

    def setup (self):
        self.res = ResourceManager("localhost", 6379)
        self.res.removeAll()

    def test_add (self):

        assert len (self.res) == 0

        r1 = self.res.add("/Location/l1")
        assert isinstance(r1, Resource)
        assert len(self.res) == 1

        # location already added
        assert_raises(InvalidLocationException, self.res.add, "/Location/l1")

        r2 = self.res.add ("/Location/l2")
        assert isinstance(r2, Resource)
        assert len(self.res) == 2
        
        assert_raises(InvalidLocationException, self.res.add, "wrong location")

        assert "/Location/l1" in self.res
        assert "/Location/l2" in self.res
        assert "/Location/0" in self.res
        assert not "/LocationNotExistent/l2" in self.res

        r3 = self.res.add("/Location/h_f5167765-a784-4ecf-80fd-1dfb859339c7")
        assert isinstance(r3, Resource)
        assert len(self.res) == 3


    def test_remove (self):
        self.res.add ("/Location/l1")
        assert len(self.res) == 1

        assert self.res.remove ("/Location/l1") == True
        assert "/Location/l1" not in self.res
        assert len(self.res) == 0

    def test_remove (self):
        self.res.add ("/Location/l1")
        self.res.add ("/Location/l2")
        assert len(self.res) == 2

        assert self.res.remove ("/Location/l1") == True
        assert self.res.remove ("/Location/l2") == True
        assert "/Location/l1" not in self.res
        assert "/Location/l2" not in self.res
        assert len(self.res) == 0

    def test_get (self):
        self.res.add ("/Location/l2")
        self.res.add ("/Location/l1")
        self.res.add("/Location/h_f5167765-a784-4ecf-80fd-1dfb859339c7")

        ret = self.res.get("/Location/h_f5167765-a784-4ecf-80fd-1dfb859339c7")
        assert ret.location == "/Location/h_f5167765-a784-4ecf-80fd-1dfb859339c7"

        assert_raises(ObjectNotFoundException, self.res.get, "/Location/l99")

        # get using subscription
        assert self.res["/Location/l1"].location == "/Location/l1"
        assert_raises(KeyError, self.res.__getitem__, "/LocationNotExistent/l1")
        assert_raises(KeyError, self.res.__getitem__, "wrong location")        

        # get by index
        assert self.res.get("/Location/0").location == "/Location/l2"
        assert self.res.get("/Location/1").location == "/Location/l1"
        assert_raises(ObjectNotFoundException, self.res.get, '/Location/9')
        assert_raises(ObjectNotFoundException, self.res.get, '/LocationNotExistent/0')
        assert_raises(InvalidLocationException, self.res.get, 'wrong location')

    def test_get_by_class (self):
        self.res.add ("/Location/l1")
        self.res.add ("/Location/l2")

        entries = [self.res.get ("/Location/l1"), self.res.get ("/Location/l2")]

        # get by class
        found = self.res.getByClass ("Location")

        print entries
        print found
        
        assert (entries == found)


    def test_get_by_class_and_bases (self):
        tests_dir = os.path.abspath(os.path.dirname(__file__))
        
        self.res.add ("/ResourcesHelperA/a", loader_path=[tests_dir])
        self.res.add ("/ResourcesHelperB/b", loader_path=[tests_dir])

        self.res.add ("/ResourcesHelperA/aa", loader_path=[tests_dir])
        self.res.add ("/ResourcesHelperB/bb", loader_path=[tests_dir])

        entries = [
            self.res.get ("/ResourcesHelperA/a"), self.res.get ("/ResourcesHelperB/b"),
            self.res.get ("/ResourcesHelperA/aa"), self.res.get ("/ResourcesHelperB/bb")]

        # get by class
        found = self.res.getByClass ("ResourcesHelperBase")

        assert (entries == found == self.res.getAll())
