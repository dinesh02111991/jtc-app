[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3,kivy
orientation = portrait
version = 1.0

# ---- ANDROID CONFIG ----
android.api = 33
android.minapi = 21
android.arch = arm64-v8a
android.ndk = 25b
android.build_tools_version = 33.0.2
android.bootstrap = sdl2

# ---- DEBUGGING ----
log_level = 2
