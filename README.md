# GeoIntel AI — Property Geothermal Suitability Analyzer

**AI-Assisted Property Geothermal Suitability Analyzer**
Version 0.2 — Demo Prototype
Developed by Xtreme Intelligence Inc.

> GeoIntel AI helps evaluate whether a residential or commercial property may be a good
> candidate for geothermal heating and cooling by estimating suitability, installation cost,
> savings potential, payback period, and next-step recommendations.

---

## Version 0.2 — Feature List

| Feature | Description |
|---|---|
| Polished branding | Product name, version, tagline, and company attribution throughout |
| 7-tab layout | Property Inputs · Executive Dashboard · Financial Analysis · Risk Factors · Site Assessment Checklist · Sales Proposal Draft · Methodology |
| Sidebar sample loader | Load any of 3 sample properties to instantly demo the tool |
| Input validation | Hard errors for invalid data; soft warnings for edge cases |
| 6-factor scoring model | Lot size, building size, energy bill, year built, property type, HVAC opportunity |
| Plain-English score explanation | Tells the user exactly what drove their score |
| Executive Dashboard | Metric cards + category banner + recommendation summary |
| Financial scenarios table | Low / mid / high installation cost, savings, and payback |
| 3 charts | Energy cost comparison · Installation cost scenarios · 20-year savings timeline |
| Dynamic risk factors | Risk list generated from inputs with severity levels (High / Medium / Low) |
| Tailored site checklist | Checklist adapts based on lot size, building age, and property type |
| Sales Proposal Draft | Polished, editable consultant-style proposal from Xtreme Intelligence Inc. |
| Methodology tab | Explains assumptions, scoring model, limitations, and version roadmap |
| Notes field | Optional property context captured and included in outputs |
| Download proposal | One-click .txt export of the proposal |

---

## Setup Instructions

### Requirements

- macOS (Intel or Apple Silicon)
- Python 3.11 or later
- No API keys required
- No internet connection required — fully local

### Step 1 — Navigate to the project folder

```bash
cd ~/Projects/geothermal-property-ai
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv
```

### Step 3 — Activate the virtual environment

```bash
source venv/bin/activate
```

### Step 4 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 5 — Run the app

```bash
streamlit run app.py
```

The app opens automatically at **http://localhost:8501**

---

## How to Run the App (Quick Reference)

Each time you want to run the app after setup:

```bash
cd ~/Projects/geothermal-property-ai
source venv/bin/activate
streamlit run app.py
```

---

## 3-Minute Demo Script

Use this script to show the tool to a client, contractor, realtor, or stakeholder.

### 0:00 — Open the app and introduce it

> "This is GeoIntel AI — a prototype tool we built to quickly assess whether a property
> is a strong candidate for geothermal heating and cooling. It takes about 30 seconds to
> run and outputs a suitability score, cost estimate, risk factors, and a proposal draft."

### 0:20 — Load the strong residential candidate

1. In the left sidebar, open **Sample Properties**
2. Select **Residential Strong Candidate — Clarksville, MD**
3. The form fills in automatically

### 0:35 — Click Analyze Property

1. Go to the **Property Inputs** tab
2. Scroll down and click **Analyze Property**
3. The green banner confirms results are ready

### 0:50 — Walk through the Executive Dashboard

1. Click **Executive Dashboard**
2. Point out:
   - The **Excellent Candidate** label and green icon
   - The six metric cards (score, category, cost, savings, payback, energy cost)
   - The score breakdown bar chart
   - The recommendation paragraph

> "In about 30 seconds we know this is a strong candidate with a payback period around
> X years before incentives. With the 30% federal tax credit, that drops significantly."

### 1:30 — Show Financial Analysis

1. Click **Financial Analysis**
2. Show the scenarios table (low / mid / high)
3. Point to the energy cost comparison chart
4. Point to the 20-year savings timeline

> "This chart shows where the break-even point is. After that, it's pure savings."

### 2:00 — Show Risk Factors

1. Click **Risk Factors**
2. Expand one or two items
3. Mention that these are generated automatically from the inputs

> "Every property gets a tailored risk list — a contractor would use this as a starting
> point for the site visit conversation."

### 2:20 — Show the Proposal

1. Click **Sales Proposal Draft**
2. Show the auto-generated proposal text
3. Click **Download as .txt** to demo the export

> "This gives us a professional first draft for the property owner in under a minute."

### 2:45 — Load the weak candidate (optional)

1. Sidebar → **Residential Weak Candidate — Small Lot**
2. Click Analyze → Executive Dashboard
3. Show the Low Suitability rating and what changed

### 3:00 — Wrap up

> "Version 0.2 is a local prototype. Future versions will connect to parcel data,
> utility rate databases, and Maryland incentive programs — and generate a formal PDF
> proposal. We're building toward a full lead generation and proposal platform."

---

## Sample Property Test Cases

| Property | Expected Score | Expected Category |
|---|---|---|
| Residential Strong Candidate — Clarksville, MD | 80–95 | Excellent Candidate |
| Residential Weak Candidate — Small Lot | 20–40 | Low Suitability |
| Commercial Medical Office — Columbia, MD | 65–80 | Good / Excellent Candidate |

---

## Project Structure

```
geothermal-property-ai/
├── app.py                   Main Streamlit application (v0.2)
├── requirements.txt         Python dependencies
├── sample_properties.json   Three demo properties
└── README.md                This file
```

---

## Known Limitations (v0.2)

- All calculations use simplified industry averages — actual costs vary by location, soil type, and contractor
- Subsurface conditions (soil, rock, groundwater) are not modeled
- Does not connect to real parcel, zoning, or permit databases
- Does not include actual utility rate data or time-of-use pricing
- Does not model loan scenarios, NPV, or IRR
- Savings estimates do not account for electricity price inflation
- Federal and state incentives are noted but not applied to the financial model

---

## Version Roadmap

| Version | Planned Feature |
|---|---|
| v0.3 | PDF proposal export |
| v0.4 | Maryland incentive estimator (static lookup table) |
| v0.5 | Property / parcel data lookup (public data sources) |
| v1.0 | SaaS-style lead generation and formal proposal platform |
