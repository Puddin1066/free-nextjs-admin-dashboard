# ADVScout - Modular Venture Scout Platform

ADVScout is a modular venture scouting platform that identifies revenue-stage companies using AI enrichment, free APIs, and advanced scoring algorithms.

## Features

- **Modular Architecture**: Each component is a self-contained Python script
- **AI Enrichment**: GPT-powered company analysis and insights
- **Free API Integration**: NIH, OpenCorporates, and other public data sources
- **Scoring Engine**: Advanced algorithms to identify revenue-stage companies
- **Comparable Analysis**: Automated competitive landscape mapping
- **Decision-Maker Mapping**: Contact identification and organizational mapping
- **Comprehensive Reporting**: Markdown and CSV output formats

## Architecture

```
advscout/
├── core/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging utilities
│   └── utils.py           # Common utilities
├── modules/
│   ├── __init__.py
│   ├── enrichment.py      # GPT-powered enrichment
│   ├── api_collector.py   # Free API data collection
│   ├── scoring.py         # Company scoring algorithms
│   ├── comparables.py     # Comparable analysis
│   ├── contacts.py        # Decision-maker mapping
│   └── reporting.py       # Report generation
├── data/
│   ├── companies.csv      # Input company data
│   ├── templates/         # Report templates
│   └── output/            # Generated reports
├── scripts/
│   ├── run_full_scout.py  # Complete scouting pipeline
│   ├── run_enrichment.py  # Enrichment only
│   ├── run_scoring.py     # Scoring only
│   └── run_reports.py     # Reporting only
├── requirements.txt
└── README.md
```

## Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure API Keys**
```bash
cp config.example.py config.py
# Edit config.py with your API keys
```

3. **Run Full Scout**
```bash
python scripts/run_full_scout.py --input data/companies.csv --output data/output/
```

4. **Run Individual Modules**
```bash
# Enrichment only
python scripts/run_enrichment.py --company "TechCorp Inc"

# Scoring only
python scripts/run_scoring.py --input data/enriched_companies.csv

# Generate reports
python scripts/run_reports.py --input data/scored_companies.csv
```

## Module Overview

### 1. **Enrichment Module** (`modules/enrichment.py`)
- GPT-powered company analysis
- Business model identification
- Market positioning insights
- Technology stack analysis

### 2. **API Collector Module** (`modules/api_collector.py`)
- NIH database integration
- OpenCorporates data collection
- Public financial data
- Regulatory filings

### 3. **Scoring Module** (`modules/scoring.py`)
- Revenue-stage identification
- Growth trajectory analysis
- Market opportunity scoring
- Risk assessment

### 4. **Comparables Module** (`modules/comparables.py`)
- Competitive landscape mapping
- Market positioning analysis
- Valuation benchmarking
- Growth comparison

### 5. **Contacts Module** (`modules/contacts.py`)
- Decision-maker identification
- Organizational mapping
- Contact information enrichment
- Communication preferences

### 6. **Reporting Module** (`modules/reporting.py`)
- Markdown report generation
- CSV data export
- Executive summaries
- Visual charts and graphs

## Configuration

Create a `config.py` file with your API keys:

```python
# API Configuration
OPENAI_API_KEY = "your-openai-key"
NIH_API_KEY = "your-nih-key"  # If required
OPENCORPORATES_API_KEY = "your-opencorporates-key"  # If required

# Scoring Configuration
REVENUE_STAGE_THRESHOLD = 1000000  # $1M ARR
GROWTH_RATE_THRESHOLD = 0.5  # 50% YoY growth
MARKET_SIZE_THRESHOLD = 1000000000  # $1B market

# Output Configuration
OUTPUT_FORMAT = ["markdown", "csv"]
REPORT_TEMPLATE = "templates/scout_report.md"
```

## Usage Examples

### Full Pipeline
```bash
python scripts/run_full_scout.py \
  --input data/companies.csv \
  --output data/output/ \
  --config config.py
```

### Individual Modules
```bash
# Enrich specific company
python modules/enrichment.py --company "Acme Corp" --output enriched_acme.json

# Score companies from CSV
python modules/scoring.py --input companies.csv --output scored_companies.csv

# Generate comparable analysis
python modules/comparables.py --target "TechCorp" --industry "SaaS" --output comparables.md
```

## Output Examples

### Markdown Report
- Executive Summary
- Company Overview
- Market Analysis
- Competitive Landscape
- Financial Projections
- Risk Assessment
- Recommendation

### CSV Export
- Company Name, Industry, Revenue Stage, Score, Risk Level
- Contact Information, Decision Makers, Email, Phone
- Comparable Companies, Valuation, Growth Rate

## Requirements

- Python 3.8+
- OpenAI API key
- Internet connection for API calls
- CSV input file with company data

## License

MIT License - see LICENSE file for details.