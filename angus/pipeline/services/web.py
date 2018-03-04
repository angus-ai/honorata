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

import Queue
from threading import Thread, Event

import tornado.web
import tornado.ioloop
import tornado.gen
from tornado.locks import Condition

import cv2

from angus.pipeline import Service

class Watchdog(tornado.ioloop.PeriodicCallback):
    '''Watch to stop the main ioloop when exit
    '''
    def __init__(self, exit_event, frame_grabber):
        super(Watchdog, self).__init__(self.check, 1000)
        self.exit = exit_event
        self.frame_grabber = frame_grabber

    def check(self):
        ''' Check if event exit is set.
        Stop the main ioloop if it is true.
        '''
        if self.exit.is_set():
            self.frame_grabber.shutdown()
            self.frame_grabber.join()
            tornado.ioloop.IOLoop.current().stop()

class FrameGrabber(Thread):
    '''Watch if a new frame is coming
    '''
    def __init__(self, messages):
        super(FrameGrabber, self).__init__()
        self.messages = messages
        self.notifier = Condition()
        self.frame = None
        self.to_exit = Event()

    def shutdown(self):
        ''' Stop the thread
        '''
        self.to_exit.set()

    def run(self):
        while not self.to_exit.is_set():
            try:
                message = self.messages.get(True, 1)
                if message is None:
                    break
                frame = message.get("ar_frame", None)
                if frame is None:
                    continue
                _, frame = cv2.imencode(".jpg",
                                        frame,
                                        [cv2.IMWRITE_JPEG_QUALITY, 80])
                frame = frame.tostring()
                self.frame = frame
                self.notifier.notify()
            except Queue.Empty:
                continue

class FrameHandler(tornado.web.RequestHandler):
    """Produce results as a multipart stream.
    """
    def initialize(self, frame_handler):
        #pylint: disable=arguments-differ
        """Initialize the handler.
        """
        self.up = True
        self.frame_handler = frame_handler

    @tornado.gen.coroutine
    def get(self):
        #pylint: disable=arguments-differ
        """Stream output results.
        """
        self.set_header('Content-Type',
                        'multipart/x-mixed-replace;boundary=--myboundary')

        while self.up:
            frame = self.frame_handler.frame
            if frame is None:
                # Wait a first frame
                yield tornado.gen.sleep(0.5)
                continue

            response = "\r\n".join(("--myboundary",
                                    "Content-Type: image/jpeg",
                                    "Content-Length: " + str(len(frame)),
                                    "",
                                    frame,
                                    ""))
            self.write(response)
            yield self.flush()
            yield self.frame_handler.notifier.wait()

    def on_connection_close(self):
        """Exit when connection close.
        """
        self.up = False


class FrameServer(Service):
    '''A service that run a mjpeg server with incoming message
    '''
    def __init__(self, *args, **kwargs):
        self.port = kwargs.pop("port", 0)
        super(FrameServer, self).__init__(*args, **kwargs)

    def main(self):
        tornado.ioloop.IOLoop.current().clear_instance()
        tornado.ioloop.IOLoop.clear_current()
        tornado.ioloop.IOLoop.instance()

        frame_handler = FrameGrabber(self.qinput)
        frame_handler.start()

        Watchdog(self.exit, frame_handler).start()

        app = tornado.web.Application([
            (r"/", FrameHandler, dict(frame_handler=frame_handler)),
        ])

        app.listen(self.port)
        tornado.ioloop.IOLoop.current().start()
