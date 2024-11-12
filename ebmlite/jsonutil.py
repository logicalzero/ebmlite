"""
Utilities for serializing EBML to JSON and back.
These are considered experimental.
"""

import base64
from datetime import datetime
import json
from typing import Any, Dict, Union

from . import core


# ===========================================================================
#
# ===========================================================================

def escapedBytearray(value: Union[bytearray, bytes]) -> str:
    return 'base64:' + str(base64.b64encode(value), 'utf8')


def escapedDatetime(value: datetime) -> str:
    return f'time:{value.timestamp()}'


def unescapedBytearray(value: str) -> bytes:
    if value.startswith('base64:'):
        value = value[7:]
    return base64.b64decode(value)


def unescapeedDatetime(value: str) -> datetime:
    if value.startswith('time:'):
        value = value[5:]
    return datetime.utcfromtimestamp(float(value))


def escapeDict(value: Union[Dict[str, Any], list]):
    """ Convert `bytearray`/`bytes` and `datetime.datetime` values in a
        dictionary into strings that can be encoded as JSON.
    """
    if isinstance(value, list):
        iterator = enumerate(value)
    elif isinstance(value, dict):
        iterator = value.items()
    else:
        raise ValueError(f'cannot iterate {type(value)}')

    for k, v in iterator:
        if isinstance(v, (bytearray, bytes)):
            value[k] = escapedBytearray(v)
        elif isinstance(v, datetime):
            value[k] = escapedDatetime(v)
        elif isinstance(v, (list, dict)):
            escapeDict(v)


def unescapeDict(value: Union[Dict[str, Any], list]):
    """ Convert `bytearray`/`bytes` and `datetime.datetime` values
        escaped by `escapeDict()` back to their original form.
    """
    if isinstance(value, list):
        iterator = enumerate(value)
    elif isinstance(value, dict):
        iterator = value.items()
    else:
        raise ValueError(f'cannot iterate {type(value)}')

    for i, v in iterator:
        if v.startswith('base64:'):
            value[i] = unescapedBytearray(v)
        elif v.startswith('time:'):
            value[i] = unescapeedDatetime(v)
        elif isinstance(v, (dict, list)):
            unescapeDict(v)


class EscapedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return escapedDatetime(o)
        elif isinstance(o, (bytes, bytearray)):
            return escapedBytearray(o)
        return super().default(o)


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
            escapedBytearray)
    dates = ({v.name for v in schema.elements.values() if v.dtype is datetime},
             escapedDatetime)

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

    return EscapedJSONEncoder().encode(doc.dump(void, unknown))
