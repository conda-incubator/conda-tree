#!/usr/bin/env python

from setuptools import setup
import shutil


# we need to rename the script because it's not a valid module name
shutil.copyfile('conda-tree.py', 'conda_tree.py')

setup(name='conda-tree',
      version='1.0.3',
      description='conda dependency tree helper',
      author='Renan Valieris',
      url='https://github.com/rvalieris/conda-tree',
      py_modules=['conda_tree'],
      install_requires=[
          'networkx',
          'colorama'
      ],
      entry_points={
        'console_scripts': ['conda-tree=conda_tree:main']})
