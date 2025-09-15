#!/usr/bin/env bash
set -euo pipefail

cmake -S core -B build/core
cmake --build build/core
