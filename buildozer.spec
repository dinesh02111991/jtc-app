[app]
# (str) Title of your application
title = MyApp

# (str) Package name
package.name = myapp

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code directory
source.dir = .

# (list) Source file extensions to include
source.include_exts = py,kv,png,jpg

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation (one of: portrait, landscape, all)
orientation = portrait

# (str) Application version
version = 1.0

# ----------------------------------------------------------------------
# Android specific
# ----------------------------------------------------------------------
# (int) Android API to use
android.api = 33

# (int) Minimum API required
android.minapi = 21

# (str) Android architecture
android.arch = arm64-v8a

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android build tools version
android.build_tools_version = 33.0.2

# (str) Bootstrap to use (SDL2 recommended for modern Kivy)
p4a.bootstrap = sdl2

# (bool) Skip update check (True is safer in CI/CD)
android.skip_update = True

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
# (int) Log level: 0 = debug, 1 = info, 2 = warning, 3 = error
log_level = 2
