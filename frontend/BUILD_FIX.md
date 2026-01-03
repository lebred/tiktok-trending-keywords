# Frontend Build Fix - Complete Guide

## Problems Fixed

1. **Next.js version mismatch**: Package using Next 15.x instead of pinned 14.0.4
2. **Path alias resolution**: `@/` imports not resolving to correct files

## Files Changed

### 1. `package.json` - Added helper scripts

- `"build:export": "next build && next export"` - Build and export in one command
- `"reinstall": "npm run clean && npm install && npm ls next"` - Clean reinstall with version check

### 2. `tsconfig.json` - Fixed path alias resolution

- Added `"baseUrl": "."` (REQUIRED for paths to work)
- Kept `"paths": { "@/*": ["./*"] }` (resolves all @/ imports)

### 3. `next.config.js` - Added webpack alias fallback

- Added webpack config with `config.resolve.alias['@']` pointing to frontend root
- Ensures @/ imports work in both TypeScript and webpack

### 4. `package-lock.json` - Created/updated

- Locks Next.js to exactly 14.0.4
- Ensures deterministic installs

## Fix Instructions

### Option A: Automated (Recommended)

Run the verification script:

```bash
cd frontend
./INSTALL_VERIFY.sh
```

This will:

1. Clean install dependencies
2. Verify Next.js version is 14.0.4
3. Verify required files exist
4. Run type check
5. Build and export
6. Verify output structure

### Option B: Manual Step-by-Step

```bash
cd frontend

# 1. Clean reinstall
npm run clean
npm install

# 2. Verify Next.js version
npm ls next
# Expected: next@14.0.4

node -p "require('./node_modules/next/package.json').version"
# Expected: 14.0.4

# 3. Verify files exist
ls -la lib/api.ts components/KeywordList.tsx components/KeywordDetailClient.tsx
# All should exist

# 4. Type check (verify @/ imports resolve)
npm run type-check
# Should pass with no errors

# 5. Build
npm run build
# Should complete successfully and create out/ directory

# 6. Verify output
ls -la out/
ls -la out/index.html
ls -la out/_next/
# All should exist

# 7. Verify asset paths (should be /app/_next/... not /_next/...)
grep "_next" out/index.html | head -3
# Should show /app/_next/... paths
```

## Validation Commands

```bash
# Check Next.js version (must be 14.0.4)
npm ls next --depth=0

# Check actual installed version
node -p "require('./node_modules/next/package.json').version"

# Verify TypeScript can resolve @/ imports
npm run type-check

# Build and verify
npm run build
test -f out/index.html && echo "✓ Build succeeded" || echo "✗ Build failed"
```

## Troubleshooting

### If Next.js is still wrong version:

```bash
# Force clean reinstall
rm -rf node_modules .next package-lock.json out
npm cache clean --force
npm install
npm ls next
```

### If @/ imports still don't resolve:

1. Check `tsconfig.json` has `baseUrl: "."`
2. Check `next.config.js` has webpack alias
3. Restart your editor/IDE (TypeScript language server may need restart)

### If build fails with module errors:

```bash
# Clear Next.js cache
rm -rf .next
npm run build
```

### If out/ directory not created:

- Check that `next.config.js` has `output: 'export'`
- Try: `npm run build && npm run export`

## Expected Build Output Structure

```
frontend/
├── out/
│   ├── index.html              # Main page
│   ├── _next/                  # Next.js assets
│   │   ├── static/
│   │   └── ...
│   ├── archive/
│   │   └── index.html
│   └── keywords/
│       └── [id]/
│           └── index.html
└── ...
```

Asset paths in HTML should be `/app/_next/...` (due to `basePath: '/app'` in config).

## Production Deployment

After successful build:

```bash
# Copy to server
rsync -avz out/ user@server:/var/www/trendearly/app/

# Or if building on server
npm run clean
npm install
NEXT_PUBLIC_API_URL=https://trendearly.xyz/api npm run build
cp -r out/* /var/www/trendearly/app/
```
