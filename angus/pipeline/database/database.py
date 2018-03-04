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

import sqlite3 as lite
import sys

class Database(object):
    def __init__(self):
        self.name = './honorata.db'
        try:
            connect = lite.connect(self.name)
            cursor = connect.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS pipes(" +
                           ",".join([
                               "id TEXT PRIMARY KEY",
                               "type TEXT",
                               "placement TEXT, "
                               "max_fps INT",
                               "video TEXT",
                               "client_id TEXT",
                               "access_token TEXT",
                               "auto_start INT",
                               "template TEXT",
                               "name TEXT UNIQUE",
                               ]) +
                           ");")
            connect.commit()
        except lite.Error, exception:

            print "Error database %s:" % exception.args[0]
            sys.exit(1)
        finally:

            if connect:
                connect.close()

    def _get_pipes(self):
        '''Get all pipes
        '''
        data = []
        try:
            connect = lite.connect(self.name)
            connect.row_factory = lite.Row
            cursor = connect.cursor()
            cursor.execute("SELECT * FROM pipes")
            pipes = cursor.fetchall()

            data = pipes
        except lite.Error, exception:

            print "Error %s:" % exception.args[0]
        finally:

            if connect:
                connect.close()

        return data

    def get_pipes(self):
        '''Get all pipes
        '''
        data = self._get_pipes()
        return data

    def create_pipe(self, pipe_data):
        ''' Create a new pipe in the database
        '''
        inserted = False
        try:
            connect = lite.connect(self.name)
            cursor = connect.cursor()
            cursor.execute("INSERT INTO pipes(" +
                           ",".join([
                               "id",
                               "type",
                               "placement",
                               "max_fps",
                               "video",
                               "client_id",
                               "access_token",
                               "auto_start",
                               "template",
                               "name",
                               ]) +
                           ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           pipe_data)
            connect.commit()
            inserted = True
        except lite.Error, exception:

            print "Error %s:" % exception.args[0]
        finally:

            if connect:
                connect.close()
        return inserted

    def update_pipe(self, pipe):
        '''Modify pipe data
        '''
        error = None
        try:
            connect = lite.connect(self.name)
            cursor = connect.cursor()
            cursor.execute("UPDATE Pipes SET auto_start=?, name=? WHERE id=?",
                           (pipe.auto_start, pipe.name, pipe.pid))
            connect.commit()

        except lite.Error, exception:
            error = exception.args[0]
            print "Error %s:" % error
        finally:

            if connect:
                connect.close()
        return error

    def delete_pipe(self, pid):
        '''Delete a pipe from the database
        '''
        deleted = True
        try:
            connect = lite.connect(self.name)
            cursor = connect.cursor()
            cursor.execute("DELETE FROM pipes WHERE id=?",
                           (pid,))
            connect.commit()

        except lite.Error, exception:
            deleted = False
            print "Error %s:" % exception.args[0]
        finally:

            if connect:
                connect.close()
        return deleted
