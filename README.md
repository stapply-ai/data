# 🚀 Stapply Job Data Aggregator

<div align="center">

**A powerful, open-source job aggregator that collects job postings from multiple ATS platforms and makes them publicly available.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Open%20Source-green.svg)](LICENSE)

[Features](#-features) • [Quick Start](#-quick-start) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📊 Public Data

The aggregated job data is available at: **https://storage.stapply.ai/jobs.csv**

This CSV is updated regularly and contains job postings from all supported platforms.

## ✨ Features

- **🌐 Multi-Platform Support** - Scrape jobs from 5+ different ATS platforms (Ashby, Greenhouse, Lever, Workable, Rippling)
- **🔍 Smart Discovery** - Multiple discovery methods to find companies using ATS platforms
- **📦 Structured Data** - Clean, normalized job data with consistent schema across platforms
- **🔄 Incremental Processing** - Checkpoint system prevents duplicate processing
- **📈 Job Lifecycle Tracking** - Automatically detect and mark inactive jobs
- **🎯 Semantic Search** - OpenAI embeddings for job title and description (Ashby)
- **🐳 Self-Hosted Options** - Use SearXNG for unlimited discovery without API limits
- **📝 Export Formats** - CSV exports with automatic diff tracking for new/updated jobs

## 🏗️ Architecture

The project follows a modular, platform-based architecture:

```
data/
├── 📁 Platform Modules (ashby/, greenhouse/, lever/, workable/)
│   ├── main.py              # Platform-specific scraper
│   ├── export_to_csv.py     # CSV export utility
│   ├── companies/           # JSON files (one per company)
│   ├── jobs.csv             # Platform-specific job export
│   └── *_companies.csv      # Company URL registry
│
├── 📁 Core Components
│   ├── models/              # Pydantic data models for each platform
│   ├── classifier/          # Job classification tools
│   ├── searxng-docker/      # SearXNG self-hosted setup
│   └── gather_jobs.py       # Job consolidation utility
│
├── 🔍 Discovery Scripts
│   ├── searxng_discovery.py      # Self-hosted search (unlimited!)
│   ├── discovery.py              # Discovery utilities
│   └── [other discovery methods]
│
└── 📄 Configuration
    ├── pyproject.toml       # Python dependencies
    ├── env.example           # Environment variables template
    └── README.md            # This file
```

### Data Flow

1. **Discovery** → Find companies using ATS platforms via search APIs
2. **Scraping** → Fetch jobs from each company's ATS API (saved as JSON)
3. **Export** → Convert JSON to CSV format with standardized schema
4. **Consolidation** → Merge all platform CSVs into unified `jobs.csv`
5. **Processing** → Optional: Save to PostgreSQL with embeddings

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- PostgreSQL (optional, for database processing)
- SearXNG instance (optional, for unlimited discovery)

### Installation

```bash
# Clone the repository
git clone https://github.com/stapply-ai/data.git
cd data

# Install dependencies using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file from the example:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Required for job processing and embeddings
DATABASE_URL=postgresql://user:pass@host:port/dbname
OPENAI_API_KEY=sk-...

# Optional: Discovery methods
SEARXNG_URL=http://localhost:8080        # Self-hosted search (unlimited!)
SERPAPI_API_KEY=your_serpapi_key        # SerpAPI for discovery
FIRECRAWL_API_KEY=fc-your_key           # Firecrawl search API
GOOGLE_API_KEY=your_google_key          # Google Custom Search API
GOOGLE_CSE_ID=your_cse_id               # Custom Search Engine ID
BING_API_KEY=your_bing_key              # Bing Search API
```

## 📖 Usage

### Job Scraping

Scrape jobs from discovered companies:

```bash
# Ashby
cd ashby
python main.py              # Scrapes jobs to companies/ directory as JSON
python export_to_csv.py     # Exports jobs from JSON to jobs.csv

# Greenhouse
cd greenhouse
python main.py
python export_to_csv.py

# Lever
cd lever
python main.py
python export_to_csv.py

# Workable
cd workable
python main.py
python export_to_csv.py
```

### Company Discovery

Find more companies using different discovery methods:

#### Option 1: SearXNG Discovery (Recommended) ⭐

Self-hosted search with unlimited queries:

```bash
# Setup: Follow SEARXNG_SETUP.md (10 minutes)
# Then discover companies:
python searxng_discovery.py --platform all --max-queries 20
python searxng_discovery.py --platform ashby --pages 10
```

**Advantages:**
- Unlimited queries (no rate limits!)
- No API keys needed
- Privacy-focused
- Aggregates from multiple search engines
- Can run on localhost or VPS


### Consolidate Jobs

Merge all platform CSVs into a single file:

```bash
python gather_jobs.py
```

This creates a unified `jobs.csv` at the root with jobs from all platforms.

## 🛠️ Tech Stack

- **Python 3.12+** - Modern Python features
- **aiohttp** - Async HTTP client for concurrent scraping
- **Pydantic** - Data validation and modeling
- **SQLAlchemy** - Database ORM
- **PostgreSQL** - Data storage (optional)
- **OpenAI API** - Text embeddings for semantic search
- **pandas** - Data processing and CSV handling
- **SearXNG** - Self-hosted metasearch engine

## 📚 Documentation

- **[SEARXNG_SETUP.md](SEARXNG_SETUP.md)** - Complete guide to setting up SearXNG
- **[env.example](env.example)** - Environment variables reference

## 🤝 Contributing

We welcome contributions! This project thrives on community involvement. Here are several ways you can help:

### 🎯 Ways to Contribute

#### 1. Add More Companies

Help us discover more companies using ATS platforms:

1. Find companies using ATS platforms (visit careers pages, check job boards)
2. Add URLs to the appropriate CSV:
   - `ashby/companies.csv`
   - `greenhouse/greenhouse_companies.csv`
   - `lever/lever_companies.csv`
   - `workable/workable_companies.csv`
3. Submit a pull request

#### 2. Improve Discovery Scripts

- Add new search strategies to discovery scripts
- Optimize query patterns for better results
- Add support for new discovery APIs
- Improve error handling and retry logic

#### 3. Add New ATS Platforms

Help us support more platforms:

1. Create a new platform directory (e.g., `rippling/`)
2. Implement scraper in `main.py`
3. Add Pydantic models in `models/`
4. Add platform to discovery scripts
5. Update documentation

#### 4. Enhance Data Quality

- Improve job data normalization
- Add data validation
- Enhance job classification
- Add more metadata fields

#### 5. Documentation & Examples

- Improve documentation
- Add code examples
- Create tutorials
- Fix typos and clarify instructions

#### 6. Bug Reports & Feature Requests

- Report bugs via GitHub issues
- Suggest new features
- Share your use cases

### 🚀 Getting Started with Contributions

1. **Fork the repository**
2. **Create a branch** for your contribution:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and test them
4. **Commit with clear messages**:
   ```bash
   git commit -m "Add: description of your changes"
   ```
5. **Push and create a pull request**

### 📋 Contribution Guidelines

- Follow existing code style and patterns
- Add comments for complex logic
- Test your changes before submitting
- Update documentation if needed
- Keep pull requests focused and atomic

### 💡 Ideas for Contributions

- [ ] Add support for more ATS platforms (Rippling, SmartRecruiters, etc.)
- [ ] Improve error handling and retry mechanisms
- [ ] Add data validation and quality checks
- [ ] Create a web dashboard for monitoring
- [ ] Add more discovery methods
- [ ] Improve job classification
- [ ] Add support for more export formats (JSON, Parquet, etc.)
- [ ] Create Docker setup for easy deployment
- [ ] Add CI/CD pipeline
- [ ] Improve documentation and examples

## 📊 Supported Platforms

| Platform | Status | Companies | Jobs |
|----------|--------|-----------|------|
| **Ashby** | ✅ Active | 1,000+ | 10,000+ |
| **Greenhouse** | ✅ Active | 500+ | 5,000+ |
| **Lever** | ✅ Active | 300+ | 3,000+ |
| **Workable** | ✅ Active | 200+ | 2,000+ |
| **Rippling** | 🚧 Coming Soon | - | - |

## 🔧 Development

### Project Structure

Each platform module follows a consistent structure:

- **`main.py`** - Main scraper that fetches jobs from ATS APIs
- **`export_to_csv.py`** - Exports JSON job data to CSV format
- **`companies/`** - Directory containing JSON files (one per company)
- **`jobs.csv`** - Platform-specific job export
- **`*_companies.csv`** - Registry of company URLs to scrape

### Key Concepts

- **Checkpoint System** - Prevents duplicate processing by tracking last run state
- **Incremental Updates** - Only processes new or updated jobs
- **JSON Storage** - Raw job data stored as JSON files for flexibility
- **CSV Export** - Standardized CSV format for easy consumption
- **Diff Tracking** - Automatic detection of new/updated jobs

## 📝 License

This project is open source. Contributions are welcome!

## 🌐 Links

- **Public Jobs CSV**: https://storage.stapply.ai/jobs.csv
- **Website**: https://stapply.ai
- **Issues**: [GitHub Issues](https://github.com/stapply-ai/data/issues)

---

<div align="center">

**Made with ❤️ by the Stapply team**

*Help us build the most comprehensive job data aggregator!*

[⭐ Star us on GitHub](https://github.com/stapply-ai/data) • [🐛 Report Issues](https://github.com/stapply-ai/data/issues) • [💬 Discussions](https://github.com/stapply-ai/data/discussions)

</div>
