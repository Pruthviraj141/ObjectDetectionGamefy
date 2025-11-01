#!/usr/bin/env bash
set -e

echo "🚀 Upgrading pip, setuptools, and wheel..."

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Build completed successfully!"
