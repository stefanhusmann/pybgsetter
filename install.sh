#!/bin/sh
##      pyBgSetter installer
##
##  Author of this file:
##      - Pável Varela Rodríguez <neonskull@gmail.com>
##
##  Copyright (C) 2010 Pável Varela Rodríguez <neonskull@gmail.com>
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published
## by the Free Software Foundation; version 2 only.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.


ROOT=""
[ -n "$1" ] && ROOT=$1

# Scripts
install -Dm755 ./src/pybgsetter.py "$ROOT"/usr/bin/pybgsetter || exit 1

# UI
install -Dm644 ./src/pybgsetterui.glade "$ROOT"/usr/share/pybgsetter/pybgsetterui.glade || exit 1

# Extras
install -Dm644 ./src/extras/LICENSE "$ROOT"/usr/share/pybgsetter/extras/LICENSE || exit 1
install -Dm644 ./src/extras/HELP "$ROOT"/usr/share/pybgsetter/extras/HELP || exit 1

# Translations
install -Dm644 ./po/i18n/es/LC_MESSAGES/pybgsetter.mo "$ROOT"/usr/share/locale/es/LC_MESSAGES/pybgsetter.mo || exit 1
install -Dm644 ./po/i18n/cs/LC_MESSAGES/pybgsetter.mo "$ROOT"/usr/share/locale/cs/LC_MESSAGES/pybgsetter.mo || exit 1
install -Dm644 ./po/i18n/fr/LC_MESSAGES/pybgsetter.mo "$ROOT"/usr/share/locale/fr/LC_MESSAGES/pybgsetter.mo || exit 1
install -Dm644 ./po/i18n/pl/LC_MESSAGES/pybgsetter.mo "$ROOT"/usr/share/locale/pl/LC_MESSAGES/pybgsetter.mo || exit 1
install -Dm644 ./po/i18n/de/LC_MESSAGES/pybgsetter.mo "$ROOT"/usr/share/locale/de/LC_MESSAGES/pybgsetter.mo || exit 1

# .desktop file
install -Dm644 ./pybgsetter.desktop "$ROOT"/usr/share/applications/pybgsetter.desktop || exit 1

