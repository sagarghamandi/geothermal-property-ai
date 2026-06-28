"""
GeoIntel AI - Property Geothermal Suitability Analyzer
A Streamlit MVP for evaluating properties as geothermal installation candidates.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="GeoIntel AI - Property Geothermal Suitability Analyzer",
    page_icon="🌍",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────

# Installation cost per sq ft (residential vs commercial)
RESIDENTIAL_COST_LOW_PER_SQFT = 12   # $/sqft low estimate
RESIDENTIAL_COST_HIGH_PER_SQFT = 22  # $/sqft high estimate
COMMERCIAL_COST_LOW_PER_SQFT = 18
COMMERCIAL_COST_HIGH_PER_SQFT = 30

# Geothermal typically cuts HVAC energy use by 40–70 %
# We apply these to the estimated HVAC portion of the energy bill (~50–65 %)
RESIDENTIAL_HVAC_FRACTION = 0.55   # share of energy bill that is HVAC
COMMERCIAL_HVAC_FRACTION = 0.60
SAVINGS_RATE_LOW = 0.40            # conservative savings on HVAC portion
SAVINGS_RATE_HIGH = 0.65           # optimistic savings on HVAC portion

# Minimum lot size thresholds (acres) for horizontal vs vertical loops
HORIZONTAL_LOOP_MIN_ACRES = 0.5    # horizontal ground loop needs space
VERTICAL_LOOP_MIN_ACRES = 0.10     # vertical borehole needs much less

# ── Helper: load sample properties ───────────────────────────────────────────

@st.cache_data
def load_samples():
    path = Path(__file__).parent / "sample_properties.json"
    with open(path) as f:
        return json.load(f)

# ── Core calculations ─────────────────────────────────────────────────────────

def calc_annual_energy_cost(monthly_bill: float) -> float:
    """Annualise the monthly energy bill."""
    return monthly_bill * 12


def calc_installation_cost(sqft: float, prop_type: str) -> tuple[float, float]:
    """Return (low_estimate, high_estimate) for geothermal installation."""
    if prop_type == "Residential":
        low = sqft * RESIDENTIAL_COST_LOW_PER_SQFT
        high = sqft * RESIDENTIAL_COST_HIGH_PER_SQFT
    else:
        low = sqft * COMMERCIAL_COST_LOW_PER_SQFT
        high = sqft * COMMERCIAL_COST_HIGH_PER_SQFT
    return round(low), round(high)


def calc_annual_savings(annual_energy_cost: float, prop_type: str) -> tuple[float, float]:
    """Return (conservative_savings, optimistic_savings) per year."""
    hvac_frac = RESIDENTIAL_HVAC_FRACTION if prop_type == "Residential" else COMMERCIAL_HVAC_FRACTION
    hvac_cost = annual_energy_cost * hvac_frac
    low = round(hvac_cost * SAVINGS_RATE_LOW)
    high = round(hvac_cost * SAVINGS_RATE_HIGH)
    return low, high


def calc_payback(install_low: float, install_high: float,
                 savings_low: float, savings_high: float) -> tuple[float, float]:
    """Return (best_case_years, worst_case_years) simple payback period."""
    best = round(install_low / max(savings_high, 1), 1)
    worst = round(install_high / max(savings_low, 1), 1)
    return best, worst


def calc_suitability_score(
    lot_acres: float,
    sqft: float,
    prop_type: str,
    monthly_bill: float,
    year_built: int,
) -> int:
    """
    Compute a 0–100 suitability score from five weighted factors.

    Weights:
      Lot size       – 30 pts  (biggest single driver: loop field space)
      Energy bill    – 25 pts  (higher bill → more savings potential)
      Building size  – 20 pts  (sweet-spot: 1 500–5 000 sqft for residential)
      Year built     – 15 pts  (newer = better insulation, easier retrofit)
      Property type  – 10 pts  (commercial gets a slight boost; consistent demand)
    """
    score = 0

    # ── Lot size (30 pts) ─────────────────────────────────────────────────────
    if lot_acres >= 1.0:
        score += 30
    elif lot_acres >= 0.5:
        score += 22
    elif lot_acres >= VERTICAL_LOOP_MIN_ACRES:
        # Tight lot → vertical boreholefeasible but more expensive
        score += 12
    else:
        score += 3

    # ── Monthly energy bill (25 pts) ──────────────────────────────────────────
    if prop_type == "Residential":
        if monthly_bill >= 300:
            score += 25
        elif monthly_bill >= 200:
            score += 18
        elif monthly_bill >= 120:
            score += 10
        else:
            score += 3
    else:  # Commercial
        if monthly_bill >= 2000:
            score += 25
        elif monthly_bill >= 1000:
            score += 18
        elif monthly_bill >= 500:
            score += 10
        else:
            score += 3

    # ── Building size (20 pts) ────────────────────────────────────────────────
    if prop_type == "Residential":
        if 1500 <= sqft <= 5000:
            score += 20
        elif sqft > 5000:
            score += 14  # very large homes cost more but still good
        elif sqft >= 800:
            score += 10
        else:
            score += 4
    else:  # Commercial
        if sqft >= 5000:
            score += 20
        elif sqft >= 2000:
            score += 14
        else:
            score += 6

    # ── Year built (15 pts) ───────────────────────────────────────────────────
    if year_built >= 2000:
        score += 15
    elif year_built >= 1985:
        score += 10
    elif year_built >= 1970:
        score += 6
    else:
        score += 2  # very old buildings may need envelope upgrades first

    # ── Property type bonus (10 pts) ──────────────────────────────────────────
    if prop_type == "Commercial":
        score += 10   # commercial loads are heavier and more predictable
    else:
        score += 7    # residential is still great, slightly less consistent

    return min(score, 100)


def score_to_category(score: int) -> tuple[str, str]:
    """Return (label, color) for a suitability score."""
    if score >= 80:
        return "Excellent Candidate", "🟢"
    elif score >= 60:
        return "Good Candidate", "🔵"
    elif score >= 40:
        return "Needs Further Site Assessment", "🟡"
    else:
        return "Low Suitability", "🔴"


def build_loop_type(lot_acres: float) -> str:
    if lot_acres >= 0.5:
        return "Horizontal ground loop (trenching)"
    elif lot_acres >= VERTICAL_LOOP_MIN_ACRES:
        return "Vertical borehole (drilling)"
    else:
        return "Pond/lake loop or shared district system (if available)"


def generate_ai_recommendation(
    prop_type: str,
    score: int,
    category: str,
    lot_acres: float,
    sqft: float,
    year_built: int,
    monthly_bill: float,
    savings_low: float,
    savings_high: float,
    payback_best: float,
    payback_worst: float,
    loop_type: str,
    hvac_type: str,
) -> str:
    """Build a plain-English recommendation paragraph."""
    lines = []

    lines.append(
        f"Based on the information provided, this {prop_type.lower()} property "
        f"scores **{score}/100** for geothermal suitability — rated as a **{category}**."
    )

    if score >= 80:
        lines.append(
            "This property is an excellent candidate for a geothermal heat pump system. "
            "The combination of available land, energy consumption profile, and building "
            "characteristics all align well with a geothermal retrofit."
        )
    elif score >= 60:
        lines.append(
            "This property shows strong geothermal potential. With the right system design, "
            "the owner should expect reliable long-term performance and meaningful savings."
        )
    elif score >= 40:
        lines.append(
            "This property has moderate geothermal potential. A professional site assessment "
            "is recommended before committing — factors such as soil type, groundwater depth, "
            "and utility rates will determine final viability."
        )
    else:
        lines.append(
            "This property presents challenges for a standard geothermal installation. "
            "Limited lot size, low energy bills, or an older building envelope may reduce "
            "the return on investment. A site engineer should evaluate alternatives."
        )

    # Loop type note
    lines.append(
        f"Given the {lot_acres:.2f}-acre lot, a **{loop_type}** system is the most likely approach."
    )

    # Year built note
    if year_built < 1985:
        lines.append(
            f"The building was constructed in {year_built}. Upgrading insulation and "
            "air sealing before installing geothermal is strongly recommended — this can "
            "reduce system sizing and improve payback."
        )

    # Current HVAC note
    if "Electric" in hvac_type or "Resistance" in hvac_type:
        lines.append(
            "Replacing electric resistance heating with geothermal will likely produce "
            "the highest savings, as geothermal heat pumps deliver 3–5× more heat per "
            "kWh than strip heaters."
        )
    elif "Gas" in hvac_type or "Propane" in hvac_type:
        lines.append(
            "Transitioning from a gas or propane system to geothermal eliminates fuel "
            "price volatility and reduces carbon emissions while typically lowering "
            "operating costs."
        )

    # Savings summary
    lines.append(
        f"Projected annual savings range from **${savings_low:,}** (conservative) to "
        f"**${savings_high:,}** (optimistic), with a simple payback period of "
        f"**{payback_best}–{payback_worst} years**. Federal and state incentives "
        "(e.g., the 30 % IRA tax credit) can significantly shorten payback."
    )

    return "\n\n".join(lines)


def generate_sales_proposal(
    address: str,
    city: str,
    state: str,
    prop_type: str,
    sqft: float,
    install_low: float,
    install_high: float,
    savings_low: float,
    savings_high: float,
    payback_best: float,
    payback_worst: float,
    score: int,
    category: str,
) -> str:
    """Generate a short sales proposal paragraph for the property owner."""
    return f"""
Dear Property Owner at {address}, {city}, {state},

We are pleased to present a preliminary geothermal energy feasibility summary for your \
{prop_type.lower()} property ({sqft:,.0f} sq ft). After reviewing key property characteristics, \
your property has received a geothermal suitability score of **{score}/100** — classified as a \
**{category}**.

A geothermal heat pump system installed at this location is estimated to cost between \
**${install_low:,}** and **${install_high:,}**, depending on site conditions and final system design. \
You could realistically expect to save between **${savings_low:,} and ${savings_high:,} per year** \
on heating and cooling costs, resulting in a simple payback period of approximately \
**{payback_best} to {payback_worst} years**.

Beyond the financial returns, geothermal systems provide consistent indoor comfort, \
dramatically lower carbon emissions, and increase property value. Additionally, the current \
30% federal Investment Tax Credit (ITC) under the Inflation Reduction Act can meaningfully \
reduce your out-of-pocket cost.

We would welcome the opportunity to conduct a full on-site assessment and provide a detailed \
proposal tailored to your property. Please contact us to schedule a no-obligation site visit.

Warm regards,
GeoIntel AI Solutions Team
""".strip()


# ── UI ────────────────────────────────────────────────────────────────────────

def main():
    st.title("🌍 GeoIntel AI — Property Geothermal Suitability Analyzer")
    st.markdown(
        "Evaluate whether your residential or commercial property is a strong candidate "
        "for a geothermal heat pump system. Fill in the form below and click **Analyze**."
    )
    st.divider()

    # ── Sidebar: load a sample ────────────────────────────────────────────────
    with st.sidebar:
        st.header("Quick Start")
        st.markdown("Load a sample property to see the analyzer in action.")
        samples = load_samples()
        sample_names = ["— select a sample —"] + [s["name"] for s in samples]
        chosen = st.selectbox("Sample Properties", sample_names)
        selected_sample = None
        if chosen != "— select a sample —":
            selected_sample = next(s for s in samples if s["name"] == chosen)
        st.divider()
        st.markdown(
            "**Disclaimer:** All calculations are illustrative estimates based on "
            "industry averages. A licensed geothermal contractor must perform a "
            "formal site assessment before any installation decision."
        )

    # ── Pull defaults from sample if selected ─────────────────────────────────
    def sv(key, fallback):
        """Return value from selected sample or fallback."""
        if selected_sample and key in selected_sample:
            return selected_sample[key]
        return fallback

    # ── Input form ────────────────────────────────────────────────────────────
    with st.form("property_form"):
        st.subheader("Property Information")

        col1, col2 = st.columns(2)
        with col1:
            prop_type = st.selectbox(
                "Property Type",
                ["Residential", "Commercial"],
                index=0 if sv("property_type", "Residential") == "Residential" else 1,
            )
        with col2:
            address = st.text_input("Street Address", value=sv("address", ""))

        col3, col4, col5 = st.columns(3)
        with col3:
            city = st.text_input("City", value=sv("city", ""))
        with col4:
            state = st.text_input("State", value=sv("state", ""), max_chars=2)
        with col5:
            zip_code = st.text_input("ZIP Code", value=str(sv("zip", "")))

        st.subheader("Building Details")
        col6, col7, col8 = st.columns(3)
        with col6:
            sqft = st.number_input(
                "Building Size (sq ft)", min_value=100, max_value=500_000,
                value=int(sv("sqft", 2000)), step=100,
            )
        with col7:
            lot_acres = st.number_input(
                "Lot Size (acres)", min_value=0.01, max_value=500.0,
                value=float(sv("lot_acres", 0.5)), step=0.05, format="%.2f",
            )
        with col8:
            year_built = st.number_input(
                "Year Built", min_value=1800, max_value=2025,
                value=int(sv("year_built", 2000)), step=1,
            )

        hvac_options = [
            "Gas Furnace + Central AC",
            "Heat Pump",
            "Electric Resistance + Central AC",
            "Propane Furnace + Central AC",
            "Rooftop Units (RTUs)",
            "Boiler (Hot Water)",
            "Chiller System",
            "Mini-Split (Ductless)",
            "Other",
        ]
        default_hvac = sv("hvac_type", "Gas Furnace + Central AC")
        hvac_idx = hvac_options.index(default_hvac) if default_hvac in hvac_options else 0
        hvac_type = st.selectbox("Current HVAC System", hvac_options, index=hvac_idx)

        st.subheader("Energy & Occupancy")
        col9, col10 = st.columns(2)
        with col9:
            monthly_bill = st.number_input(
                "Estimated Monthly Energy Bill ($)",
                min_value=10, max_value=100_000,
                value=int(sv("monthly_energy_bill", 200)), step=10,
            )

        if prop_type == "Residential":
            with col10:
                occupants = st.number_input(
                    "Number of Occupants", min_value=1, max_value=50,
                    value=int(sv("occupants", 2)), step=1,
                )
            business_type = None
        else:
            with col10:
                biz_options = [
                    "Office", "Retail", "Restaurant", "Warehouse",
                    "Healthcare", "Education", "Hospitality", "Other",
                ]
                default_biz = sv("business_type", "Office")
                biz_idx = biz_options.index(default_biz) if default_biz in biz_options else 0
                business_type = st.selectbox("Business Type", biz_options, index=biz_idx)
            occupants = None

        submitted = st.form_submit_button("🔍 Analyze Property", use_container_width=True)

    # ── Results ───────────────────────────────────────────────────────────────
    if not submitted:
        st.info("Fill in the form above and click **Analyze Property** to see results.")
        return

    if not address or not city or not state:
        st.error("Please enter at least a street address, city, and state.")
        return

    # Run calculations
    annual_cost = calc_annual_energy_cost(monthly_bill)
    install_low, install_high = calc_installation_cost(sqft, prop_type)
    savings_low, savings_high = calc_annual_savings(annual_cost, prop_type)
    payback_best, payback_worst = calc_payback(install_low, install_high, savings_low, savings_high)
    score = calc_suitability_score(lot_acres, sqft, prop_type, monthly_bill, year_built)
    category, icon = score_to_category(score)
    loop_type = build_loop_type(lot_acres)

    st.divider()
    st.header(f"Results for {address}, {city}, {state} {zip_code}")

    # ── Score banner ──────────────────────────────────────────────────────────
    score_col, cat_col = st.columns([1, 2])
    with score_col:
        st.metric("Suitability Score", f"{score} / 100")
    with cat_col:
        st.markdown(f"### {icon} {category}")
        st.caption(f"Recommended loop type: {loop_type}")

    st.divider()

    # ── Financial summary ─────────────────────────────────────────────────────
    st.subheader("Financial Summary")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Annual Energy Cost", f"${annual_cost:,.0f}")
    m2.metric(
        "Installation Cost Range",
        f"${install_low:,} – ${install_high:,}",
        help="Estimate only; depends on soil, depth, and system size.",
    )
    m3.metric(
        "Est. Annual Savings",
        f"${savings_low:,} – ${savings_high:,}",
        help="Conservative to optimistic range on HVAC costs.",
    )
    m4.metric(
        "Simple Payback Period",
        f"{payback_best}–{payback_worst} yrs",
        help="Before incentives. The 30% IRA tax credit can shorten this.",
    )

    # ── Charts ────────────────────────────────────────────────────────────────
    st.subheader("Visual Breakdown")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("**Energy Cost: Before vs. After Geothermal**")
        savings_mid = (savings_low + savings_high) / 2
        remaining = annual_cost - savings_mid
        cost_df = pd.DataFrame(
            {"Scenario": ["Current Annual Cost", "After Geothermal (est.)"],
             "Annual Cost ($)": [annual_cost, max(remaining, 0)]}
        ).set_index("Scenario")
        st.bar_chart(cost_df)

    with chart_col2:
        st.markdown("**Suitability Score Breakdown (out of max points)**")
        breakdown_df = pd.DataFrame(
            {
                "Factor": ["Lot Size", "Energy Bill", "Building Size", "Year Built", "Property Type"],
                "Max Points": [30, 25, 20, 15, 10],
            }
        ).set_index("Factor")
        st.bar_chart(breakdown_df)

    # ── Payback timeline chart ────────────────────────────────────────────────
    st.markdown("**Cumulative Savings Over 20 Years (midpoint estimate)**")
    savings_mid = (savings_low + savings_high) / 2
    install_mid = (install_low + install_high) / 2
    years = list(range(0, 21))
    cumulative = [round(savings_mid * y - install_mid) for y in years]
    timeline_df = pd.DataFrame({"Year": years, "Net Cumulative Savings ($)": cumulative}).set_index("Year")
    st.line_chart(timeline_df)
    st.caption(
        f"Chart uses midpoint installation cost (${install_mid:,.0f}) and midpoint annual savings "
        f"(${savings_mid:,.0f}/yr). Break-even shown where line crosses $0."
    )

    st.divider()

    # ── AI Recommendation ─────────────────────────────────────────────────────
    st.subheader("🤖 AI Recommendation")
    recommendation = generate_ai_recommendation(
        prop_type=prop_type,
        score=score,
        category=category,
        lot_acres=lot_acres,
        sqft=sqft,
        year_built=year_built,
        monthly_bill=monthly_bill,
        savings_low=savings_low,
        savings_high=savings_high,
        payback_best=payback_best,
        payback_worst=payback_worst,
        loop_type=loop_type,
        hvac_type=hvac_type,
    )
    st.markdown(recommendation)

    st.divider()

    # ── Sales Proposal Draft ──────────────────────────────────────────────────
    st.subheader("📄 Sales Proposal Draft")
    proposal = generate_sales_proposal(
        address=address,
        city=city,
        state=state,
        prop_type=prop_type,
        sqft=sqft,
        install_low=install_low,
        install_high=install_high,
        savings_low=savings_low,
        savings_high=savings_high,
        payback_best=payback_best,
        payback_worst=payback_worst,
        score=score,
        category=category,
    )
    st.markdown(proposal)
    st.download_button(
        label="⬇️ Download Proposal as .txt",
        data=proposal,
        file_name=f"geothermal_proposal_{zip_code or 'property'}.txt",
        mime="text/plain",
    )

    st.divider()

    # ── Raw data expander ─────────────────────────────────────────────────────
    with st.expander("📊 Show All Inputs & Calculated Values"):
        data = {
            "Property Type": prop_type,
            "Address": f"{address}, {city}, {state} {zip_code}",
            "Square Footage": f"{sqft:,} sq ft",
            "Lot Size": f"{lot_acres:.2f} acres",
            "Year Built": year_built,
            "HVAC Type": hvac_type,
            "Monthly Energy Bill": f"${monthly_bill:,}",
            "Annual Energy Cost": f"${annual_cost:,}",
            "Installation Cost (Low)": f"${install_low:,}",
            "Installation Cost (High)": f"${install_high:,}",
            "Annual Savings (Low)": f"${savings_low:,}",
            "Annual Savings (High)": f"${savings_high:,}",
            "Simple Payback (Best)": f"{payback_best} years",
            "Simple Payback (Worst)": f"{payback_worst} years",
            "Suitability Score": f"{score} / 100",
            "Category": category,
            "Recommended Loop Type": loop_type,
        }
        if prop_type == "Residential":
            data["Occupants"] = occupants
        else:
            data["Business Type"] = business_type

        summary_df = pd.DataFrame(list(data.items()), columns=["Field", "Value"])
        st.dataframe(summary_df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
