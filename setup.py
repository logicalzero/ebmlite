import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()

setuptools.setup(
        name='ebmlite',
        version='0.0.0',
        description='A lightweight, "pure Python" library for parsing EBML (Extensible Binary Markup Language) data.'
)