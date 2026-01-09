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

# 🔑 FORCE buildozer to use system SDK
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653

log_level = 2
