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

"""
Help to interface with uvc camera.
"""
import os
import json
import logging
try:
    from pyv4l2.control import Control
except:
    pass

LOGGER = logging.getLogger(__name__)

class VideoDevice(object):
    def __init__(self, device):
        self.device = device
        try:
            self.control = Control(device)
        except:
            self.control = None

    def _retro_link(self, root):
        devices = os.listdir(root)
        for device in devices:
            path = os.readlink(os.path.join(root, device))
            path = os.path.join(root, path)
            if os.path.abspath(self.device) == os.path.abspath(path):
                return device
        return None

    @property
    def path(self):
        """
        Try to find a unique method to identify a webcam
        """
        return self._retro_link("/dev/v4l/by-path")

    @property
    def uid(self):
        """
        Try to find an uid.
        """
        return self._retro_link("/dev/v4l/by-id")

    @property
    def index(self):
        """
        Return the index of the device.
        """
        return int(self.device[len("/dev/video"):])

    @property
    def controls(self):
        """
        Return a list of available controls.
        """
        if self.control:
            return self.control.get_controls()
        return []

    def set(self, control_id, value):
        if self.control:
            self.control.set_control_value(control_id, value)

    def get(self, control_id):
        if self.control:
            return self.control.get_control_value(control_id)
        return ""

    def to_json(self):
        return {
            "device": self.device,
            "index": self.index,
            "uid": self.uid,
            "path": self.path,
        }



class FakeDevice(object):
    """
    For test, use video file
    """
    def __init__(self, path):
        self.file_path = path
        self.path = path
        self.uid = os.path.basename(path)
        self.index = path
        self._controls = list()
        self.mapping = None

class Controller(object):
    """
    Set automatic to True for a automatic refresh.
    """
    def __init__(self, automatic=False):
        self.automatic = automatic
        self._devices = None

    def refresh_devices(self):
        """
        Force to compute the list of available devices.
        """
        dev = "/dev/"
        video = "video"
        paths = [os.path.join(dev, f) for f in os.listdir(dev) if f[:len(video)] == video]

        self._devices = [VideoDevice(path) for path in paths]

    @property
    def devices(self):
        """
        Get the list of available devices.
        """
        if self.automatic or self._devices is None:
            self.refresh_devices()
        return self._devices

    def get(self, **kwargs):
        """
        Get a specific device by "path", "index" or "uid".
        """
        if 'index' in kwargs:
            index = kwargs.get('index')
            devices = [d for d in self.devices if d.index == index]
        elif 'uid' in kwargs:
            uid = kwargs.get('uid')
            devices = [d for d in self.devices if d.uid == uid]
        elif 'path' in kwargs:
            path = kwargs.get('path')
            devices = [d for d in self.devices if d.device == path]

        if len(devices) == 1:
            return devices[0]

        raise Exception("No such camera")


def main():
    """
    By default the module list all available devices.
    """
    controller = Controller()
    for device in controller.devices:
        stg = json.dumps({
            "device": device.device,
            "index": device.index,
            "uid": device.uid,
            "path": device.path,
            }, indent=4)
        print(stg)

if __name__ == '__main__':
    main()
