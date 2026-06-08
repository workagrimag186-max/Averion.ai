# CI Fix: @swc/helpers Dependency Conflict

## Issue
The Web CI workflow was failing with the following error:
```
npm error `npm ci` can only install packages when your package.json and package-lock.json or npm-shrinkwrap.json are in sync.
npm error Missing: @swc/helpers@0.5.23 from lock file
```

## Root Cause
- `@swc/helpers@0.5.23` was explicitly declared in `apps/web/package.json` as a direct dependency
- Next.js internally depends on `@swc/helpers@0.5.15` as a nested dependency
- This created a version conflict that `npm ci` detected during its strict validation
- `@swc/helpers` is a transitive dependency that should be managed by Next.js, not declared explicitly

## Resolution
**Date:** 2026-06-08

### Changes Made
1. **Removed explicit dependency** from `apps/web/package.json`:
   - Deleted `"@swc/helpers": "0.5.23"` from the dependencies section
   - This allows Next.js to manage the dependency internally

2. **Regenerated package-lock.json**:
   - Ran `npm install` in `apps/web` directory
   - The lock file now properly reflects only the transitive dependency from Next.js
   - Output: "removed 1 package, and audited 388 packages"

### Verification
- ✅ `@swc/helpers@0.5.23` no longer appears in `package.json`
- ✅ `package-lock.json` is now in sync with `package.json`
- ✅ No explicit `@swc/helpers` dependency at root level in lock file
- ✅ Next.js's internal `@swc/helpers@0.5.15` dependency remains intact

## Why This Works
- `@swc/helpers` is a helper library used by SWC (the compiler Next.js uses)
- Next.js already includes it as a dependency, so explicit declaration is unnecessary
- Removing it eliminates the version conflict while maintaining all functionality
- This follows npm best practices for managing transitive dependencies

## Future Prevention
- Avoid explicitly declaring transitive dependencies unless absolutely necessary
- Let framework dependencies (like Next.js) manage their own internal dependencies
- If a specific version is needed, consider using npm overrides or resolutions instead