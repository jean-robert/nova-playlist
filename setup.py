from distutils.core import setup
from setuptools import find_packages

setup(name='nova-playlist',
      version='0.4.0',
      author='Guillaume Thomas',
      author_email='guillaume.thomas642@gmail.com',
      license='LICENCE.txt',
      description='Nova playlist',
      url='https://github.com/jean-robert/nova-playlist',
      install_requires=map(lambda line: line.strip("\n"),
                           open("requirements.txt", "r").readlines()),
      include_package_data=True,
      packages=find_packages(),
      )
