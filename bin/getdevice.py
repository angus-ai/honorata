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

import os

import win_devices

def main():
    devices = win_devices.get_devices()

    try:
        with open("device.ini", "r") as f:
            default_index = int(f.read())
    except Exception as e:
        default_index = 0

    available = []
    for device in devices:
        index = device[0]
        available.append(str(index))
        name = device[1]
        info = "[DEFAULT]" if index == default_index else ""
        print("{}){} {}".format(index, info, name))

    if len(devices) == 0:
        raw_input("No webcam available, please press [ENTER]")
        index = ""
    else:
        index = raw_input("Please select your input: ")
        index = int(index) if index in available else default_index
        index = str(index)

    with open("device.ini", "w") as f:
        f.write(index)

if __name__ == "__main__":
    main()
