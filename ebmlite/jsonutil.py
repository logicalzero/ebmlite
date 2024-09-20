"""
Utilities for serializing EBML to JSON and back.
"""

import base64
from datetime import datetime
import json
from typing import Any, Dict

from . import core


# ===========================================================================
#
# ===========================================================================

def json2dict(data: str, schema: core.Schema) -> Dict[str, Any]:
    """ Decode a JSON string of a 'dumped' EBML `Document` into a `dict`,
        converting the values of `BinaryElement` and `DateElement` types:
        values of keys matching `DateElement` subclasses are converted from
        float to `datetime`, and `BinaryElement` subclasses are converted to
        `bytes`. `BinaryElement` values are decoded from base64 if the JSON
        string starts with `"base64:"`.

        :param data: The encoded JSON string.
        :param schema: The `ebmlite.Schema` to use to identify binary and
            date elements.
    """
    bins = ({v.name for v in schema.elements.values() if v.dtype is bytearray},
            lambda o: base64.b64decode(o[7:]) if o.startswith('base64:') else bytes(o))
    dates = ({v.name for v in schema.elements.values() if v.dtype is datetime},
             lambda o: datetime.utcfromtimestamp(o / 10**6))

    def hook(o):
        for names, converter in (bins, dates):
            for name in names.intersection(o):
                val = o[name]
                if isinstance(val, list):
                    o[name] = [converter(v) for v in val]
                else:
                    o[name] = converter(val)
        return o

    return json.loads(data, object_hook=hook)


def json2ebml(data: str, schema: core.Schema) -> core.Document:
    """ Decode a JSON string 'dumped' `ebmlite.Document` back into a
        `ebmlite.Document`.

        :param data: The encoded JSON string.
        :param schema: The schema of the resulting `ebmlite.Document`.
    """
    return schema.loads(schema.encodes(json2dict(data, schema)))


def ebml2json(doc: core.Document,
              void: bool = True,
              unknown: bool = True) -> str:
    """ Dump a Document's value as JSON. It is similar to `Document.dump()`,
        but `datetime.datetime` and `bytearray` values are safely
        encoded; `datetime.datetime` values are converted to float, and
        `bytearray` values are base64-encoded and given the prefix
        `"base64:"`.

        :param doc: The EBML `Document` to dump to JSON.
        :param void: If `False`, Void elements will be excluded from the
            resulting dictionary.
        :param unknown: If `False`, unknown elements will be excluded from
            the resulting dictionary.
    """
    class EBMLEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.timestamp()
            elif isinstance(o, (bytes, bytearray)):
                return 'base64:' + str(base64.b64encode(o), 'utf8')
            return super().default(o)

    return EBMLEncoder().encode(doc.dump(void, unknown))
