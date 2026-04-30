"""
Utilities for serializing EBML to JSON and back. Data types that cannot be
automatically serialized as JSON are converted into string forms that can,
with a prefix to indicate the encoding.

These are considered experimental.
"""

import base64
from datetime import datetime, timezone
import json
from typing import Any, Dict, Union

from ebmlite import core


__all__ = ("ebml2json", "json2ebml")


# ===========================================================================
#
# ===========================================================================

def escapedBytearray(value: Union[bytearray, bytes]) -> str:
    """ Utility function to convert binary data into JSON serializable strings.
    """
    return 'base64:' + str(base64.b64encode(value), 'utf8')


def escapedDatetime(value: datetime) -> str:
    """ Utility function to convert `datetime` objects into a JSON
        serializable form.
    """
    return f'time:{value.timestamp()}'


def unescapedBytearray(value: str) -> bytes:
    """ Utility function to deserialize serialized binary. """
    if value.startswith('base64:'):
        value = value[7:]
    return base64.b64decode(value)


def unescapedDatetime(value: str) -> datetime:
    """ Utility function to deserialize serialized `datetime` objects.
    """
    if value.startswith('time:'):
        value = value[5:]
    return datetime.fromtimestamp(float(value), tz=timezone.utc)


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
            value[i] = unescapedDatetime(v)
        elif isinstance(v, (dict, list)):
            unescapeDict(v)


class EscapedJSONEncoder(json.JSONEncoder):
    """ JSON encoder that converts `bytes`, `bytearray`, and `datetime`
        objects into serializable strings.
    """
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
            unescapedBytearray)
    dates = ({v.name for v in schema.elements.values() if v.dtype is datetime},
             unescapedDatetime)

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


def json2ebml(data: str, schema: core.Schema, headers: bool=False) -> core.Document:
    """ Decode a JSON string 'dumped' `ebmlite.Document` back into a
        `ebmlite.Document`.

        :param data: The encoded JSON string.
        :param schema: The schema of the resulting `ebmlite.Document`.
        :param headers: If `True`, include the standard ``EBML`` header
            element.
    """
    return schema.loads(schema.encodes(json2dict(data, schema), headers=headers))


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
