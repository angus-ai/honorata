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

import logging
import multiprocessing
import signal

import pkg_resources

import tornado.ioloop
import tornado.web

import angus.honorata
from angus.pipeline.database.database import Database
import angus.pipeline.admin
import webbrowser

LOGGER = logging.getLogger("Honorata")

class Controller(object):
    def __init__(self, app):
        self.app = app
        self.is_closing = False

    def try_exit(self):
        if self.is_closing:
            LOGGER.info('Shutting down gracefully Honorata...')
            self.app.pipe_manager.shutdown_all()
            tornado.ioloop.IOLoop.current().stop()

    def signal_handler(self, signum, frame):
        self.is_closing = True

def main():
    multiprocessing.freeze_support()

    angus.honorata.setup_logging()

    plugins = {
        entry_point.name: entry_point.load()
        for entry_point
        in pkg_resources.iter_entry_points('honorata.plugins.templates')
    }

    templates = list()
    for plugin_name, get_templates in plugins.iteritems():
        LOGGER.info("Extend templates from %s", plugin_name)
        templates.extend(get_templates())

    app = angus.pipeline.admin.Application(db=Database(), templates=templates)

    controller = Controller(app)

    signal.signal(signal.SIGINT, controller.signal_handler)

    app.logger.info("Webserver listening on port 8888")

    app.listen(8888)
    tornado.ioloop.PeriodicCallback(controller.try_exit, 100).start()
    tornado.ioloop.IOLoop.current().add_callback(lambda: webbrowser.open("http://localhost:8888"))
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()
