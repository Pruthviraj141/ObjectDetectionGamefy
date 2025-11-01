#!/usr/bin/env bash
set -e  # stop on any error

echo "🚀 Updating pip, setuptools, and wheel..."
pip install --upgrade pip
pip install --upgrade setuptools wheel

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Build complete! Ready to start the app."
