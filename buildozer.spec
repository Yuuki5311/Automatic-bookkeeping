[app]
title = 自动记账
package.name = autobookkeeping
package.domain = org.example
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
requirements = python3,kivy==2.3.0,kivymd==1.2.0,pyjnius
orientation = portrait
osx.python_version = 3
osx.kivy_version = 1.9.1
fullscreen = 0
android.permissions = BIND_NOTIFICATION_LISTENER_SERVICE,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
android.accept_sdk_license = True
android.arch = arm64-v8a
android.allow_backup = True
version = 1.3.0

[buildozer]
log_level = 2
warn_on_root = 1
