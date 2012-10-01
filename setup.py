from setuptools import setup
from os import path

f = open(path.join(path.dirname(__file__), 'README'))
long_description = f.read().strip()
f.close()

f = open(path.join(path.dirname(__file__), 'requirements.txt'))
install_requires = f.read().strip()
f.close()

setup(
    name='ThingDoc',
    version='1.0',
    description='ThingDoc is a clever things comment parser.',
    long_description=long_description,
    license='GNU GPLv3',
    author='Josef Prusa',
    author_email='iam@josefprusa.cz',
    url='https://github.com/josefprusa/ThingDoc',
    packages = ['thingdoc'],
    scripts=['bin/thingdoc'],
    install_requires=install_requires,
    include_package_data = True,
    zip_safe = False,
)

