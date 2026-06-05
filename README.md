# AI PDF Earnings Call Auditor 🔎

An automated forensic auditing pipeline prototype designed to detect internal financial contradictions in earnings call transcripts. It processes PDFs, extracts forward-looking guidance metrics, cross-references them against historical financial tables within the document, and displays severity-rated Audit Cards.

## Decoupled Architecture

The project is split into two components:
1. **`/backend`**: Python FastAPI application hosting a LangGraph adversarial state machine. Programmatically runs a LiteLLM Proxy or routes requests through OpenRouter (defaults to free model: `google/gemini-2.5-flash:free`). Includes Neon Postgres database integration to store audit histories and parsed files.
2. **`/frontend`**: A React Single Page Application (SPA) powered by Vite and Tailwind CSS. Implements a premium split-screen dashboard utilizing native browser `EventSource` to render live streaming agent logs, reasoning tokens, and color-coded Audit Cards.

---

## How It Works & Usage Guidelines

### 1. Document Requirements
The auditor processes **one earnings call PDF** at a time. To test the forensic auditor effectively, the document should contain:
- **Forward-looking Guidance**: Statements estimating future performances (e.g., *"We expect Q3 Revenue to be between $10.2B and $10.5B"* or *"FY26 operating margin is forecasted at 25%"*).
- **Historical Numeric Tables**: Tables or summaries outlining current/historical figures (e.g., past quarter revenues, balance sheets, share structures, or operating expense tables).

### 2. Adversarial Agent State Machine (LangGraph)
Once the audit begins:
- **Node A (Guidance Extractor)**: Splits the PDF and extracts forward-looking guidance metrics (Revenue, EPS, Margin, etc.).
- **Node B (Forensic Auditor)**: Cross-references the extracted metrics against historical tables. If a calculation/metric discrepancy is found but the explanation is ambiguous or data is incomplete, it loops back to Node A with a correction suggestion (up to 3 times).
- **Node C (Synthesizer)**: Formulates final "Audit Cards" with JSON metadata and severity levels (`High`, `Med`, `Low`).

---

## Setup & Configuration

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenRouter API key (to run LLMs for free) or OpenAI/Groq API keys.
- Neon Postgres Connection string (Optional: backend falls back to local SQLite if left blank).

### Environment Variables

#### Backend (`/backend/.env`)
Create a `.env` file inside `/backend` following this schema (see `backend/.env.example`):
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_MODEL=google/gemini-2.5-flash:free
LLM_API_BASE=https://openrouter.ai/api/v1
DATABASE_URL=postgresql://user:password@ep-something.aws.neon.tech/neondb?sslmode=require
```

#### Frontend (`/frontend/.env.local` or `.env`)
Create a `.env` file inside `/frontend`:
```env
VITE_BACKEND_URL=http://localhost:7860
```

---

## Local Development Execution

### 1. Start the Backend API
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --port 7860 --reload
```
The FastAPI documentation will be available at `http://localhost:7860/docs`.

### 2. Start the Frontend SPA
```bash
cd frontend
npm install
npm run dev
```
The client app will open at `http://localhost:5173`.

---

## Deployment Configuration

### Backend (Railway / Hugging Face Spaces)
The backend includes a `Dockerfile` that automatically runs on port `7860` or the platform's `$PORT` environment variable.
1. Connect your Github repository to Railway.
2. In Railway settings, add environment variables for `OPENROUTER_API_KEY`, `LLM_MODEL`, `LLM_API_BASE`, and your Neon Postgres `DATABASE_URL`.
3. Railway will automatically detect the root-level `Dockerfile` and build/deploy the container without any manual settings.

### Frontend (Vercel)
The frontend is built to run on Vercel out of the box.
1. Deploy the project using the Vercel dashboard or CLI.
2. In Vercel environment configurations, set:
   `VITE_BACKEND_URL = https://your-backend-railway-url.railway.app`
3. Vercel will compile the Vite build (`npm run build`) and host it statically.


## Results

1. For Clean PDFs with correct numbers it works as expected.
![alt text](results/low_severity.png)

2. For PDFs with no relation between forward and backward numbers it works as expected.
![alt text](results/high_severity.png)