#!/bin/bash
# Frontend Build Verification Script

set -e

cd "$(dirname "$0")"

echo "=== Step 1: Clean install ==="
npm run clean
npm install

echo ""
echo "=== Step 2: Verify Next.js version ==="
NEXT_VERSION=$(npm ls next --depth=0 2>&1 | grep next@ || echo "Not found")
echo "npm ls next output: $NEXT_VERSION"

NODE_VERSION=$(node -p "require('./node_modules/next/package.json').version" 2>&1 || echo "Not found")
echo "Actual Next.js version installed: $NODE_VERSION"

if [ "$NODE_VERSION" != "14.0.4" ]; then
  echo "ERROR: Next.js version mismatch! Expected 14.0.4, got $NODE_VERSION"
  exit 1
fi

echo ""
echo "=== Step 3: Verify file structure ==="
for file in lib/api.ts components/KeywordList.tsx components/KeywordDetailClient.tsx; do
  if [ -f "$file" ]; then
    echo "✓ $file exists"
  else
    echo "✗ $file MISSING"
    exit 1
  fi
done

echo ""
echo "=== Step 4: Type check ==="
npm run type-check

echo ""
echo "=== Step 5: Build ==="
npm run build

echo ""
echo "=== Step 6: Verify output ==="
if [ -d "out" ]; then
  echo "✓ out/ directory created"
  if [ -f "out/index.html" ]; then
    echo "✓ out/index.html exists"
  else
    echo "✗ out/index.html MISSING"
    exit 1
  fi
  if [ -d "out/_next" ]; then
    echo "✓ out/_next/ directory exists"
  else
    echo "✗ out/_next/ directory MISSING"
    exit 1
  fi
  
  echo ""
  echo "=== Step 7: Verify asset paths ==="
  if grep -q "/app/_next" out/index.html; then
    echo "✓ Asset paths correctly use /app/_next/ prefix"
  else
    echo "⚠ Warning: Asset paths may not have /app/ prefix"
  fi
else
  echo "✗ out/ directory NOT created"
  exit 1
fi

echo ""
echo "=== ✓ All checks passed! ==="

