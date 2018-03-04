#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from setuptools import setup, find_packages
import sys

__updated__ = "2018-02-23"
__author__ = "Aurélien Moreau"
__copyright__ = "Copyright 2017, Angus.ai"
__credits__ = [
    "Aurélien Moreau",
    "Gwennaël Gâté",
    "Raphaël Lumbroso",
    "Jean Testard",
    "Younes Iddahamou",
    "Ilyace Regaibi",
]

__license__ = "Apache v2.0"
__maintainer__ = "Aurélien Moreau"
__status__ = "Production"
__version__ = "1.4.0"

setup(name='honorata',
      version=__version__,
      description='Angus Honorata Client',
      author=__author__,
      author_email='aurelien.moreau@angus.ai',
      url='http://www.angus.ai/',
      install_requires=[
          "tornado >=4.5, <4.6",
          "requests >=2.18, <2.19",
          "angus-sdk-python >=0.0, <0.1",
          "pyyaml >=3.12, <3.13",
          "numpy >=1.12, <1.13",
          "pytz >=2018, < 2019",
      ] + ([
          "win-devices >= 0.0.0, <0.1.0",
      ] if sys.platform.startswith("win") else []),
      license=__license__,
      packages=find_packages(exclude=['tests']),
      entry_points={
          'honorata.plugins.templates': [
              'cloud_audience = angus.plugins.cloud_audience:templates',
          ]
      },
      package_data={
          "angus.pipeline.admin": [
              "static/*.html",
              "static/*.js",
              "static/*.css",
              "static/js/*.js",
              "static/css/*.css",
              "static/images/*.png",
          ],
      },
      scripts=[
          'bin/honorata.py',
          'bin/honorata.bat',
          ]
      )
