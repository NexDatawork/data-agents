<p align="center">
  <img src="assets/banner.png" alt="NexDatawork Banner" width="100%"/>
</p>

<div align="center">

 <h1 style="margin-bottom:0; border-bottom:none;">
   <a href="https://www.nexdatawork.io/blank">
     NexDatawork
   </a>
 </h1>

 <h2 style="margin-top:0;">
  An AI data agent for data engineering and analytics without writing code 
 </h2>

<div align='center'>
<a href="https://github.com/NexDatawork/data-agents/pulls"><img alt = "pull requests" src = "https://img.shields.io/github/issues-pr/NexDatawork/data-agents?label=pull%20requests&labelColor=rgba(56, 52, 182, 1)&color=rgb(90, 42, 184)"/></a> 
<a href="LICENSE"><img alt = "LICENSE" src = "https://img.shields.io/badge/license-Apache%202.0-blueviolet?style=flat&color=rgb(90, 42, 184)&labelColor=rgba(56, 52, 182, 1)"/></a> 
<a href = "https://discord.gg/Tb55tT5UtZ"><img src="https://img.shields.io/badge/Discord-Join%20Community-7289DA?logo=discord&logoColor=white&color=rgb(90, 42, 184)&labelColor=rgba(56, 52, 182, 1)" alt="Discord"></a>
<a href="https://github.com/NexDatawork/data-agents/stargazers"><img src="https://img.shields.io/github/stars/NexDatawork/data-agents?style=social" alt="GitHub Stars"></a>
<a href="https://huggingface.co/NexDatawork">
 <img alt="Hugging Face" src="https://img.shields.io/badge/Hugging%20Face-Models%20%26%20Datasets?logo=huggingface&color=rgb(90, 42, 184)">
</a>


 </div>

</div>

---

## Table of Contents

- [Overview](#overview)
- [Try It Now](#-try-it-now)
- [Features and Workflow](#features-and-workflow)
- [Architecture](#architecture)
- [Data Agent Dataflow](#data-agent-dataflow)
- [Use Case](#use-case)
- [Demo Datasets](#demo-datasets)
- [Requirements and Quickstart](#requirements-and-quickstart)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**NexDatawork** is an AI-powered data agent designed to simplify data engineering and analytics tasks without requiring users to write code. It leverages LangChain, LangGraph, and Azure OpenAI to provide:

- **Automated Data Analysis** - Upload CSVs and receive comprehensive insights
- **Natural Language Queries** - Ask questions in plain English
- **SQL Generation** - Automatically create optimized SQL queries
- **ETL Pipeline Creation** - Generate data transformation code
- **Web Scraping** - Extract data from the web using AI

Whether you are a data analyst, business user, or data engineer, NexDatawork accelerates your workflow by automating repetitive tasks and providing explainable AI-driven insights.

---

## 🚀 Try It Now

### Option 1: Hugging Face Sandbox (No Setup Required)

**Test the data agent instantly** by clicking the Hugging Face badge above or visiting our [Hugging Face Space](https://huggingface.co/NexDatawork). No local installation needed!

[![Open in Hugging Face](https://img.shields.io/badge/🤗%20Hugging%20Face-Try%20Demo-yellow)](https://huggingface.co/NexDatawork)

### Option 2: Run the Notebook Locally

For a step-by-step walkthrough with detailed outputs:

1. Clone the repository
2. Open [`examples/data_agent_demo.ipynb`](examples/data_agent_demo.ipynb)
3. Run cells sequentially to see line-by-line results
4. Experiment with your own data and prompts

### Option 3: Contribute to the Notebook

Want to improve the agent? You can:
- Fork the repository
- Modify the notebook in `examples/data_agent_demo.ipynb`
- Add new features or improve existing functionality
- Submit a pull request with your improvements

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

---

## Features and Workflow

### Key Features

| Feature | Description |
|---------|-------------|
| Explainable AI | Full reasoning trace for every analysis |
| Dashboard and Export | Interactive visualizations with PDF export |
| Seamless Workflow | Upload, Analyze, Visualize in minutes |
| Contextual Intelligence | Industry and topic-aware analysis |
| Chat Interface | Refine results through conversation |
| Web Scraping | AI-powered data extraction from websites |

### Workflow

**Step 1: Upload your data**

Choose the **Data Upload** menu and select CSV files from your computer or drag and drop.

<image src='assets/image.png' alt='uploading data' width=250>

**Step 2: Specify your requirements**

Select an **Industry**, **Topics**, and **Requirements** for better, more targeted results.

**Step 3: Receive analyzed data**

- **Data Brain** tab: Summary, insights, and methodology
- **Dashboard** tab: Graphs and statistical overview
- **Chat** tab: Ask questions about your data

<image src='assets/image-1.png' alt='analysis results' width=300>

---

## Architecture

NexDatawork uses a modular agent-based architecture built on LangChain and LangGraph:

### Component Breakdown

| Layer | Components | Purpose |
|-------|-----------|---------|
| **Frontend** | Next.js, Gradio, Radix UI | User interface and visualization |
| **AI Agents** | DataFrame, SQL, ETL, Web Scrape | Task-specific processing |
| **LLM and Tools** | Azure OpenAI, LangChain, LangGraph | AI inference and orchestration |
| **Data** | CSV, SQLite, Supabase, Pandas | Storage and manipulation |

### Architecture Diagram

```
+--------------------------------------------------------------------------+
|                         NEXDATAWORK ARCHITECTURE                          |
+--------------------------------------------------------------------------+

+--------------------------------------------------------------------------+
|                            FRONTEND LAYER                                 |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
|  |  Next.js  |  |  Gradio   |  | Radix UI  |  | Recharts  |              |
|  |  Web App  |  | Interface |  | Components|  |  Charts   |              |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
+--------------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------------+
|                            AI AGENT LAYER                                 |
|  +--------------------------------------------------------------------+  |
|  |                      AI_tools Coordinator                          |  |
|  |   Manages agent history, coordinates pipelines, stores results     |  |
|  +--------------------------------------------------------------------+  |
|                                  |                                        |
|         +------------------------+------------------------+               |
|         v                        v                        v               |
|  +-----------+            +-----------+            +-----------+          |
|  | DataFrame |            |    SQL    |            | Web Scrape|          |
|  |   Agent   |            |   Agent   |            |   Agent   |          |
|  +-----------+            +-----------+            +-----------+          |
+--------------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------------+
|                          LLM & TOOLS LAYER                                |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
|  |Azure OpenAI|  | LangChain |  | LangGraph |  | SQLAlchemy|              |
|  |  (GPT-4)  |  |  Agents   |  |   ReAct   |  |  SQLite   |              |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
+--------------------------------------------------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------------+
|                            DATA LAYER                                     |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
|  | CSV Files |  |  SQLite   |  | Supabase  |  |  Pandas   |              |
|  | (Upload)  |  | (Runtime) |  | (Storage) |  | DataFrames|              |
|  +-----------+  +-----------+  +-----------+  +-----------+              |
+--------------------------------------------------------------------------+
```

---

## Data Agent Dataflow

This diagram illustrates how data flows through the NexDatawork agent system:

```
                             +---------------+
                             |  USER INPUT   |
                             |  -----------  |
                             |  - CSV Files  |
                             |  - Question   |
                             |  - Parameters |
                             +-------+-------+
                                     |
                                     v
                   +-------------------------------------+
                   |         INPUT PROCESSING            |
                   |  pd.read_csv() -> pd.concat()       |
                   |  Merge multiple files into one DF   |
                   +------------------+------------------+
                                      |
                     +----------------+----------------+
                     v                v                v
             +-----------+    +-----------+    +-----------+
             |  ANALYZE  |    | SQL QUERY |    | WEB SCRAPE|
             |ask_agent()|    |sql_pipe() |    |web_scrap()|
             +-----+-----+    +-----+-----+    +-----+-----+
                   |                |                |
                   v                v                v
   +-------------------+ +------------------+ +------------------+
   |   PANDAS AGENT    | |    SQL AGENT     | |  SCRAPING AGENT  |
   |  - Parse columns  | |  - create_db()   | |  - SmartScraper  |
   |  - Infer types    | |  - SQLite write  | |  - Keyword parse |
   |  - Multi-method   | |  - SQLToolkit    | |  - Data extract  |
   +--------+----------+ +--------+---------+ +--------+---------+
            |                     |                    |
            +---------------------+--------------------+
                                  |
                                  v
                   +-------------------------------------+
                   |          LLM PROCESSING             |
                   |  Azure OpenAI (GPT-4)               |
                   |  - Streaming enabled                |
                   |  - Callback handlers                |
                   +------------------+------------------+
                                      |
                                      v
                   +-------------------------------------+
                   |         OUTPUT GENERATION           |
                   |  - Markdown reports                 |
                   |  - SQL queries                      |
                   |  - ETL Python code                  |
                   +------------------+------------------+
                                      |
                     +----------------+----------------+
                     v                v                v
             +-----------+    +-----------+    +-----------+
             | DATA BRAIN|    | DASHBOARD |    |   CHAT    |
             | - Summary |    | - Charts  |    | - Q&A     |
             | - Insights|    | - Stats   |    | - Refine  |
             +-----------+    +-----------+    +-----------+
```

### Dataflow Summary

| Stage | Input | Process | Output |
|-------|-------|---------|--------|
| **1. Input** | CSV files, natural language question | File parsing, concatenation | Unified DataFrame |
| **2. Routing** | User action selection | Route to appropriate agent | Agent invocation |
| **3. Analysis** | DataFrame + prompt | Pandas agent with LLM | Insights, recommendations |
| **4. SQL** | DataFrame to SQLite | ReAct agent with SQL toolkit | SQL queries, results |
| **5. Scraping** | URL/keywords | SmartScraper tool | Extracted data |
| **6. ETL** | Raw data | Preview, Transform, Generate | Python code |
| **7. Output** | Agent results | Format and display | Reports, visualizations |

---

## Use Case

After analysis, results are displayed in two main tabs:

### Data Brain

1) **Executive Summary** - General overview and methodology

<p align='center'>
<image src='assets/executive_summary.png' alt='executive summary' width=500>
</p>

2) **Business Insights** - Recommendations and opportunities

<p align='center'>
<image src='assets/business_insights.png' alt='business insights' width=500>
</p>

3) **Statistical Analysis** - Detailed data evidence and distributions

<p align='center'>
<image src='assets/Methodology.png' alt='Methodology' width=500 />
<image src='assets/Data_evidence.png' alt='Data evidence' width=500 />
<image src='assets/Statistical_insights.png' alt='Statistical insights' width=500 />
<image src='assets/categorical_distribution.png' alt='categorical distribution' width=500 />
</p>

### Dashboard

Quick overview with key metrics:

* **File Information**
<p align='center'>
<image src='assets/file_information.png' alt='file_information' width=500 />
</p>

* **Column Types** - Numerical, categorical, temporal breakdown
* **Data Quality and Statistical Summary**
<p align='center'>
 <image src='assets/analysis_summary.png' alt='analysis_summary' width=500 />
</p>

* **Visualizations**
<p align='center'>
 <image src='assets/graph1.png' alt='graph1' width=225 />
 <image src='assets/graph2.png' alt='graph2' width=250 />
 <image src='assets/graph3.png' alt='graph3' width=225 />
</p>

---

## Demo Datasets

This repository includes demo datasets for testing. See [data/README.md](data/README.md) for details.

| Dataset | Use Case | Key Columns |
|---------|----------|-------------|
| workflow_painpoints_demo.csv | Workflow analysis | step_name, time_spent, had_error |
| cafe_sales.csv | Point-of-sale analysis | product_category, quantity, total_price |
| spotify_churn_dataset.csv | Churn modeling | subscription_type, listening_hours, is_churned |
| Walmart.csv | Retail sales patterns | store, weekly_sales, is_holiday |
| customer_support_tickets.csv | Support analytics | priority, status, resolution_time |
| product_reviews_demo.csv | Sentiment analysis | rating, review_text, verified_purchase |

> **Note:** All demo datasets are for demonstration and testing purposes only.

---

## Requirements and Quickstart

### Prerequisites

| Requirement | Description |
|-------------|-------------|
| [Node.js](https://nodejs.org/en) | v18+ recommended |
| [Python](https://python.org) | 3.10+ for agent scripts |
| [Supabase](https://supabase.com/) | Database backend |
| [OpenAI/Azure](https://platform.openai.com/) | LLM API access |

### Environment Variables

Create a .env file (see [.env.example](.env.example)):

```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
OPENAI_API_KEY=your_openai_key

# For Azure OpenAI (optional)
AZURE_OPENAI_ENDPOINT=your_azure_endpoint
AZURE_OPENAI_API_KEY=your_azure_key
```

### Quickstart

```bash
# Clone the repository
git clone https://github.com/NexDatawork/data-agents.git
cd data-agents

# Copy environment file and add your keys
cp .env.example .env

# Install dependencies
npm install

# Start the development server
npm run dev
```

### Python Agent Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

---

## Project Structure

```
data-agents/
|-- assets/                  # Images and static assets
|   +-- public/              # Public assets
|-- data/                    # Demo CSV datasets
|   +-- README.md            # Dataset documentation
|-- examples/                # Example notebooks
|   +-- data_agent_demo.ipynb
|-- src/                     # Source code (Python agents)
|   |-- agents/              # AI agent implementations
|   |-- prompts/             # LLM prompt templates
|   +-- utils/               # Helper utilities
|-- .env.example             # Environment template
|-- CONTRIBUTING.md          # Contribution guidelines
|-- LICENSE                  # Apache 2.0 license
|-- README.md                # This file
|-- REQUIREMENTS.md          # Project requirements
|-- package.json             # Node.js dependencies
|-- requirements.txt         # Python dependencies
+-- next.config.mjs          # Next.js configuration
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick links:
- [Report a Bug](https://github.com/NexDatawork/data-agents/issues/new?template=bug_report.yml)
- [Request a Feature](https://github.com/NexDatawork/data-agents/issues/new?template=feature_request.yml)
- [Join Discord](https://discord.gg/Tb55tT5UtZ)

---

## License

This project is licensed under the [Apache 2.0 License](LICENSE).

---

<div align="center">

**[Website](https://www.nexdatawork.io)** | **[Documentation](https://github.com/NexDatawork/data-agents/wiki)** | **[Discord](https://discord.gg/Tb55tT5UtZ)** | **[Hugging Face](https://huggingface.co/NexDatawork)**

Made with love by the NexDatawork team

</div>
