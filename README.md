# Web Research Agent (Google Cloud Run Edition)

This is an autonomous AI research agent powered by the DeepSeek API (deepseek-v4-flash).

When you provide a research question, the agent will:
1. Plan 4 targeted, multi-dimensional search queries.
2. Search DuckDuckGo to find relevant sources.
3. Scrape the URLs and extract clean text.
4. Filter out irrelevant, low-substance, or SEO spam pages.
5. Synthesize a comprehensive markdown report using deep reasoning.

This project is built as a full-stack, cloud-ready application.

## Features

- Full-Stack UI: A modern Next.js frontend built with React and Tailwind CSS.
- Authentication: Secured with NextAuth.js credentials login. The API is protected via Backend API Keys.
- Asynchronous Cloud Backend: 
  - FastAPI provides a high-performance SSE (Server-Sent Events) API.
  - Google Cloud Tasks handle long-running, concurrent web scraping tasks asynchronously.
- Persistent Database: Research logs and metadata are stored in a MongoDB database.
- History Dashboard: Browse past research tasks, including sources used, token metrics, and expandable reports.
- Cost Tracking: The UI estimates the API cost for every search based on DeepSeek's current pricing.
- Downloadable Reports: Download any finished research report as a markdown file.
- Task Cancellation: You can forcefully terminate any active research task running in the cloud.

## Architecture

- Frontend: Next.js 14 (App Router), React, Tailwind, NextAuth.js
- API Proxy: FastAPI, Python 3.12
- Worker/Queue: Cloud Tasks
- Database: MongoDB (Motor async driver)
- AI/Scraping Core: OpenAI SDK, trafilatura, BeautifulSoup4, ddgs

## Getting Started Locally

### 1. Backend Setup (Python)
Make sure you have Redis and MongoDB running locally, then set up your environment:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in the root directory:
```env
DEEPSEEK_API_KEY=your_api_key_here
BACKEND_API_KEY=dev-secret-key
REDIS_URL=redis://localhost:6379/0
MONGODB_URI=mongodb://localhost:27017
```

Start the FastAPI Server in a separate terminal:
```bash
uvicorn api:app --reload --port 8000
```

### 2. Frontend Setup (Node.js)
```bash
cd frontend
npm install
```

Create a `frontend/.env.local` file:
```env
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=super-secret-key-123
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
BACKEND_API_KEY=dev-secret-key
```

Start the Next.js Dev Server:
```bash
npm run dev
```

Visit `http://localhost:3000` to log in (Default Username: `testuser`, Password: `password123`) and start researching.

## Google Cloud Run Deployment

This application is designed to be deployed using a microservices architecture on Google Cloud Run. It runs 3 containers inside a secure VNet environment:
1. Frontend App: Next.js Node container (Public Ingress)
2. FastAPI App: Python container (Internal TCP Ingress)
3. Mongo DB & Redis: Managed services or sidecar containers.

Refer to the deployment documentation for CI/CD GitHub Actions setup.

## License
MIT
