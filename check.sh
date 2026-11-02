#!/bin/sh
# SPDX-License-Identifier: MIT
# build.sh で作った 8 つの場面を点検する。必要なもの：Node.js
set -e
cd "$(dirname "$0")"
status=0
for name in bellows bellowsLow bellowsMan bellowsLowMan piston pistonLow pistonMan pistonLowMan; do
  node tests/check.js "build/ja/$name.json" || status=1
done
exit $status
