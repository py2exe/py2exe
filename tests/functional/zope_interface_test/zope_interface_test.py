# Source: https://stackoverflow.com/a/2521650

from zope.interface import Interface, Attribute, implementer
from zope.interface.verify import verifyObject, verifyClass

class IFoo(Interface):
    x = Attribute("The X attribute")
    y = Attribute("The Y attribute")

@implementer(IFoo)
class Foo(object):
    x = 1
    def __init__(self):
        self.y = 2

assert verifyObject(IFoo, Foo())
assert verifyClass(IFoo, Foo)
