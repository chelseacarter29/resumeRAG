# Vercel Deployment Guide for ResumeRAG

This guide will help you deploy ResumeRAG to Vercel with both frontend and backend functionality.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **OpenAI API Key**: You'll need this for GraphRAG functionality

## Deployment Steps

### 1. Prepare Your Repository

Make sure your repository contains:
- `vercel.json` - Vercel configuration
- `api/` directory with Python serverless functions
- `src/` directory with React frontend
- `package.json` with build scripts
- `graphrag-workspace/` with your data files

### 2. Deploy to Vercel

1. **Connect Repository**:
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "New Project"
   - Import your GitHub repository

2. **Configure Environment Variables**:
   - In the Vercel dashboard, go to your project settings
   - Navigate to "Environment Variables"
   - Add: `OPENAI_API_KEY` with your OpenAI API key

3. **Deploy**:
   - Vercel will automatically detect the configuration
   - Click "Deploy" to start the deployment process

### 3. Verify Deployment

After deployment, test these endpoints:
- `https://your-app.vercel.app/` - Frontend
- `https://your-app.vercel.app/api/health` - Health check
- `https://your-app.vercel.app/api/query` - Query endpoint
- `https://your-app.vercel.app/api/graph-data` - Graph data

## Project Structure

```
resumeRAG/
├── api/                    # Vercel serverless functions
│   ├── query.py           # Main query endpoint
│   ├── graph-data.py      # Graph visualization data
│   ├── health.py          # Health check
│   └── requirements.txt   # Python dependencies
├── src/                   # React frontend
│   ├── components/
│   └── App.tsx
├── graphrag-workspace/    # GraphRAG data files
│   ├── output/           # Generated graph data
│   └── input/            # Resume data
├── vercel.json           # Vercel configuration
├── package.json          # Frontend dependencies
└── .vercelignore         # Files to exclude from deployment
```

## Configuration Details

### vercel.json
- Configures both static build and Python functions
- Sets up routing for API endpoints
- Defines environment variables
- Sets function timeouts

### API Functions
- `query.py`: Handles natural language queries using GraphRAG
- `graph-data.py`: Provides graph data for visualization
- `health.py`: Health check endpoint

### Frontend
- Uses relative API paths (`/api/query`, `/api/graph-data`)
- Builds to `dist/` directory
- Configured for Vercel's static hosting

## Troubleshooting

### Common Issues

1. **Function Timeout**:
   - GraphRAG queries can take time
   - Functions are configured with 30-second timeout
   - Consider optimizing queries if needed

2. **Missing Data Files**:
   - Ensure `graphrag-workspace/` is included in deployment
   - Check that all `.parquet` files are present

3. **Environment Variables**:
   - Verify `OPENAI_API_KEY` is set in Vercel dashboard
   - Check that the key has sufficient credits

4. **CORS Issues**:
   - API functions include CORS headers
   - Frontend uses relative paths to avoid CORS

### Debugging

1. **Check Vercel Logs**:
   - Go to your project dashboard
   - Click on "Functions" tab
   - View logs for each function

2. **Test API Endpoints**:
   - Use curl or Postman to test endpoints directly
   - Check response status and error messages

3. **Frontend Issues**:
   - Check browser console for errors
   - Verify API calls are using correct paths

## Performance Considerations

- **Cold Starts**: Python functions may have cold start delays
- **Data Loading**: GraphRAG data is loaded on first request
- **Caching**: Consider implementing caching for frequently accessed data
- **Function Limits**: Vercel has limits on function execution time and memory

## Updates and Maintenance

1. **Code Updates**: Push to GitHub triggers automatic deployment
2. **Environment Variables**: Update in Vercel dashboard
3. **Data Updates**: Update files in `graphrag-workspace/` and redeploy
4. **Monitoring**: Use Vercel analytics to monitor performance

## Cost Considerations

- **Vercel Pro**: Required for longer function timeouts
- **OpenAI API**: Costs based on usage
- **Bandwidth**: Vercel has bandwidth limits on free tier

## Support

For issues specific to:
- **Vercel**: Check [Vercel documentation](https://vercel.com/docs)
- **GraphRAG**: Check [GraphRAG documentation](https://github.com/microsoft/graphrag)
- **This Project**: Check the main README.md
