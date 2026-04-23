# DataMind Intelligence Engine 🧠

A premium, production-ready Text-to-SQL platform designed for high-authority data analysis. DataMind uses a multi-agent orchestration layer (LangGraph) to transform natural language into secure, optimized SQL queries across multiple database engines.

![Premium UI](https://img.shields.io/badge/UI-Glassmorphism-blue)
![Backend](https://img.shields.io/badge/Engine-Multi--DB-green)
![Security](https://img.shields.io/badge/Security-Agentic--Validation-red)

## ✨ Major Features

### 1. Multi-Engine Analytics
Switch seamlessly between **PostgreSQL** and **MySQL (XAMPP)**. The system dynamically discovers your local databases, extracts schemas, and routes queries to the correct driver.

### 2. Premium Editorial UI
*   **Glassmorphism Design**: A sleek, OS-like interface with translucent layers and backdrop blurs.
*   **Interactive Data Badges**: Database and Table lists are rendered as aesthetic, clickable components.
*   **Layered Depth**: Custom shadows and typography optimized for maximum readability.
*   **Responsive Dashboard**: Real-time status badges and professional data tables.

### 3. Agentic Intelligence Layer (LangGraph)
*   **Schema-Aware Generation**: Agents read your dynamic schema context to ensure 100% accurate table/column referencing.
*   **Validator Agent**: Every query is screened to prevent destructive actions (`DROP`, `DELETE`, `UPDATE`).
*   **Confidence Scoring**: Real-time evaluation of the AI's certainty in the generated SQL.
*   **Query Explanations**: Human-readable breakdowns of what the SQL query is doing and why.

### 4. Dynamic Engine Audit (Benchmarking)
A built-in performance suite that:
1.  Auto-scans all connected databases.
2.  Generates realistic business test cases per schema.
3.  Measures system accuracy, latency, and confidence floor.

---

## 🚀 Getting Started

### Prerequisites
*   **Python 3.10+**
*   **Node.js 18+**
*   **XAMPP** (for MySQL support)
*   **PostgreSQL** (local or remote)
*   **Mistral API Key**

### 1. Environment Setup
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
MISTRAL_API_KEY=your_key_here
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DATABASE=mysql
```

### 2. Backend Installation
```bash
pip install -r requirements.txt
python -m api.main
```

### 3. Frontend Installation
```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Technology Stack
*   **Core**: LangGraph, CrewAI, FastAPI
*   **LLM**: Mistral AI (Large/Small)
*   **Frontend**: React, Vite, Vanilla CSS (Glassmorphism)
*   **Icons**: Lucide React
*   **Drivers**: Psycopg2, MySQL-Connector-Python

## 🛡️ Security Protocol
The system enforces a **Read-Only** policy for standard users. All generated SQL is parsed and validated by a dedicated security agent before execution to ensure no data corruption can occur.

---

**Developed with ❤️ by Sahil Chavan**
