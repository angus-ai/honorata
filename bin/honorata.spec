# -*- mode: python -*-
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
from pkg_resources import iter_entry_points
import textwrap

block_cipher = None

VENV_PATH = os.environ.get("VIRTUAL_ENV")
SITE_PACKAGES = os.path.join(VENV_PATH, "Lib/site-packages")
SCRIPT_DIR = os.path.join(VENV_PATH, "Scripts")

ANGUS_MODULE = os.path.join(SITE_PACKAGES, "angus")

WEB_STATIC_PATH = "./pipeline/admin/static"
WEB_STATIC_FROM = os.path.join(ANGUS_MODULE, WEB_STATIC_PATH)
WEB_STATIC_TO = os.path.join("./angus", WEB_STATIC_PATH)

static_data = []
#
# Hook for plugins
#
all_commands = []
hiddenimports = []
for ep in iter_entry_points("honorata.plugins.templates"):
  ep.load() # Force to verify dependencies
  all_commands.append("{} = {}:{}".format(ep.name, ep.module_name, ep.attrs[0]))
  hiddenimports.append(ep.module_name)

with open("hook.py", "w") as f:
  f.write(textwrap.dedent("""
  import pkg_resources
  eps = {}
  # Do not use require, because no distribution
  class EntryPoint(pkg_resources.EntryPoint):
    def load(self, *args, **kwargs):
      return super(EntryPoint, self).load(False, *args, **kwargs)

  def iter_entry_points(group, name=None):
    for ep in eps:
      entry = EntryPoint.parse(ep)
      yield entry

  pkg_resources.iter_entry_points = iter_entry_points
  """.format(all_commands)))
#
# End of hook
#

for t in os.listdir(WEB_STATIC_FROM):
    real_path = os.path.join(WEB_STATIC_FROM, t)
    if not os.path.isdir(real_path):
        static_data.append((real_path, WEB_STATIC_TO))
    else:
        for p in os.listdir(real_path):
            static_data.append((os.path.join(real_path, p), os.path.join(WEB_STATIC_TO, t)))

honorata_a = Analysis(['honorata.py'],
             pathex=[
                SITE_PACKAGES,
                '..'
             ],
             binaries=[],
             datas=static_data + [
                ("honorata.bat", "")
             ],
             hiddenimports=['angus.pipeline'] + hiddenimports,
             hookspath=[],
             runtime_hooks=["hook.py"],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

getdevice_a = Analysis(['getdevice.py'],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

angusme_a = Analysis([os.path.join(SCRIPT_DIR, 'angusme')],
             pathex=[],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)

MERGE( (honorata_a, 'honorata', 'honorata'), (getdevice_a, 'getdevice', 'getdevice'), (angusme_a, 'angusme', 'angusme') )

honorata_pyz = PYZ(honorata_a.pure, honorata_a.zipped_data,
             cipher=block_cipher)

getdevice_pyz = PYZ(getdevice_a.pure, getdevice_a.zipped_data,
             cipher=block_cipher)

angusme_pyz = PYZ(angusme_a.pure, angusme_a.zipped_data,
             cipher=block_cipher)

honorata_exe = EXE(honorata_pyz,
          honorata_a.scripts,
          exclude_binaries=True,
          name='honorata',
          debug=False,
          strip=False,
          upx=True,
          console=True )

getdevice_exe = EXE(getdevice_pyz,
          getdevice_a.scripts,
          exclude_binaries=True,
          name='getdevice',
          debug=False,
          strip=False,
          upx=True,
          console=True )

angusme_exe = EXE(angusme_pyz,
          angusme_a.scripts,
          exclude_binaries=True,
          name='angusme',
          debug=False,
          strip=False,
          upx=True,
          console=True )

angusme_coll = COLLECT(angusme_exe,
               angusme_a.binaries,
               angusme_a.zipfiles,
               angusme_a.datas,
               strip=False,
               upx=True,
               name='angusme')

getdevice_coll = COLLECT(getdevice_exe,
               getdevice_a.binaries,
               getdevice_a.zipfiles,
               getdevice_a.datas,
               strip=False,
               upx=True,
               name='getdevice')

honorata_coll = COLLECT(honorata_exe,
               honorata_a.binaries,
               honorata_a.zipfiles,
               honorata_a.datas,
               strip=False,
               upx=True,
               name='honorata')
