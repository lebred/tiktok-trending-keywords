# Frontend Build Fix Instructions

## Issue 1: Next.js Version Mismatch

If you see Next.js 15.x when package.json says 14.0.4, clean and reinstall:

```bash
cd frontend
rm -rf node_modules .next package-lock.json
npm install
npm ls next
```

**Expected output:** `next@14.0.4`

## Issue 2: Path Alias Resolution

The `@/...` imports are now fixed in `tsconfig.json`:
- Added `baseUrl: "."` (required for paths to work)
- Simplified paths to `"@/*": ["./*"]` (covers all subpaths)

## Build and Verify

After fixing, run:

```bash
cd frontend
npm run build
ls -la out/
```

**Expected:**
- `out/index.html` exists
- `out/_next/` directory exists with assets
- Asset paths in HTML should be `/app/_next/...` (due to basePath config)

## Quick Clean Reinstall

Use the npm script:

```bash
npm run clean
npm install
npm run build
```

