[app]
# (str) Title of your application
title = MyApp

# (str) Package name
package.name = myapp

# (str) Package domain (used in the package name)
package.domain = org.example

# (str) Source code directory
source.dir = .

# (list) File extensions to include
source.include_exts = py,kv,png,jpg

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation: portrait, landscape, all
orientation = portrait

# (str) Application version
version = 1.0

# (list) Permissions
#android.permissions = INTERNET

# (str) Android bootstrap method
p4a.bootstrap = sdl2

# (int) Android API to use
android.api = 33

# (int) Minimum API your app supports
android.minapi = 21

# (str) Android NDK version
android.ndk = 25b

# (list) Supported architectures
android.arch = arm64-v8a

# (str) Android build tools version
android.build_tools_version = 36.1.0

# (bool) Skip updating SDK/NDK in Docker (Docker already has them)
android.skip_update = True

# (int) Logging level (0 = debug, 2 = info)
log_level = 2
