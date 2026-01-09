[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3,kivy
orientation = portrait
version = 1.0

# Android settings
android.api = 33
android.minapi = 21
android.arch = arm64-v8a
android.ndk = 25b
android.build_tools_version = 33.0.2

# Python for Android bootstrap
p4a.bootstrap = sdl2
android.skip_update = True

# Logging
log_level = 2
