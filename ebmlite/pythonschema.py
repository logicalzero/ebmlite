import ebmlite.core


# ==========================================================================
#
# ==========================================================================

class PythonSchema(ebmlite.core.Schema):
    """ Base class for an EBML schema implemented in Python rather than
        generated from an XML file. Unlike the standard `Schema`, this
        one is a base class for Python-based schemata (i.e., those
        created with the `ebmlite.codegen` module).
    """
    source = None
    filename = None

    # noinspection PyMissingConstructor
    def __init__(self):
        """
        """
        self.document.schema = self
        self.elementsByName = {}
        self.elementInfo = {}
        for eid, etype in self.elements.items():
            self.elementsByName[etype.name] = etype
            etype.schema = self
            info = getattr(etype, '_info', None)
            if info:
                self.elementInfo[eid] = info

    def __repr__(self):
        return f'<{self.name or self.type!r} from {self.__module__!r}'
