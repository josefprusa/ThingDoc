from setuptools import setup
from os import path
import imp

base = path.dirname(__file__)

f = open(path.join(base, 'README'))
long_description = f.read().strip()
f.close()

f = open(path.join(base, 'requirements.txt'))
install_requires = f.read().strip()
f.close()

f = open(path.join(base, 'thingdoc', 'version.py'))
version = imp.new_module('version')
exec(f.read(), version.__dict__)
f.close()

setup(
    name='ThingDoc',
    version=version.__versionstr__,
    description='ThingDoc is a clever things comment parser.',
    long_description=long_description,
    license='GNU GPLv3',
    author='Josef Prusa',
    author_email='iam@josefprusa.cz',
    url='https://github.com/josefprusa/ThingDoc',
    packages=['thingdoc'],
    entry_points={'console_scripts': ['thingdoc = thingdoc.main:main']},
    install_requires=install_requires,
    include_package_data=True,
    zip_safe=False,
)

