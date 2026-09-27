Drop these two files here for Bangla testimonials to render actual Bangla
glyphs instead of falling back to Helvetica (which shows boxes/blanks for
Bangla text):

    NotoSansBengali-Regular.ttf
    NotoSansBengali-Bold.ttf

Get them free from Google Fonts: https://fonts.google.com/noto/specimen/Noto+Sans+Bengali
(Download family -> unzip -> copy the two .ttf files into this folder.)

apps/cards/services.py auto-detects these files at import time and
registers them with ReportLab as "NotoBengali" / "NotoBengali-Bold". No
code changes needed once the files are here — just restart the app server.
