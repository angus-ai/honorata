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

'''
A dummy plugin to demonstrate how to extend honorata
'''

from angus.pipeline.service import LoopService
from angus.pipeline.services.decompressor import Decompressor
from angus.pipeline.admin import Template

class DummyService(LoopService):
    def __init__(self, *args, **kwargs):
        self.video = kwargs.pop("video", "unknown")

    def compute(self, message):
        self.logger.info("Receive a new message length %s from decompressor run on %s",
                         len(message),
                         self.video)

def templates():
    """
    Return new pipe templates to add to the pipe manager
    """
    return [
        Template("dummy", [
            Decompressor,
            DummyService,
        ])
    ]
