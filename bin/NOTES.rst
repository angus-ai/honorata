Windows Pyinstaller distribution building
-----------------------------------------

To generate a full windows dist go into ``./bin`` and run pyinstaller with ``honorata.spec``
Requirements:
* You must be in a virtualenv with installed honorata
* You must install pyinstaller ``pip install pyinstaller``
* You must install windevices ``pip install win-devices``

Helper is available:

``$> winbuild.bat honorata.spec``

All files are copied into ``./bin/dist/honorata``.
This directory is self-content, you can zip it and distribute.

To run complete process (credentials + webcam selection + honorata) please run ``honorata.bat``
