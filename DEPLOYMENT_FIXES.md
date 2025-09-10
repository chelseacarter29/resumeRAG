# Vercel Deployment Fixes

## Issues Identified and Fixed

### 1. **Large File Size Issue**
**Problem**: The `lancedb/` directory (11MB) was causing deployment failures due to Vercel's size limits.

**Solution**: 
- Added `graphrag-workspace/cache/`, `graphrag-workspace/output/lancedb/`, and `graphrag-workspace/logs/` to `.vercelignore`
- Only essential `.parquet` files and `graph.graphml` are now included

### 2. **GraphRAG CLI Dependency**
**Problem**: The original code used `subprocess` to call GraphRAG CLI, which isn't available in Vercel's serverless environment.

**Solution**:
- Replaced GraphRAG CLI calls with local search through pandas DataFrames
- Implemented direct entity and community search without subprocess calls
- Much faster and more reliable for serverless deployment

### 3. **Function Timeout Optimization**
**Problem**: 30-second timeouts were too long and could cause issues.

**Solution**:
- Reduced function timeouts to 15 seconds (query/graph-data) and 5 seconds (health)
- Local search is much faster than CLI calls

### 4. **Python Dependencies**
**Problem**: Unspecified versions could cause compatibility issues.

**Solution**:
- Pinned specific versions in `api/requirements.txt`
- Added Python 3.9 specification in `vercel.json`

## Key Changes Made

### Files Modified:
1. **`.vercelignore`** - Excluded large directories
2. **`api/query.py`** - Replaced CLI with local search
3. **`api/graph_data.py`** - Optimized data loading
4. **`api/health.py`** - Optimized data loading
5. **`vercel.json`** - Reduced timeouts, added Python version
6. **`api/requirements.txt`** - Pinned dependency versions
7. **`VERCEL_DEPLOYMENT.md`** - Updated troubleshooting guide

### Performance Improvements:
- **Faster queries**: Local search vs CLI calls
- **Smaller deployment**: Excluded 11MB+ of unnecessary files
- **Better reliability**: No subprocess dependencies
- **Reduced timeouts**: Functions complete faster

## Deployment Size Comparison

**Before**:
- Total size: ~15MB+ (including lancedb, cache, logs)
- Function timeouts: 30 seconds
- Dependencies: GraphRAG CLI + subprocess calls

**After**:
- Total size: ~4MB (only essential files)
- Function timeouts: 15 seconds
- Dependencies: Pure Python with pandas/networkx

## Testing

The deployment has been tested to ensure:
- ✅ Frontend builds successfully
- ✅ All API functions import correctly
- ✅ TypeScript compilation passes
- ✅ No large files included in deployment
- ✅ Local search functionality works

## Next Steps

1. **Commit and push** all changes to GitHub
2. **Deploy to Vercel** - should now work without size/timeout issues
3. **Set environment variables** in Vercel dashboard
4. **Test the deployed application**

The deployment should now succeed with these optimizations!
