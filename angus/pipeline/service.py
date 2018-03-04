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

from multiprocessing import Process, Queue as MPQueue, Event
import os
import time
from collections import deque
import Queue
import logging

import angus.honorata

class ServiceState(object):
    '''Manage a service state
    '''
    RUNNING_FULL = "RUNNING_FULL"
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    TERMINATING = "TERMINATING"
    TERMINATED = "TERMINATED"

    _LEVEL = {
        RUNNING_FULL: logging.WARNING,
        # default: logger.INFO
    }

    def __init__(self, logger):
        self._status = self.STARTING
        self.logger = logger

    def update(self, new_state, cause=None):
        '''Update the current state
        '''
        if self._status == new_state:
            return

        level = self._LEVEL.get(new_state, logging.INFO)
        msg = "Change state from {} to {}".format(self._status, new_state)
        if cause is not None:
            msg = "{}, caused by: {}".format(msg, cause)

        self.logger.log(level, msg)
        self._status = new_state


class Service(Process):

    def __init__(self, *args, **kwargs):
        previous = kwargs.pop("previous", None)

        super(Service, self).__init__()
        self.daemon = True
        if previous is None:
            self.qinput = None
        else:
            self.qinput = previous.qoutput

        self.qoutput = MPQueue(30)
        self.exit = Event()

        self.logger = None # Place holder for the child logger
        self.status = None # Place holder for the child status

    def send_command(self, command):
        '''Send a command from parent to child service
        '''
        pass

    def get_state(self):
        '''Retrieve the service state
        '''
        pass

    def _initialize(self):
        '''Initialization of the service just after forking in the child
        '''
        angus.honorata.setup_logging()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.status = ServiceState(self.logger)
        self.logger.info("My pid is %s", os.getpid())

    def _finalize(self):
        '''Finalization of the service just in the child process
        '''
        if self.qinput is not None:
            while True: # empty the input queue before stops
                try:
                    self.qinput.get_nowait()
                except Queue.Empty:
                    break
                except IOError:
                    print "Error on windows"
                    break
            self.qinput.close()
            self.qinput = None

        if self.qoutput is not None:
            self.qoutput.put(None)
            self.qoutput.close()
            self.qoutput = None

    def shutdown(self):
        '''Stop service
        '''
        self.exit.set()

    def main(self):
        '''The main method to be implemented
        '''
        pass

    def run(self):
        '''The main process, set logger, initialize the child process
        '''
        self._initialize()
        self.status.update(ServiceState.RUNNING)
        self.main()
        self.status.update(ServiceState.TERMINATING)
        self._finalize()
        self.status.update(ServiceState.TERMINATED)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__str__()

class LoopService(Service):
    '''A service with a main loop
    '''
    CMD_GET_STATE = "__get_state__"

    def __init__(self, *args, **kwargs):
        self.max_fps = kwargs.pop("max_fps", None)
        super(LoopService, self).__init__(*args, **kwargs)
        self.periods = deque(maxlen=10)
        self.miss = deque(maxlen=60)
        self.command = MPQueue(5)
        self.state_queue = MPQueue(1)

    def send_command(self, command):
        self.command.put(command)

    def get_state(self):
        self.send_command(self.CMD_GET_STATE)
        try:
            state = self.state_queue.get(timeout=2)
        except Queue.Empty:
            return None
        return state

    def execute(self, command):
        '''Execute the send command in the child process
        '''
        pass

    def process_state(self):
        '''Return the computed state
        '''
        pass

    def process(self, message=None):
        '''Process one message
        '''
        pass

    def initialize(self):
        '''The public initializer of the service, to be overrided
        '''
        pass

    def finalize(self):
        '''The public finalizer of the service, to be overrided
        '''
        pass

    @property
    def frequence(self):
        '''Compute the current frequency of the main loop
        '''
        return len(self.periods)/sum(self.periods)

    def _wait(self, process_time):
        '''Try to force a main loop frequency
        '''
        if self.max_fps is not None:
            delay = 1/float(self.max_fps) - process_time
            if delay > 0.:
                time.sleep(delay)

    def run(self):
        '''Setup the main process with the loop to process messages
        '''
        self._initialize()
        self.initialize()
        self.status.update(ServiceState.RUNNING)
        while not self.exit.is_set():
            try:
                start = time.time()
                try:
                    cmd = self.command.get_nowait()
                    if cmd == self.CMD_GET_STATE:
                        self.state_queue.put_nowait(self.process_state())
                    elif cmd is not None:
                        self.execute(cmd)
                except Queue.Empty:
                    pass
                except Queue.Full:
                    pass

                if self.qinput is not None:

                    msg = self.qinput.get()
                    if msg is None:
                        break
                    contrib = self.process(msg)
                else:
                    msg = dict()
                    contrib = self.process()

                if contrib is not None:
                    msg.update(contrib)

                try:
                    self.qoutput.put_nowait(msg)
                    self.miss.append(0)
                except Queue.Full:
                    self.miss.append(1)

                stop = time.time()
                self._wait((stop-start))
                stop = time.time()
                self.periods.append((stop-start))

                # If there are some results dropped in the last n loops
                # Change state
                if sum(self.miss) > 0:
                    cause = "next service is busy, some results are dropped ({} loop/s)".format(self.frequence)
                    self.status.update(ServiceState.RUNNING_FULL, cause)
                else:
                    self.status.update(ServiceState.RUNNING)
            except KeyboardInterrupt:
                break
        self.status.update(ServiceState.TERMINATING)
        self._finalize()
        self.finalize()
        self.status.update(ServiceState.TERMINATED)
