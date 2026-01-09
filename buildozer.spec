[app]
# (App basics)
title = MyApp
package.name = myapp
package.domain = org.example
source.dir = .
source.include_exts = py,kv,png,jpg
version = 1.0
orientation = portrait
requirements = python3,kivy

# Android specific
p4a.bootstrap = sdl2
android.api = 33
android.minapi = 21
android.arch = arm64-v8a
android.build_tools_version = 33.0.2
android.skip_update = True

# Logging
log_level = 2
