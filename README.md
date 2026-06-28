# GeoIntel AI — Property Geothermal Suitability Analyzer

A local Streamlit MVP that evaluates residential and commercial properties as candidates for geothermal heat pump installation.

## Features

- Property input form (residential or commercial)
- Suitability score (0–100) with weighted factors
- Financial estimates: installation cost range, annual savings, payback period
- Interactive charts (cost comparison, 20-year savings timeline)
- AI Recommendation section with plain-English analysis
- Sales Proposal Draft with one-click download
- Sidebar quick-load for sample properties

## Setup & Run

### 1. Create a virtual environment

```bash
cd geothermal-property-ai
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Streamlit app

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

## Project Structure

```
geothermal-property-ai/
├── app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
├── sample_properties.json  # Example properties for quick demo
└── README.md               # This file
```

## Calculation Methodology

All numbers are illustrative estimates based on published industry averages:

| Factor | Assumption |
|--------|-----------|
| Installation cost (residential) | $12–$22 per sq ft |
| Installation cost (commercial) | $18–$30 per sq ft |
| HVAC share of energy bill | 55% (residential), 60% (commercial) |
| Energy savings from geothermal | 40–65% of HVAC costs |
| Federal ITC | 30% (Inflation Reduction Act) — not applied automatically |

A licensed geothermal contractor must perform a formal site assessment before any installation decision.
