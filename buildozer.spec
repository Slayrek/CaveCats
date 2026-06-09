[app]

# (str) Title of your application
title = Paws and Pickaxes

# (str) Package name
package.name = pawsnpickaxes

# (str) Package domain (needed for android/ios packaging)
package.domain = org.test

# (str) Source code where the main.py is located
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,ogg,mp3,ttf,json

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
#source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
#source.exclude_dirs = tests, bin, venv

# (str) Application versioning
version = 1.1.0

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3.11, cython,  pygame==2.5.2

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = landscape

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (string) Presplash of the application
#presplash.filename = %(source.dir)s/pics/splash.png

# (string) Icon of the application
icon.filename = %(source.dir)s/pics/cat.png

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (str) Android NDK version to use
# android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid network timeouts or slow sdk updates
# android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only.
android.accept_sdk_license = True

# (str) Android entry point, default is ok for Kivy-based app
# for pygame apps, maybe:
# p4a.branch = master
# android.entrypoint = org.kivy.android.PythonActivity

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
