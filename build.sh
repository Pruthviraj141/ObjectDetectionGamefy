#!/usr/bin/env bash
set -e  # stop if any command fails

echo "🚀 Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing dependencies..."
pip install -r requirements.txt
