from types import StringType

from nose.tools import assert_raises

from chimera.core.location   import Location
from chimera.core.exceptions import InvalidLocationException


class TestLocation(object):

    def test_create(self):

        # simple strings
        l = Location('/Class/name')
        assert l

        assert l.host is None
        assert l.port is None
        assert l.cls == "Class"
        assert l.name == "name"

        # simple strings
        l = Location('//host.com.br:1000/Class/name')
        assert l

        assert l.host == 'host.com.br'
        assert l.port == 1000
        assert l.cls == "Class"
        assert l.name == "name"

        # from dict
        assert_raises(InvalidLocationException, Location)
        assert_raises(InvalidLocationException, Location, cls="Class")
        assert_raises(InvalidLocationException, Location, name="name")
        assert_raises(InvalidLocationException, Location, cls="Class", name="")
        assert_raises(InvalidLocationException, Location, cls="", name="name")
        assert_raises(InvalidLocationException, Location, cls="", name="")
        
        assert Location(cls="Class", name="0")

        # simple version
        l = Location(cls="Class", name="name")
        assert l
        
        assert l.cls == "Class"
        assert l.name == "name"
        assert type(str(l)) == StringType        

        # host version
        l = Location(host='host.com.br', port=1000, cls="Class", name="name")
        assert l
        assert l.host == 'host.com.br'
        assert l.port == 1000
        assert l.cls == "Class"
        assert l.name == "name"
        assert type(str(l)) == StringType

        l = Location(host='host.com.br', cls="Class", name="name")
        assert l
        assert l.host == 'host.com.br'
        assert l.port is None
        assert l.cls == "Class"
        assert l.name == "name"
        assert type(str(l)) == StringType

        assert_raises(InvalidLocationException, Location, host='host.com.br', port="xyz",
                                                          cls="Class", name="name")

        # copy constructor
        l1 = Location('/Class/name')
        l2 = Location(l1)

        assert l1
        assert l2
        
        assert l2.cls == l1.cls
        assert l2.name == l1.name

        assert l2 == l1
        assert id(l2) != id(l1)


    def test_eq(self):

        l1 = Location('//host.com.br:1000/Class/name')
        l2 = Location('//othr.com.br:1001/Class/name')

        # equality tests apply only to class and name
        assert hash(l1) == hash(l2)
        assert l1 == l2

        l3 = Location('//host.com.br:1000/Class/name')
        l4 = Location('//host.com.br:1000/Class/othr')

        # equality tests apply only to class and name
        assert l3 != l4

    def test_valid(self):

        valid = ["/Class/other",
                 "/Class/1",
                 "/12345Class/o",
                 "//host.com.br:1000/Class/name",
                 "//host.com.br/Class/name",
                 '//200.100.100.100:1000/Class/name',
                 '//200.100.100.100/Class/name',
                 "  /  Class   /   other   ", # spaces doesn't matter anymore.
                 ":1000/Class/name", # no host, but still valid
                 Location("/Class/name"), # copy constructor
                 ]

        for l in valid:
            loc = Location (l)
            assert loc, "'%s' is not valid" % l

    def test_invalid(self):

        invalid = [
            "/Who/am/I"
        ]

        for l in invalid:
            assert_raises (InvalidLocationException, Location, l)