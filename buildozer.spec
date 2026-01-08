[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3,kivy
orientation = portrait
version = 1.0

# --- Android SDK / NDK configuration (GitHub Actions compatible) ---
android.sdk_path = /home/runner/android-sdk
android.ndk_path = /home/runner/android-sdk/ndk/25.2.9519653
android.sdkmanager_path = /home/runner/android-sdk/cmdline-tools/latest/bin/sdkmanager

android.api = 33
android.build_tools_version = 33.0.2
android.skip_update = True
