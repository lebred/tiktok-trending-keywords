# Frontend Build Validation Commands

Run these commands from the `frontend/` directory to verify the build fix:

## Step 1: Verify package.json
```bash
cat package.json | grep '"next"'
# Expected: "next": "14.0.4",
```

## Step 2: Clean install (fixes version mismatch)
```bash
npm run clean
npm install
```

## Step 3: Verify Next.js version is correct
```bash
npm ls next --depth=0
# Expected output should include: next@14.0.4

node -p "require('./node_modules/next/package.json').version"
# Expected output: 14.0.4
```

## Step 4: Verify required files exist
```bash
ls -la lib/api.ts components/KeywordList.tsx components/KeywordDetailClient.tsx
# All three files should exist
```

## Step 5: Verify TypeScript config
```bash
cat tsconfig.json | grep -A 3 '"baseUrl"'
# Should show: "baseUrl": "."

cat tsconfig.json | grep -A 2 '"paths"'
# Should show: "@/*": ["./*"]
```

## Step 6: Type check (verifies @/ imports resolve)
```bash
npm run type-check
# Should complete with no errors
```

## Step 7: Build
```bash
npm run build
# Should complete successfully
```

## Step 8: Verify output
```bash
# Check out/ directory exists
ls -la out/

# Check key files
ls -la out/index.html
ls -la out/_next/

# Verify asset paths use /app/ prefix
grep -o "/app/_next[^\"]*" out/index.html | head -3
# Should show paths like: /app/_next/static/...
```

## Quick automated verification
```bash
./INSTALL_VERIFY.sh
# Runs all checks automatically
```

## Summary of expected results:
- ✓ Next.js version: 14.0.4
- ✓ Required files exist
- ✓ Type check passes
- ✓ Build succeeds
- ✓ out/ directory created with index.html and _next/
- ✓ Asset paths use /app/_next/ prefix

