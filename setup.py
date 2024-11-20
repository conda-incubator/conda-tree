#!/usr/bin/env python

from setuptools import setup
import shutil

# we need to rename the script because it's not a valid module name
shutil.copyfile('conda-tree.py', 'conda_tree.py')

pname = 'conda-tree'

exec(list(filter(
    lambda l: l.startswith("__version__"),
    open(pname+'.py').read().split("\n")
))[0])

setup(name=pname,
      version=__version__,
      description='conda dependency tree helper',
      author='Renan Valieris',
      url='https://github.com/conda-incubator/conda-tree',
      py_modules=['conda_tree'],
      install_requires=[
          'networkx',
          'colorama'
      ],
      entry_points={
        'console_scripts': ['conda-tree=conda_tree:main']})
