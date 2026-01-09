[app]
# App details
title = MyApp
package.name = myapp
package.domain = org.example
version = 1.0
orientation = portrait

# Source files
source.dir = .
source.include_exts = py,kv,png,jpg

# Requirements
requirements = python3,kivy

# Log level
log_level = 2

# ----------------------
# Android specific
# ----------------------
# Use the newer python-for-android bootstrap
p4a.bootstrap = sdl2

# Minimum and target API
android.api = 33
android.minapi = 21

# Architecture
android.arch = arm64-v8a

# Build tools version
android.build_tools_version = 33.0.2

# NDK version
android.ndk = 25b

# Skip auto SDK/NDK update (we handle it in the workflow)
android.skip_update = True
