[app]
title = MyApp
package.name = myapp
package.domain = org.example

source.dir = .
source.include_exts = py,kv,png,jpg

requirements = python3, kivy, kivymd, requests, pillow, sqlite3
orientation = portrait
version = 1.0

android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a
android.ndk = 25b

p4a.bootstrap = sdl2

log_level = 2
