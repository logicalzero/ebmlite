"""

"""

import textwrap
from typing import IO, List, Type
from .core import Element, MasterElement, Document, Schema


def writeDocstring(docs: str, width: int = 74) -> List[str]:
    """
    Format a documentation string as a set of wrapped quoted strings, for
    use in a class definition.

    :param docs: The docstring to render.
    :param width: Max line with. Note that this will be indented by
        4 spaces when used by other functions.
    :return: A list of substrings, including opening and closing
        triple-quotes.
    """
    if not docs:
        return []
    out = textwrap.wrap(docs.replace('"""', "'''"), width)
    return ['"""', *out, '"""']


def cleanName(name: str) -> str:
    """
    Sanitize (make valid) a string for use as a class name.

    :param name: The name to clean (e.g., an element name).
    :return: The valid name.
    """
    for c in '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~':
        name = name.replace(c, ' ')
    cleaned = ''
    for n in name.split():
        if n:
            cleaned += n[0].upper() + n[1:]
    return cleaned


def writeClass(element: Type[Element],
               docs=True) -> str:
    """
    Render a Python class defintion from an `Element` subclass.

    :param element: The element class to translate.
    :param docs: If `True`, include docstrings in the output.
    :return: A string containing the Python class definition.
    """
    bases = ', '.join(f'{c.__module__}.{c.__name__}'
                      for c in element.__bases__)
    sig = f'class {cleanName(element.__name__)}({bases}):\n'
    out = writeDocstring(element.__doc__) if docs and element.__doc__ else []
    out.append(f'__slots__ = {element.__slots__!r}')
    out.append(f'name = {element.name or element.__name__!r}')
    if Document not in element.__bases__:
        out.append(f'id = 0x{element.id:02X}')
        for attr in ('precache', 'mandatory', 'multiple', 'length'):
            out.append(f'{attr} = {getattr(element, attr)}')
        out.append(f'_info = {element.schema.elementInfo[element.id]!r}')

    if issubclass(element, MasterElement) and element.children:
        out.append(f'children = {element.children}')

    return sig + '\n'.join(f'    {line}' for line in out) + '\n\n\n'


def writeSchema(schema: Schema,
                docs=True):
    """
    Generate the code defining an EBML `Schema` as a Python class.

    :param schema: The loaded `Schema` instance to translate.
    :param docs: If `True`, include docstrings in the output.
    :return: A string containing the Python class definition.
    """
    sig = f"""class {cleanName(schema.type)}Schema(PythonSchema):\n"""
    globalels = []

    out = writeDocstring(schema.__doc__) if docs and schema.__doc__ else []
    out.append(f'name = {schema.name or schema.type!r}')
    out.append(f'type = {schema.type!r}')
    out.append(f'document = {cleanName(schema.document.__name__)}')
    out.append(f'unknown = ebmlite.core.UnknownElement')
    out.append('elements = {')
    for eid, etype in schema.elements.items():
        out.append(f'    0x{eid:02X}: {cleanName(etype.__name__)},')
        if eid in schema.globals:
            globalels.append(f'{eid}: {cleanName(etype.__name__)}')
    out.append('}')
    out.append(f'children = {schema.children}')

    out.append(f'globals = {{{", ".join(globalels)}}}')

    return sig + '\n'.join(f'    {line}' for line in out) + '\n'


def generateCode(out: IO, schema: Schema, docs=True):
    """
    Generate a Python file that explicitly defines given `Schema`
    and all its subclasses.

    :param out: The output stream to which to write the Python code.
    :param schema: The `Schema` to translate.
    :param docs: If `True`, include docstrings in the output.
    """
    out.write("import ebmlite.core\n\n")
    out.write("from ebmlite.pythonschema import PythonSchema\n\n\n")
    for eltype in schema.elements.values():
        out.write(writeClass(eltype, docs=docs))
    out.write(writeClass(schema.document, docs=docs))
    out.write(writeSchema(schema))
