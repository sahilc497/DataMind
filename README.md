# 🧠 DataMind: Enterprise Multi-Agent Text-to-SQL Platform

DataMind is a state-of-the-art intelligent analytics engine that converts natural language into production-ready SQL. Supporting multiple database types and featuring a robust security and caching layer, it is designed for scalable enterprise data exploration.

## 🚀 Key Features

- **🧩 Multi-Database Support**: Unified interface for **PostgreSQL** and **MySQL** (XAMPP-compatible).
- **🤖 Agentic Orchestration**: Powered by **LangGraph** and **CrewAI** for complex, multi-step reasoning.
- **⚡ Performance Optimized**: 
  - **Fast-Path**: Sub-100ms response for simple queries.
  - **Dual-Layer Caching**: TTL-based caching for SQL generation and data results.
- **🛡️ Enterprise Security**:
  - **Hallucination Guard**: Schema-validation before execution.
  - **RBAC**: Admin vs. User modes with destructive command blocking.
- **🧠 Advanced Analytics**:
  - **Conversational Memory**: Multi-turn query modification.
  - **Explain Mode**: Human-readable explanations + SQL `EXPLAIN` plan visualization.
  - **Data Insights**: Intelligent anomaly detection and trend analysis.
- **🎨 Premium UI**: React-based editorial interface with SQL Edit & Re-run capabilities.

## 🛠️ Technology Stack

- **Backend**: FastAPI, LangGraph, CrewAI
- **LLM**: Mistral AI (Large/Small)
- **Database**: PostgreSQL (asyncpg), MySQL (mysql-connector)
- **Frontend**: React, Lucide Icons, Vanilla CSS (Premium Editorial Design)
- **Utilities**: Cachetools, Pydantic (Settings), AsyncIO

## 📂 Project Structure

```text
/api        - FastAPI routes and middleware
/graph      - LangGraph workflow and state management
/agents     - CrewAI agent definitions and specialized tools
/db         - Database abstraction layer (Postgres/MySQL)
/services   - Normalization, RBAC, and Visualization engines
/cache      - TTL-based caching service
/memory     - Conversational context manager
/frontend   - React application
```

## 🚦 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js & npm
- PostgreSQL / XAMPP (MySQL)

### 2. Installation
```bash
# Clone the repo
git clone https://github.com/your-username/datamind-text2sql.git
cd datamind-text2sql

# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
MISTRAL_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
```

### 4. Running the System
```bash
# Start Backend (from root)
python api/main.py

# Start Frontend (from /frontend)
npm run dev
```

## 🧪 Benchmarking
The system includes a built-in benchmarking suite to measure accuracy and latency across different database types. Access it via the `/benchmark` endpoint or the UI Evaluation tab.

## 📜 License
MIT License. Created by the Advanced Agentic Coding Team.
