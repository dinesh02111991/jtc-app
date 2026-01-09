[app]
# (str) Title of your application
title = MyApp

# (str) Package name
package.name = myapp

# (str) Package domain (reverse domain style)
package.domain = org.example

# (str) Source code where the main.py is located
source.dir = .

# (list) File extensions to include
source.include_exts = py,kv,png,jpg

# (list) Requirements
requirements = python3,kivy,sdl2, hostpython3, **kivymd**

# (str) Orientation
orientation = portrait

# (str) Version of your app
version = 1.0

# (str) SDL2 bootstrap (required for Android builds)
p4a.bootstrap = sdl2

# (int) Android API settings
android.api = 33
android.minapi = 21
android.ndk = 25b

# (str) Build tools version
android.build_tools_version = 36.1.0

# (bool) Skip SDK/NDK update (important for Docker image)
android.skip_update = True

# (int) Log level (0 to 2)
log_level = 2
