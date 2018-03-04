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
Manage data flow pipe through a web interface and APIs.
'''

import sys
import subprocess
import os
import re
import logging
import json
import uuid
import socket
from contextlib import closing

import tornado.ioloop
import tornado.web

from angus.webcam import Controller

STATIC = os.path.join(os.path.dirname(__file__), "static")
CURRENT_FRAMESERVER_PORT = 8777

STATUS_STOPPED = "stopped"
STATUS_STARTED = "started"


def default_repr(obj):
    if isinstance(obj, type):
        return obj.__name__
    return obj.__class__.__name__

def port_is_available(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        if sock.connect_ex((host, port)) == 0:
            return False
        else:
            return True

class PipesHandler(tornado.web.RequestHandler):
    # pylint: disable=abstract-method
    ''' API handler for pipe collections, enable creating
    them and get parameters.
    '''
    def initialize(self, pipes, db=None):
        #pylint: disable=arguments-differ
        self.pipes = pipes
        self.db = db

    def get(self):
        #pylint: disable=arguments-differ
        pipes = [{
            'id': p.pid,
            'type': p.type,
            'placement': p.placement,
            'video': p.parameters['video'],
            'client_id': p.parameters['client_id'],
            'access_token': p.parameters['access_token'],
            'auto_start': p.auto_start,
            'port': p.parameters['port'],
            'status': p.status,
            'template': p.template,
            'name': p.name,
        } for p in self.pipes.repository.values()]
        self.finish(json.dumps(pipes))

    def post(self):
        #pylint: disable=arguments-differ
        global CURRENT_FRAMESERVER_PORT
        body = json.loads(self.request.body)
        pipe_data = (str(uuid.uuid4()),
                     body.get("type", "usb"),
                     body.get("placement", "front"),
                     int(body.get("max_fps", 4)),
                     body.get("video", 0),
                     body.get("client_id", ""),
                     body.get("access_token", ""),
                     0,
                     body.get("template", "audience"),
                     None)
        inserted = False
        if self.db is not None:
            inserted = self.db.create_pipe(pipe_data)
        while not port_is_available("localhost", CURRENT_FRAMESERVER_PORT):
            CURRENT_FRAMESERVER_PORT += 1
        video = pipe_data[4]
        pipe = self.pipes.instanciate(pipe_data[8], {
            "video": int(video) if video.isdigit() else video,
            "max_fps": pipe_data[3],
            "port": CURRENT_FRAMESERVER_PORT,
            "client_id": pipe_data[5],
            "access_token": pipe_data[6],
        }, pipe_data)

        self.finish(
            {
                "pipe_id": pipe.pid,
                "video_port": CURRENT_FRAMESERVER_PORT,
            }
        )
        CURRENT_FRAMESERVER_PORT += 1


class PipeHandler(tornado.web.RequestHandler):
    # pylint: disable=abstract-method
    ''' API to manage one pipe
    '''
    def initialize(self, pipes):
        #pylint: disable=arguments-differ
        self.pipes = pipes

    def get(self, pid):
        #pylint: disable=arguments-differ
        try:
            pipe = self.pipes.repository[pid]
            description = {
                "id": pipe.pid,
                "services": pipe.services_classes,
                "params": pipe.parameters,
                "status": pipe.status,
                "states": pipe.state(),
            }
            self.set_status(200)
            self.set_header("Content-Type", "application/json; charset=UTF-8")
            self.finish(json.dumps(description, default=default_repr))
        except KeyError:
            self.set_status(404, "Pipe not found")
            self.finish()

    def put(self, pid):
        #pylint: disable=arguments-differ
        try:
            pipe = self.pipes.repository[pid]
            body = json.loads(self.request.body)
            status = body.get("status", None)
            auto_start = body.get("auto_start", None)
            name = body.get("name", None)
            if status == STATUS_STARTED:
                pipe.start()
            elif status == STATUS_STOPPED:
                pipe.shutdown()
            if auto_start is not None:
                pipe.auto_start = bool(auto_start)
            if name is not None:
                old_name = pipe.name
                pipe.name = name
            error = self.pipes.update_pipe(pipe)
            if error is not None:
                pipe.name = old_name
                self.set_status(400, error)
                self.finish()

        except KeyError:
            self.set_status(404, "Pipe not found")
            self.finish()

    def delete(self, pid):
        #pylint: disable=arguments-differ
        try:
            deleted = self.pipes.delete_pipe(pid)
            if deleted is not True:
                self.set_status(500)
                self.finish("An error occured")
            else:
                pipe = self.pipes.repository[pid]
                if pipe.status == STATUS_STARTED:
                    pipe.shutdown()
                del self.pipes.repository[pid]
                self.set_status(200)
                self.finish("Pipe deleted successfully")
        except KeyError:
            self.set_status(404, "Pipe not found")
            self.finish()

class Pipe(object):
    '''A pipe is a dataflow process
    '''
    def __init__(self, services_classes, parameters, data=None):
        if data:
            (self.pid,
            self.type,
            self.placement,
            max_fps,
            video,
            client_id,
            access_token,
            self.auto_start,
            self.template,
            self.name) = data
        else:
            self.pid = str(uuid.uuid4())
            self.type = "usb"
            self.placement = "front"
            self.auto_start = 0
            self.template = "audience"
            self.name = ""

        self.services = list()
        self.services_classes = services_classes
        self.status = STATUS_STOPPED
        self.parameters = parameters
        self.logger = logging.getLogger("Pipe-{}".format(self.pid))

    def start(self):
        '''Start the pipe
        '''
        previous = None
        for service in self.services_classes:
            parameters = self.parameters.copy()
            parameters["previous"] = previous
            previous = service(**parameters)
            self.services.append(previous)
        for service in self.services:
            service.start()
        self.status = STATUS_STARTED
        self.logger.info("Started successfully")

    def send(self, command):
        '''Send a command to all service
        '''
        for service in self.services:
            service.send_command(command)

    def state(self):
        '''Retrieve all service states
        '''
        states = {
            str(service.__class__.__name__): service.get_state()
            for service in self.services
        }
        return states

    def shutdown(self):
        '''Stop the pipe
        '''
        for service in self.services:
            params = self.parameters.get(service.__class__, dict())
            try:
                params.pop("previous")
            except KeyError:
                pass
            service.shutdown()
            service.join()
        self.services = list()
        self.status = STATUS_STOPPED
        self.logger.info("Stopped successfully")

class PipeManager(object):
    def __init__(self, db=None):
        self.db = db
        self.repository = dict() # uuid1 => Pipe
        self.templates = dict() # name => list(services_classes)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.pipes = dict() # id => pipes from db

    def _init_pipes(self):
        '''Initialize all previously defined pipe
        '''
        global CURRENT_FRAMESERVER_PORT
        for pipe in self.pipes:
            template = pipe["template"]
            while not port_is_available("localhost", CURRENT_FRAMESERVER_PORT):
                CURRENT_FRAMESERVER_PORT += 1
            video = pipe["video"]
            pipe_ = self.instanciate(template, {
                "video": int(video) if video.isdigit() else video,
                "max_fps": pipe["max_fps"],
                "port": CURRENT_FRAMESERVER_PORT,
                "client_id": pipe["client_id"],
                "access_token": pipe["access_token"],
            }, pipe)
            if pipe["auto_start"] is not 0:
                pipe_.start()
            CURRENT_FRAMESERVER_PORT += 1

    def load_from_db(self):
        '''Load save data from database
        '''
        if self.db is not None:
            self.pipes = self.db.get_pipes()
            if self.pipes is not None:
                self._init_pipes()

    def define_template(self, name, services_classes):
        '''Register a new template
        '''
        self.templates[name] = services_classes

    def instanciate(self, name, parameters, data_pipe=None):
        '''Instanciate a new pipe from template and parameters
        '''
        # FIXME: please protect unknown template
        pipe = Pipe(self.templates[name], parameters, data_pipe)
        self.repository[pipe.pid] = pipe
        return pipe

    def update_pipe(self, pipe):
        '''Update pipe parameter in db
        '''
        return self.db.update_pipe(pipe)

    def delete_pipe(self, pid):
        '''Delete a pipe in db
        '''
        return self.db.delete_pipe(pid)

    def start(self, pid):
        '''Start a pipe
        '''
        self.repository[pid].start()

    def shutdown(self, pid):
        '''Stop a pipe
        '''
        self.repository[pid].shutdown()

    def shutdown_all(self):
        '''Stop all pipes
        '''
        for pipe_id in self.repository:
            self.logger.info("Shutting down gracefully pipe %s", pipe_id)
            self.repository[pipe_id].shutdown()

class StreamsHandler(tornado.web.RequestHandler):
    # pylint: disable=abstract-method
    '''List the available video camera devices.
    '''

    def initialize(self, controller):
        #pylint: disable=arguments-differ
        self.controller = controller

    def get(self):
        #pylint: disable=arguments-differ
        if sys.platform == "win32":
            import win_devices
            devices = win_devices.get_devices()
            devices = {d[0]: {"index": d[0], "device": d[1]} for d in devices}
        elif sys.platform == "darwin":
            res = subprocess.check_output(["system_profiler", "SPCameraDataType"])
            cams = re.findall("\\n\\n    (\w.*):", res)
            devices = [(cam, {"index": i, "device": cam}) for i, cam in enumerate(cams)]
        else:
            devices = [(d.uid, d.to_json()) for d in self.controller.devices]
        self.finish(dict(devices))

class SignalHandler(tornado.web.RequestHandler):
    # pylint: disable=abstract-method
    '''API handler to send signals to pipes
    '''
    def initialize(self, pipes):
        #pylint: disable=arguments-differ
        self.pipes = pipes

    def put(self, pid, signal):
        #pylint: disable=arguments-differ
        self.pipes.repository[pid].send(signal)


class StateHandler(tornado.web.RequestHandler):
    # pylint: disable=abstract-method
    '''API handler to get back pipe states
    '''
    def initialize(self, pipes):
        #pylint: disable=arguments-differ
        self.pipes = pipes

    def get(self, pid, service_name):
        #pylint: disable=arguments-differ
        try:
            pipe = self.pipes.repository[pid]
            state = None
            services = pipe.services
            for service in services:
                name = str(service.__class__.__name__)
                if  name.lower() == service_name.lower():
                    state = {
                        name: service.get_state()
                    }
            if state is None:
                msg = "Service '{}' not found in pipe '{}'".format(service_name, pid)
                self.set_status(404, msg)
                self.finish()
            else:
                self.set_status(200)
                self.set_header("Content-Type",
                                "application/json; charset=UTF-8")
                self.finish(json.dumps(state, default=default_repr))

        except KeyError:
            self.set_status(404, "Pipe not found")
            self.finish()

class Template(object):
    def __init__(self, name, classes):
        self.name = name
        self.classes = classes

class Application(tornado.web.Application):
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = kwargs.pop("db", None)
        self.templates = kwargs.pop("templates", list())

        self.pipe_manager = PipeManager(self.db)
        for template in self.templates:
            self.pipe_manager.define_template(template.name, template.classes)

        self.pipe_manager.load_from_db()
        self.controller = Controller()
        urls = [
            (r"/streams", StreamsHandler, dict(controller=self.controller)),
            (r"/pipes", PipesHandler, dict(pipes=self.pipe_manager, db=self.db)),
            (r"/pipes/(.*)/(.*)/state", StateHandler, dict(pipes=self.pipe_manager)),
            (r"/pipes/(.*)", PipeHandler, dict(pipes=self.pipe_manager)),
            (r"/signal/(.*)/(.*)", SignalHandler, dict(pipes=self.pipe_manager)),
            (r"/", tornado.web.RedirectHandler, dict(url='/index.html')),
            (r"/(.*)", tornado.web.StaticFileHandler, { "path": STATIC }),
        ]

        if len(args) > 0:
            args[0][:0] = urls
        else:
            args = (urls,)

        super(Application, self).__init__(*args, **kwargs)
