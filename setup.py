#!/usr/bin/env python

from setuptools import setup, find_packages
with open("README.md", "r") as fh:
    long_description = fh.read()

# install_requires = set()
# with open( "requirements/hyperclass.txt" ) as f:
#   for dep in f.read().split('\n'):
#       if dep.strip() != '' and not dep.startswith('-e'):
#           install_requires.add( dep )

setup(name='astrolab',
      version='0.0.1',
      description='Jupyterlab workbench supporting visual exploration and classification of astronomical xray and light curve data',
      author='Thomas Maxwell',
      zip_safe=False,
      author_email='thomas.maxwell@nasa.gov',
      url='https://github.com/nasa-nccs-cds/astrolab.git',
      long_description=long_description,
      long_description_content_type="text/markdown",
      packages=find_packages(),
#      install_requires=list(install_requires),
#      data_files=[ ('hyperclass/util', [ 'hyperclass/util/config_template.txt' ] ) ],
      classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)

