import os.path

from ebmlite import core, jsonutil

FILENAME = os.path.join(os.path.dirname(__file__), 'SSX46714-doesnot.IDE')


def test_json():
    schema = core.loadSchema('mide_ide.xml')
    doc = schema.load(FILENAME)

    serialized = jsonutil.ebml2json(doc)
    deserialized = jsonutil.json2ebml(serialized, schema)

    orig = doc.dump()
    read = deserialized.dump()

    assert deserialized is not doc
    assert orig is not read
    assert orig == read
