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

import StringIO
import numpy as np

import cv2

import angus.client
from angus.pipeline import LoopService

class SceneAnalysisClient(LoopService):
    def __init__(self, *args, **kwargs):
        self.endpoint = kwargs.pop("endpoint", "https://gate.angus.ai")
        self.client_id = kwargs.pop("client_id", None)
        self.access_token = kwargs.pop("access_token", None)

        super(SceneAnalysisClient, self).__init__(*args, **kwargs)
        self.service = None

    def connect(self):
        if self.client_id and self.access_token:
            client = angus.client.connect(
                url=self.endpoint,
                client_id=self.client_id,
                access_token=self.access_token
            )
        else:
            client = angus.client.connect()
        self.service = client.services.get_service("scene_analysis", version=1)
        self.service.enable_session()

    def initialize(self):
        self.connect()

    def process(self, message=None):
        frame = message.get("frame", None)
        timestamp = message.get("timestamp", None)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, buff = cv2.imencode(".jpg", gray, [cv2.IMWRITE_JPEG_QUALITY, 80])
        buff = StringIO.StringIO(np.array(buff).tostring())

        res = self.service.process({
            "image": buff,
            "timestamp" : timestamp.isoformat(),
        }).result

        # Work on a copy
        frame = frame.copy()

        if "error" in res:
            self.logger.error(res["error"])
        else:
            # This parses the events
            if "events" in res:
                for event in res["events"]:
                    value = res["entities"][event["entity_id"]][event["key"]]
                    self.logger.info("%s| %s, %s",
                                     event["type"],
                                     event["key"],
                                     value)

            # This parses the entities data
            for _, val in res["entities"].iteritems():
                x, y, dx, dy = map(int, val["face_roi"])
                cv2.rectangle(frame, (x, y), (x+dx, y+dy), (0, 255, 0), 2)


        return {
            "ar_frame": frame
        }
