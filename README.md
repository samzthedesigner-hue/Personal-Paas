# Personal PaaS Controller

A self-hosted controller that manages your projects on Render via API.

## Features

- Deploy GitHub repos to Render
- List all deployed projects
- View project status
- Get public URLs
- Start/Stop/Restart services
- View logs
- Web dashboard
- API for mobile app integration

## Setup

1. Deploy this repo to Render
2. Set environment variables:
   - `RENDER_API_KEY` - Your Render API key
   - `GITHUB_TOKEN` - Your GitHub personal access token
3. Access the dashboard at your Render URL

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/projects` - List projects
- `POST /api/deploy` - Deploy new project
- `GET /api/github/repos` - List GitHub repos
- `POST /api/projects/:id/restart` - Restart project
- `POST /api/projects/:id/stop` - Stop project
- `DELETE /api/projects/:id` - Delete projectaas
