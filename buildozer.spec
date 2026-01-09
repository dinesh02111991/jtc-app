[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3,kivy
orientation = portrait
version = 1.0

# --- ANDROID ---
android.api = 33
android.minapi = 21
android.arch = arm64-v8a

# 🔴 FORCE SYSTEM SDK (CRITICAL)
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653

# 🔴 DO NOT LET BUILDOZER DOWNLOAD SDK
android.skip_update = True
android.build_tools_version = 33.0.2

# 🔴 REQUIRED (deprecated warning safe)
p4a.bootstrap = sdl2

log_level = 2
