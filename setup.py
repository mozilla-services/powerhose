# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()


requires = ['pyzmq', 'circus']


setup(name='powerhose',
      version='0.2',
      packages=find_packages(),
      include_package_data=True,
      description='Implementation of the Request-Reply Broken pattern in ZMQ',
      long_description=README + '\n\n' + CHANGES,
      zip_safe=False,
      license='MPLv2.0',
      classifiers=[
        "Programming Language :: Python",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"
      ],
      install_requires=requires,
      author='Mozilla Services',
      author_email='services-dev@mozilla.org',
      url='https://github.com/mozilla-services/powerhose',
      test_requires=['nose'],
      test_suite = 'nose.collector',
      entry_points="""
      [console_scripts]
      powerhose-broker = powerhose.broker:main
      powerhose-worker = powerhose.worker:main
      powerhose = powerhose:main
      """)
