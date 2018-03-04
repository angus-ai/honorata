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

import datetime

import cv2
import pytz

from angus.pipeline import LoopService

class Decompressor(LoopService):
    def __init__(self, *args, **kwargs):
        self.video = kwargs.pop("video", 0)
        super(Decompressor, self).__init__(*args, **kwargs)

    def initialize(self):
        # pylint: disable=attribute-defined-outside-init
        self.cap = cv2.VideoCapture(self.video)
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.cv.CV_CAP_PROP_FPS, 10)
        self.remain_try = 5

    def process(self):
        # pylint: disable=arguments-differ
        if not self.cap.isOpened():
            self.shutdown()

        frame = self.cap.read()[1]

        if frame is None:
            if self.remain_try == 0:
                self.shutdown()
                return

            self.remain_try -= 1
            return

        timestamp = datetime.datetime.now(pytz.utc)

        return {
            "timestamp": timestamp,
            "frame": frame,
        }

    def finalize(self):
        self.cap.release()

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()
