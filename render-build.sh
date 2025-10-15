#!/usr/bin/env bash
set -o errexit  # останавливаем при ошибках

pip install --upgrade pip setuptools wheel
pip install --no-cache-dir -r requirements.txt
