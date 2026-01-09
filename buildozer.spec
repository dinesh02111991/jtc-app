[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3,kivy
orientation = portrait
version = 1.0

android.api = 33
android.minapi = 21
android.arch = arm64-v8a
android.ndk = 25b
android.build_tools_version = 33.0.2
android.bootstrap = sdl2

# 🔴 THIS IS THE FIX
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.skip_update = True

log_level = 2
