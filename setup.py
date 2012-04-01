import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()


requires = ['pyzmq', 'circus']


setup(name='powerhose',
      version='0.1',
      packages=find_packages(),
      include_package_data=True,
      long_description=README + '\n\n' + CHANGES,
      zip_safe=False,
      install_requires=requires,
      author='Mozilla Services',
      author_email='services-dev@mozilla.org',
      url='https://github.com/mozilla-services/cornice',
      entry_points="""
      [console_scripts]
      powerhose-broker = powerhose.broker:main
      powerhose-worker = powerhose.worker:main
      powerhose = powerhose:main
      """)
