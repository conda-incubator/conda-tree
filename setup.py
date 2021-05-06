#!/usr/bin/env python

from setuptools import setup
import shutil


# we need to rename the script because it's not a valid module name
shutil.copyfile('conda-tree.py', 'conda_tree.py')

setup(name='conda-tree',
      version='0.1.1',
      description='conda dependency tree helper',
      author='Renan Valieris',
      url='https://github.com/rvalieris/conda-tree',
      py_modules=['conda_tree'],
      entry_points={
        'console_scripts': ['conda-tree=conda_tree:main']})
