#!/bin/bash
# Script to download the corrected package-lock.json from CI

cd apps/web

# The CI successfully generated the correct package-lock.json
# We need to regenerate it locally with Node.js 22

echo "This script requires Node.js 22 to be installed."
echo "Current Node version:"
node --version

echo ""
echo "If you have Node.js 22, run: npm install"
echo "This will update package-lock.json with the correct dependencies."
echo ""
echo "Then commit and push:"
echo "  git add package-lock.json"
echo "  git commit -m 'fix: update package-lock.json with Node.js 22'"
echo "  git push origin issue-129"

# Made with Bob
