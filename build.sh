#!/usr/bin/env bash
set -e
echo "🚀 Forcing Python 3.10..."
pyenv install -s 3.10.13
pyenv global 3.10.13
python --version

echo "📦 Upgrading tools..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
