"""
GeoIntel AI — Property Geothermal Suitability Analyzer
Version 0.2 — Demo Prototype
Developed by Xtreme Intelligence Inc.

An AI-assisted property analysis tool for estimating geothermal suitability,
installation cost, savings potential, payback period, and next-step recommendations.
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path

# ── Page config (must be the very first Streamlit call) ───────────────────────

st.set_page_config(
    page_title="GeoIntel AI",
    page_icon="🌍",
    layout="wide",
)

# ── App-level constants ────────────────────────────────────────────────────────

APP_VERSION  = "0.2"
CURRENT_YEAR = 2026

# Installation cost per sq ft — residential ($25–$55 industry range)
RES_COST_LOW  = 25
RES_COST_MID  = 40
RES_COST_HIGH = 55
RES_INSTALL_MIN = 20_000   # minimum realistic job size

# Installation cost per sq ft — commercial ($18–$45 industry range)
COM_COST_LOW  = 18
COM_COST_MID  = 30
COM_COST_HIGH = 45
COM_INSTALL_MIN = 40_000

# Savings rates applied to the full annual energy cost
# Residential: 35–55%, Commercial: 30–50%
RES_SAVINGS_LOW  = 0.35
RES_SAVINGS_MID  = 0.45
RES_SAVINGS_HIGH = 0.55
COM_SAVINGS_LOW  = 0.30
COM_SAVINGS_MID  = 0.40
COM_SAVINGS_HIGH = 0.50

# Lot size thresholds (acres) that determine loop type
HORIZONTAL_LOOP_MIN_ACRES = 0.50   # horizontal trenching
VERTICAL_LOOP_MIN_ACRES   = 0.10   # vertical borehole

# ── Load sample properties ─────────────────────────────────────────────────────

@st.cache_data
def load_samples() -> list[dict]:
    path = Path(__file__).parent / "sample_properties.json"
    with open(path) as f:
        return json.load(f)

# ── Core scoring ───────────────────────────────────────────────────────────────

def calculate_suitability_score(
    lot_acres: float,
    sqft: float,
    prop_type: str,
    monthly_bill: float,
    year_built: int,
    hvac_type: str,
) -> tuple[int, dict]:
    """
    Return (score 0–100, breakdown dict) using six weighted factors.

    Factor weights:
      Lot size               30 pts  — determines which loop system is feasible
      Building size          20 pts  — scale of the system and savings
      Energy bill            20 pts  — higher bill = more savings potential
      Year built             10 pts  — newer buildings retrofit more cleanly
      Property type          10 pts  — commercial loads are more predictable
      HVAC opportunity       10 pts  — older/less-efficient system = bigger gain
    """
    breakdown = {}
    total = 0

    # ── Lot size (30 pts) ─────────────────────────────────────────────────────
    if lot_acres >= 2.0:
        pts = 30
    elif lot_acres >= 1.0:
        pts = 24
    elif lot_acres >= 0.5:
        pts = 16
    elif lot_acres >= 0.1:
        pts = 8
    else:
        pts = 2   # lot too small for most standard loop systems
    total += pts
    breakdown["Lot Size (30 pts)"] = pts

    # ── Building size (20 pts) ────────────────────────────────────────────────
    if prop_type == "Residential":
        if 1_500 <= sqft <= 5_000:
            pts = 20   # ideal residential size range
        elif sqft > 5_000:
            pts = 15   # large home — higher cost but still viable
        elif sqft >= 800:
            pts = 12
        else:
            pts = 5
    else:   # Commercial
        if sqft >= 10_000:
            pts = 20
        elif sqft >= 5_000:
            pts = 16
        elif sqft >= 2_000:
            pts = 10
        else:
            pts = 5
    total += pts
    breakdown["Building Size (20 pts)"] = pts

    # ── Energy bill (20 pts) ──────────────────────────────────────────────────
    if prop_type == "Residential":
        if monthly_bill >= 400:
            pts = 20
        elif monthly_bill >= 250:
            pts = 15
        elif monthly_bill >= 150:
            pts = 10
        elif monthly_bill >= 80:
            pts = 5
        else:
            pts = 2   # very low bill — payback will be extended
    else:   # Commercial
        if monthly_bill >= 3_000:
            pts = 20
        elif monthly_bill >= 1_500:
            pts = 15
        elif monthly_bill >= 750:
            pts = 10
        elif monthly_bill >= 300:
            pts = 5
        else:
            pts = 2
    total += pts
    breakdown["Energy Bill (20 pts)"] = pts

    # ── Year built (10 pts) ───────────────────────────────────────────────────
    if year_built >= 2010:
        pts = 10   # modern envelope — straightforward retrofit
    elif year_built >= 2000:
        pts = 8
    elif year_built >= 1990:
        pts = 6
    elif year_built >= 1980:
        pts = 4
    elif year_built >= 1970:
        pts = 2
    else:
        pts = 1   # very old — envelope upgrades may be needed first
    total += pts
    breakdown["Year Built (10 pts)"] = pts

    # ── Property type (10 pts) ────────────────────────────────────────────────
    if prop_type == "Commercial":
        pts = 10   # larger, more consistent loads — strong fit for GHP
    else:
        pts = 8    # residential is excellent too
    total += pts
    breakdown["Property Type (10 pts)"] = pts

    # ── HVAC replacement opportunity (10 pts) ─────────────────────────────────
    # Higher points = bigger gain from switching to geothermal
    if "Electric Resistance" in hvac_type:
        pts = 10   # replacing strip heat with GHP is the highest-savings switch
    elif "Propane" in hvac_type:
        pts = 9
    elif "Gas Furnace" in hvac_type or "Gas" in hvac_type:
        pts = 8
    elif "Rooftop" in hvac_type or "RTU" in hvac_type:
        pts = 8
    elif "Boiler" in hvac_type:
        pts = 6
    elif "Chiller" in hvac_type:
        pts = 5
    elif "Heat Pump" in hvac_type:
        pts = 5   # already reasonably efficient — gain is smaller
    elif "Mini-Split" in hvac_type:
        pts = 5
    else:
        pts = 6
    total += pts
    breakdown["HVAC Opportunity (10 pts)"] = pts

    return min(total, 100), breakdown


def get_candidate_category(score: int) -> tuple[str, str, str]:
    """
    Map a numeric score to (category_label, icon, professional_description).
    """
    if score >= 80:
        return (
            "Excellent Candidate", "🟢",
            "This property scores highly across lot size, building profile, and energy spend. "
            "It appears to be a strong candidate for a formal geothermal feasibility review. "
            "A site visit and energy audit are recommended as near-term next steps.",
        )
    elif score >= 60:
        return (
            "Good Candidate", "🔵",
            "This property shows solid geothermal potential. One or more factors limit the top "
            "score, but with the right system design a contractor should be able to deliver "
            "reliable performance and meaningful long-term savings.",
        )
    elif score >= 40:
        return (
            "Needs Further Site Assessment", "🟡",
            "This property has moderate geothermal potential. Key variables — such as soil "
            "conditions, lot configuration, and local utility rates — should be verified "
            "before pursuing a formal proposal. A contractor site visit is the recommended "
            "first step.",
        )
    else:
        return (
            "Low Suitability", "🔴",
            "Based on the inputs provided, this property faces meaningful barriers to a "
            "cost-effective geothermal installation. Small lot size, low energy bills, or "
            "building characteristics may limit the return on investment. A site engineer "
            "can evaluate alternative approaches such as mini-split upgrades or shared "
            "district systems.",
        )


def build_loop_type(lot_acres: float) -> str:
    """Recommend the most likely loop configuration based on lot size."""
    if lot_acres >= HORIZONTAL_LOOP_MIN_ACRES:
        return "Horizontal ground loop (trenching)"
    elif lot_acres >= VERTICAL_LOOP_MIN_ACRES:
        return "Vertical borehole (drilling)"
    else:
        return "Pond/lake loop or shared district system (if available)"


# ── Financial calculations ─────────────────────────────────────────────────────

def calculate_financials(sqft: float, prop_type: str, monthly_bill: float) -> dict:
    """
    Return a dict with all financial estimates across three scenarios.

    Installation cost is based on sq ft with a minimum floor.
    Savings are a percentage of the annual energy cost (not just the HVAC portion)
    to keep the model simple and easy to explain to a non-technical audience.
    """
    annual_cost = monthly_bill * 12

    # Installation cost (low / mid / high)
    if prop_type == "Residential":
        install_low  = max(sqft * RES_COST_LOW,  RES_INSTALL_MIN)
        install_mid  = sqft * RES_COST_MID
        install_high = sqft * RES_COST_HIGH
        sl, sm, sh   = RES_SAVINGS_LOW, RES_SAVINGS_MID, RES_SAVINGS_HIGH
    else:
        install_low  = max(sqft * COM_COST_LOW,  COM_INSTALL_MIN)
        install_mid  = sqft * COM_COST_MID
        install_high = sqft * COM_COST_HIGH
        sl, sm, sh   = COM_SAVINGS_LOW, COM_SAVINGS_MID, COM_SAVINGS_HIGH

    savings_low  = annual_cost * sl
    savings_mid  = annual_cost * sm
    savings_high = annual_cost * sh

    geo_cost_low  = max(annual_cost - savings_high, 0)
    geo_cost_mid  = max(annual_cost - savings_mid,  0)
    geo_cost_high = max(annual_cost - savings_low,  0)

    def payback(install, savings):
        return round(install / max(savings, 1), 1)

    return {
        "annual_cost":   round(annual_cost),
        "install_low":   round(install_low),
        "install_mid":   round(install_mid),
        "install_high":  round(install_high),
        "savings_low":   round(savings_low),
        "savings_mid":   round(savings_mid),
        "savings_high":  round(savings_high),
        "geo_cost_low":  round(geo_cost_low),
        "geo_cost_mid":  round(geo_cost_mid),
        "geo_cost_high": round(geo_cost_high),
        "payback_best":  payback(install_low,  savings_high),
        "payback_mid":   payback(install_mid,  savings_mid),
        "payback_worst": payback(install_high, savings_low),
    }


# ── Score explanation ──────────────────────────────────────────────────────────

def build_score_explanation(
    lot_acres: float,
    sqft: float,
    prop_type: str,
    monthly_bill: float,
    year_built: int,
    hvac_type: str,
    breakdown: dict,
) -> str:
    """
    Return a bullet-by-bullet plain-English explanation of the score.
    """
    lines = []

    # Identify the two highest-scoring factors to mention in the intro
    sorted_factors = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    top_two = [f.split(" (")[0].lower() for f, _ in sorted_factors[:2]]
    lines.append(
        f"Your score is driven primarily by **{top_two[0]}** and **{top_two[1]}**. "
        "Here is how each factor contributed:"
    )
    lines.append("")

    # Lot size
    if lot_acres >= 2.0:
        lines.append(f"- **Lot size ({lot_acres:.2f} ac):** Excellent — ample space for any loop configuration.")
    elif lot_acres >= 1.0:
        lines.append(f"- **Lot size ({lot_acres:.2f} ac):** Good — fits a horizontal or vertical loop system.")
    elif lot_acres >= HORIZONTAL_LOOP_MIN_ACRES:
        lines.append(f"- **Lot size ({lot_acres:.2f} ac):** Adequate — horizontal loop is feasible.")
    elif lot_acres >= VERTICAL_LOOP_MIN_ACRES:
        lines.append(f"- **Lot size ({lot_acres:.2f} ac):** Tight — vertical borehole is the likely option, adding 15–25% to cost.")
    else:
        lines.append(f"- **Lot size ({lot_acres:.2f} ac):** Very small — standard loop systems may not be feasible.")

    # Building size
    if prop_type == "Residential":
        if 1_500 <= sqft <= 5_000:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Ideal residential size — efficient system design.")
        elif sqft > 5_000:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Large home — higher system cost but strong savings potential.")
        elif sqft >= 800:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Smaller home — system will be modest in scale.")
        else:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Very small — limited economy of scale.")
    else:
        if sqft >= 10_000:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Strong commercial scale — ideal for a central GHP system.")
        elif sqft >= 5_000:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Good commercial size.")
        elif sqft >= 2_000:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Moderate commercial scale.")
        else:
            lines.append(f"- **Building size ({sqft:,.0f} sq ft):** Small — limited savings volume.")

    # Energy bill
    if prop_type == "Residential":
        if monthly_bill >= 400:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** High — strong savings potential and attractive payback.")
        elif monthly_bill >= 250:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Good — solid payback expected.")
        elif monthly_bill >= 150:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Moderate — payback period will be longer than average.")
        else:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Low — geothermal ROI may be limited; verify actual usage.")
    else:
        if monthly_bill >= 3_000:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** High commercial energy cost — excellent savings opportunity.")
        elif monthly_bill >= 1_500:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Good commercial energy spend.")
        elif monthly_bill >= 750:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Moderate commercial spend.")
        else:
            lines.append(f"- **Monthly bill (${monthly_bill:,.0f}):** Low for commercial — full energy audit recommended.")

    # Year built
    if year_built >= 2010:
        lines.append(f"- **Year built ({year_built}):** Modern construction — clean retrofit candidate.")
    elif year_built >= 2000:
        lines.append(f"- **Year built ({year_built}):** Recent construction — generally good insulation baseline.")
    elif year_built >= 1990:
        lines.append(f"- **Year built ({year_built}):** Some insulation upgrades may help system performance.")
    elif year_built >= 1980:
        lines.append(f"- **Year built ({year_built}):** Building envelope improvements are recommended before installation.")
    else:
        lines.append(f"- **Year built ({year_built}):** Older building — envelope upgrades likely needed to right-size the system.")

    # Property type
    if prop_type == "Commercial":
        lines.append("- **Property type (Commercial):** Consistent and predictable loads make geothermal an ideal fit.")
    else:
        lines.append("- **Property type (Residential):** Residential properties are strong geothermal candidates with well-understood load profiles.")

    # HVAC opportunity
    if "Electric Resistance" in hvac_type:
        lines.append(f"- **HVAC ({hvac_type}):** Replacing electric resistance heat with a GHP delivers the highest possible savings ratio — 3–5× more heat per kWh.")
    elif "Propane" in hvac_type:
        lines.append(f"- **HVAC ({hvac_type}):** Propane-to-geothermal transition eliminates fuel price volatility and typically cuts heating costs significantly.")
    elif "Gas" in hvac_type:
        lines.append(f"- **HVAC ({hvac_type}):** Geothermal can replace gas and reduce both operating cost and carbon footprint.")
    elif "Heat Pump" in hvac_type:
        lines.append(f"- **HVAC ({hvac_type}):** Upgrading from air-source to ground-source heat pump improves efficiency but with a smaller margin than fossil fuel replacements.")
    else:
        lines.append(f"- **HVAC ({hvac_type}):** Existing system should be evaluated for compatibility and replacement opportunity during the site visit.")

    return "\n".join(lines)


# ── Risk factors ───────────────────────────────────────────────────────────────

def generate_risk_factors(
    lot_acres: float,
    prop_type: str,
    year_built: int,
    hvac_type: str,
    monthly_bill: float,
) -> list[dict]:
    """
    Return a list of relevant risk factors dynamically generated from inputs.
    Each entry: { "level": "High"|"Medium"|"Low", "factor": str, "detail": str }
    """
    risks = []

    # Lot size
    if lot_acres < VERTICAL_LOOP_MIN_ACRES:
        risks.append({
            "level": "High",
            "factor": "Lot Size May Be Too Small for Standard Loop Systems",
            "detail": (
                f"At {lot_acres:.2f} acres, the lot is too small for a standard horizontal "
                "or vertical ground loop. A pond/lake loop or a shared district system "
                "would need to be explored as alternatives."
            ),
        })
    elif lot_acres < HORIZONTAL_LOOP_MIN_ACRES:
        risks.append({
            "level": "Medium",
            "factor": "Vertical Drilling Required — Higher Installation Cost",
            "detail": (
                f"At {lot_acres:.2f} acres, horizontal trenching is not feasible. A vertical "
                "borehole system is the likely option, which adds approximately 15–25% to "
                "installation cost compared to horizontal loops."
            ),
        })

    # Soil and rock — always unknown until investigated
    risks.append({
        "level": "Medium",
        "factor": "Soil and Rock Conditions Are Unknown",
        "detail": (
            "Subsurface conditions (soil type, rock depth, groundwater level) are not "
            "modeled in this screening tool. Hard rock, expansive clay, or high water "
            "tables can significantly affect drilling cost and system design. A site "
            "investigation or geotechnical report is needed."
        ),
    })

    # Older building envelope
    if year_built < 1990:
        risks.append({
            "level": "Medium",
            "factor": "Older Building Envelope May Reduce Efficiency Gains",
            "detail": (
                f"Built in {year_built}, this property may have inadequate insulation, "
                "air leakage, or older windows. Addressing the building envelope before "
                "installing geothermal is recommended — it avoids oversizing the system "
                "and shortens payback."
            ),
        })
    elif year_built < 2000:
        risks.append({
            "level": "Low",
            "factor": "Building Envelope Should Be Inspected",
            "detail": (
                f"Built in {year_built}, minor insulation or air-sealing improvements "
                "may improve system performance and reduce the required system size."
            ),
        })

    # HVAC compatibility
    if "Heat Pump" in hvac_type:
        risks.append({
            "level": "Low",
            "factor": "Existing Heat Pump Compatibility Check Needed",
            "detail": (
                "An existing air-source heat pump may share ductwork, but refrigerant "
                "type, distribution capacity, and control systems must be verified for "
                "geothermal compatibility."
            ),
        })
    elif "Boiler" in hvac_type:
        risks.append({
            "level": "Medium",
            "factor": "Boiler System May Need Modification",
            "detail": (
                "Geothermal heat pumps work best with low-temperature distribution systems "
                "(in-floor radiant, oversized radiators, or forced air). High-temperature "
                "radiator loops may require system modifications or a full replacement."
            ),
        })

    # Low energy bill — ROI risk
    if prop_type == "Residential" and monthly_bill < 150:
        risks.append({
            "level": "Medium",
            "factor": "Low Energy Bill May Limit Return on Investment",
            "detail": (
                f"At ${monthly_bill}/month, annual energy savings from geothermal may not "
                "generate an attractive payback period without significant incentives. "
                "Review 12 months of utility bills to confirm actual usage patterns."
            ),
        })
    if prop_type == "Commercial" and monthly_bill < 800:
        risks.append({
            "level": "Medium",
            "factor": "Energy Bill Should Be Verified",
            "detail": (
                f"A ${monthly_bill}/month commercial bill is lower than average for a "
                "geothermal project. Confirm that this reflects full energy usage including "
                "common area loads, tenant meters, and seasonal peaks."
            ),
        })

    # Permitting — always applies
    risks.append({
        "level": "Low",
        "factor": "Permitting and Local Zoning Review Required",
        "detail": (
            "Geothermal drilling requires permits in most jurisdictions. Local zoning may "
            "restrict bore depth, proximity to property lines, setbacks from wells, or "
            "equipment placement. Review local regulations early to avoid project delays."
        ),
    })

    # Incentives not yet applied
    risks.append({
        "level": "Low",
        "factor": "Incentives and Rebates Not Yet Included",
        "detail": (
            "This analysis does not include the 30% federal Investment Tax Credit (ITC), "
            "state rebates, utility incentive programs, or local grants. These can reduce "
            "the net cost by 30–50%. Research available programs for this location before "
            "preparing a final proposal."
        ),
    })

    # Commercial-specific
    if prop_type == "Commercial":
        risks.append({
            "level": "Low",
            "factor": "Commercial Usage Schedule Affects Savings Assumptions",
            "detail": (
                "Savings estimates are based on the monthly energy bill only. Actual "
                "commercial loads depend on occupancy hours, plug loads, tenant equipment, "
                "and seasonal demand patterns. A commercial energy audit is recommended "
                "before finalizing system sizing."
            ),
        })

    return risks


# ── Site checklist ─────────────────────────────────────────────────────────────

def build_site_checklist(
    prop_type: str, lot_acres: float, year_built: int
) -> list[str]:
    """
    Return a tailored site assessment checklist.
    """
    items = [
        "Confirm parcel boundaries and identify usable outdoor drilling or trenching area",
        "Collect 12 months of utility bills to establish an accurate energy baseline",
        "Inspect existing HVAC system — age, condition, fuel type, and duct layout",
        "Review building envelope: insulation, windows, and air sealing",
        "Identify potential loop field area and evaluate access for drilling equipment",
        "Review local permitting requirements for geothermal wells and ground loops",
        "Research available federal, state, utility, and local incentives and rebates",
        "Schedule a licensed geothermal contractor for a no-obligation site visit",
        "Request formal system sizing and proposals from at least two contractors",
        "Prepare formal feasibility assessment and customer proposal",
    ]
    if year_built < 1990:
        items.insert(3, "Commission a building energy audit to address envelope gaps before system sizing")
    if lot_acres < HORIZONTAL_LOOP_MIN_ACRES:
        items.insert(4, "Evaluate vertical borehole feasibility and local well-drilling regulations")
    if prop_type == "Commercial":
        items.append("Conduct a commercial energy audit to verify load profile and peak demand")
        items.append("Review tenant lease terms for HVAC upgrade rights and cost-sharing options")
    return items


# ── Recommendation summary ─────────────────────────────────────────────────────

def generate_recommendation_summary(
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
    """
    Return a structured plain-English recommendation (used in Executive Dashboard).
    """
    lines = []

    lines.append(
        f"This {prop_type.lower()} property scores **{score}/100** and is rated a "
        f"**{category}** for geothermal suitability."
    )

    if score >= 80:
        lines.append(
            "The property profile — lot size, energy spend, and building characteristics — "
            "strongly supports a geothermal heat pump system. We recommend scheduling a "
            "formal site visit as a near-term next step."
        )
    elif score >= 60:
        lines.append(
            "The property shows solid geothermal potential. With the right system design, "
            "the owner should expect reliable performance and meaningful long-term savings."
        )
    elif score >= 40:
        lines.append(
            "The property has moderate potential. Key site variables — soil conditions, lot "
            "layout, and local utility rates — should be verified before a formal proposal."
        )
    else:
        lines.append(
            "This property faces meaningful barriers to a cost-effective geothermal installation. "
            "A site engineer should evaluate whether alternatives such as mini-split upgrades "
            "or community loop systems are more appropriate."
        )

    lines.append(
        f"Given the {lot_acres:.2f}-acre lot, a **{loop_type}** configuration is the "
        "most likely system approach."
    )

    if year_built < 1985:
        lines.append(
            f"The building was constructed in {year_built}. Upgrading insulation and addressing "
            "air leakage before installation is strongly recommended — it reduces system size "
            "requirements and improves payback."
        )

    if "Electric Resistance" in hvac_type or "Propane" in hvac_type:
        lines.append(
            f"Replacing the current **{hvac_type}** system with geothermal represents one of "
            "the highest-savings fuel switches available — geothermal heat pumps deliver "
            "3–5× more heat per dollar than electric resistance or propane."
        )
    elif "Gas" in hvac_type:
        lines.append(
            "Transitioning from a gas system to geothermal eliminates fuel price volatility "
            "and reduces carbon emissions while typically lowering total operating costs."
        )

    lines.append(
        f"Projected annual savings range from **${savings_low:,.0f}** (conservative) "
        f"to **${savings_high:,.0f}** (optimistic). "
        f"Simple payback is estimated at **{payback_best}–{payback_worst} years** before "
        "incentives. The 30% federal IRA Investment Tax Credit can meaningfully shorten "
        "this window."
    )

    return "\n\n".join(lines)


# ── Sales proposal ─────────────────────────────────────────────────────────────

def generate_proposal_text(
    address: str,
    city: str,
    state: str,
    zip_code: str,
    prop_type: str,
    sqft: float,
    lot_acres: float,
    year_built: int,
    hvac_type: str,
    monthly_bill: float,
    score: int,
    category: str,
    install_low: float,
    install_high: float,
    savings_low: float,
    savings_high: float,
    payback_best: float,
    payback_worst: float,
    risk_factors: list[dict],
) -> str:
    """
    Generate a polished, consultant-style proposal from Xtreme Intelligence Inc.
    Professional and consultative — not salesy.
    """
    sep  = "=" * 62
    dash = "-" * 42

    # Summarize top two risk factors for the proposal
    top_risks = [r["factor"] for r in risk_factors if r["level"] in ("High", "Medium")][:3]
    risk_bullets = "\n".join(f"  - {r}" for r in top_risks) if top_risks else "  - No significant barriers identified at this stage."

    return f"""PRELIMINARY GEOTHERMAL SUITABILITY REPORT
Prepared by: Xtreme Intelligence Inc. | GeoIntel AI Solutions
{sep}

Based on the preliminary information provided, Xtreme Intelligence Inc.
has prepared an initial geothermal suitability review for:

  Property:  {address}, {city}, {state} {zip_code}
  Type:      {prop_type}
  Size:      {sqft:,.0f} sq ft  |  Lot: {lot_acres:.2f} acres
  Built:     {year_built}  |  HVAC: {hvac_type}
  Est. Monthly Energy Cost: ${monthly_bill:,.0f}

SUITABILITY ASSESSMENT
{dash}
GeoIntel AI has assigned this property a geothermal suitability score
of {score}/100, placing it in the {category} category.

{"This property is an outstanding candidate for geothermal. The combination of available outdoor space, energy profile, and building characteristics all align well with a high-performing system." if score >= 80 else "This property shows solid geothermal potential and warrants a formal site assessment to confirm feasibility and finalize system sizing." if score >= 60 else "This property has moderate geothermal potential. Key site variables should be confirmed during a professional site assessment." if score >= 40 else "This property faces some barriers to a standard geothermal installation. Alternative approaches may be worth evaluating alongside a standard feasibility study."}

PRELIMINARY FINANCIAL ESTIMATES
{dash}
The following estimates are based on simplified industry benchmarks
and have not been confirmed by a site assessment or engineering review.

  Installation Cost (estimate):
    Conservative:    ${install_low:>10,.0f}
    High-end:        ${install_high:>10,.0f}

  Estimated Annual Savings:
    Conservative:    ${savings_low:>10,.0f} per year
    Optimistic:      ${savings_high:>10,.0f} per year

  Estimated Simple Payback Period:
    Best case:       {payback_best} years
    Worst case:      {payback_worst} years

Note: The 30% federal Investment Tax Credit (ITC) under the Inflation
Reduction Act may apply and can significantly reduce the net cost.
State and utility incentives may reduce it further.

KEY CONSIDERATIONS
{dash}
{risk_bullets}

RECOMMENDED NEXT STEP
{dash}
The recommended next step is to complete a site-level feasibility
review with parcel, utility, HVAC, permitting, and incentive
information. This will allow Xtreme Intelligence Inc. to prepare a
formal proposal with confirmed costs, savings, and financing options.

Please contact us to schedule a no-obligation site visit.

{dash}
Prepared by: Xtreme Intelligence Inc. | GeoIntel AI Solutions
All estimates are preliminary and illustrative. This report does not
constitute an engineering assessment or a formal proposal."""


# ── Main application ───────────────────────────────────────────────────────────

def main():

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("## 🌍 GeoIntel AI")
        st.markdown("**AI-Assisted Property Geothermal Suitability Analyzer**")
        st.markdown(f"Version {APP_VERSION} &nbsp;|&nbsp; Demo Prototype")
        st.divider()

        st.markdown(
            "This prototype uses manual inputs and simplified assumptions. "
            "Future versions may connect to parcel, zoning, utility, incentive, "
            "and energy datasets."
        )
        st.divider()

        st.markdown("#### Load a Sample Property")
        samples = load_samples()
        sample_names = ["— select a sample —"] + [s["name"] for s in samples]
        chosen = st.selectbox("Sample Properties", sample_names, label_visibility="collapsed")
        selected = None
        if chosen != "— select a sample —":
            selected = next(s for s in samples if s["name"] == chosen)
            st.caption(f"Loaded: **{chosen}**")

        st.divider()
        st.caption(
            "**Disclaimer:** All figures are illustrative estimates based on "
            "industry averages. A licensed geothermal contractor must perform a "
            "formal site assessment before any installation decision."
        )
        st.caption(f"© {CURRENT_YEAR} Xtreme Intelligence Inc.")

    # ── Helper: pull value from selected sample or use a fallback ─────────────
    def sv(key, fallback):
        if selected and key in selected:
            return selected[key]
        return fallback

    # ── Page header ────────────────────────────────────────────────────────────
    st.markdown("# 🌍 GeoIntel AI")
    st.markdown("### AI-Assisted Property Geothermal Suitability Analyzer")
    st.markdown(f"**Version {APP_VERSION} — Demo Prototype** &nbsp;|&nbsp; Developed by Xtreme Intelligence Inc.")
    st.markdown(
        "> GeoIntel AI helps evaluate whether a residential or commercial property may be a good "
        "candidate for geothermal heating and cooling by estimating suitability, installation cost, "
        "savings potential, payback period, and next-step recommendations."
    )
    st.divider()

    # ── Tabs ───────────────────────────────────────────────────────────────────
    (
        tab_inputs,
        tab_dashboard,
        tab_financial,
        tab_risks,
        tab_checklist,
        tab_proposal,
        tab_methodology,
    ) = st.tabs([
        "📋 Property Inputs",
        "📊 Executive Dashboard",
        "💰 Financial Analysis",
        "⚠️  Risk Factors",
        "✅ Site Assessment Checklist",
        "📄 Sales Proposal Draft",
        "📖 Methodology",
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — Property Inputs
    # ══════════════════════════════════════════════════════════════════════════
    with tab_inputs:
        st.subheader("Enter Property Information")
        st.markdown(
            "Fill in the fields below and click **Analyze Property** to generate a full "
            "suitability report. You can also load a sample property from the sidebar."
        )

        with st.form("property_form"):

            # ── Property Details ───────────────────────────────────────────────
            st.markdown("#### Property Details")
            c1, c2 = st.columns(2)
            with c1:
                prop_type = st.selectbox(
                    "Property Type",
                    ["Residential", "Commercial"],
                    index=0 if sv("property_type", "Residential") == "Residential" else 1,
                )
            with c2:
                address = st.text_input(
                    "Street Address",
                    value=sv("address", ""),
                    placeholder="e.g. 6000 Example Road",
                )

            c3, c4, c5 = st.columns(3)
            with c3:
                city = st.text_input("City", value=sv("city", ""), placeholder="e.g. Clarksville")
            with c4:
                state = st.text_input("State", value=sv("state", ""), max_chars=2, placeholder="MD")
            with c5:
                zip_code = st.text_input("ZIP Code", value=str(sv("zip", "")), placeholder="21029")

            # ── Building Details ───────────────────────────────────────────────
            st.markdown("#### Building Details")
            c6, c7, c8 = st.columns(3)
            with c6:
                sqft = st.number_input(
                    "Building Size (sq ft)",
                    min_value=0, max_value=500_000,
                    value=int(sv("sqft", 2_500)), step=100,
                    help="Total conditioned square footage of the building.",
                )
            with c7:
                lot_acres = st.number_input(
                    "Lot Size (acres)",
                    min_value=0.00, max_value=500.0,
                    value=float(sv("lot_acres", 0.5)), step=0.05, format="%.2f",
                    help="Total parcel size. Larger lots allow more loop field options.",
                )
            with c8:
                year_built = st.number_input(
                    "Year Built",
                    min_value=1800, max_value=2030,
                    value=int(sv("year_built", 2000)), step=1,
                    help="Original construction year. Older buildings may need envelope upgrades first.",
                )

            hvac_options = [
                "Gas Furnace + Central AC",
                "Heat Pump (Air Source)",
                "Electric Resistance + Central AC",
                "Propane Furnace + Central AC",
                "Rooftop HVAC Units (RTUs)",
                "Boiler (Hot Water / Steam)",
                "Chiller System",
                "Mini-Split (Ductless)",
                "Other / Unknown",
            ]
            default_hvac = sv("hvac_type", "Gas Furnace + Central AC")
            hvac_idx     = hvac_options.index(default_hvac) if default_hvac in hvac_options else 0
            hvac_type = st.selectbox(
                "Current HVAC System Type",
                hvac_options,
                index=hvac_idx,
                help="The existing heating and cooling system. Affects savings estimates and risk flags.",
            )

            # ── Energy & Occupancy ─────────────────────────────────────────────
            st.markdown("#### Energy & Occupancy")
            c9, c10 = st.columns(2)
            with c9:
                monthly_bill = st.number_input(
                    "Estimated Monthly Energy Bill ($)",
                    min_value=0, max_value=200_000,
                    value=int(sv("monthly_energy_bill", 250)), step=10,
                    help="Average combined gas + electric bill. Used to estimate annual savings.",
                )
            if prop_type == "Residential":
                with c10:
                    occupants = st.number_input(
                        "Number of Occupants",
                        min_value=1, max_value=100,
                        value=int(sv("occupants", 3)), step=1,
                    )
                business_type = None
            else:
                with c10:
                    biz_options = [
                        "Office", "Medical Office", "Retail", "Restaurant",
                        "Warehouse / Industrial", "Healthcare / Hospital",
                        "Education / School", "Hospitality / Hotel",
                        "Nonprofit / Church", "Other",
                    ]
                    default_biz = sv("business_type", "Office")
                    biz_idx     = biz_options.index(default_biz) if default_biz in biz_options else 0
                    business_type = st.selectbox("Business / Facility Type", biz_options, index=biz_idx)
                occupants = None

            # Optional notes
            st.markdown("#### Notes (Optional)")
            notes = st.text_area(
                "Additional context about the property",
                value=sv("notes", ""),
                placeholder=(
                    "e.g. Property is under consideration for sale. Owner wants a cost estimate "
                    "before listing. Existing HVAC is 18 years old and due for replacement."
                ),
                height=80,
            )

            submitted = st.form_submit_button(
                "🔍  Analyze Property", use_container_width=True, type="primary"
            )

        # ── Validation and computation (after submit) ──────────────────────────
        if submitted:
            errors   = []
            warnings = []

            if sqft <= 0:
                errors.append("Building square footage must be greater than 0.")
            if lot_acres <= 0:
                errors.append("Lot size must be greater than 0 acres.")
            if monthly_bill <= 0:
                errors.append("Monthly energy bill must be greater than $0.")
            if year_built > CURRENT_YEAR:
                errors.append(f"Year built ({year_built}) cannot be in the future.")
            if not address.strip() or not city.strip() or not state.strip():
                errors.append("Please enter at least a street address, city, and state.")

            # Soft warnings — don't block, just alert
            if 0 < lot_acres < 0.05:
                warnings.append(
                    f"Lot size ({lot_acres:.3f} acres) is very small. "
                    "Standard geothermal drilling may not be feasible."
                )
            if prop_type == "Residential" and 0 < monthly_bill < 100:
                warnings.append(
                    f"Monthly energy bill (${monthly_bill}) is very low for a residential property. "
                    "Geothermal ROI may be limited — verify full energy usage."
                )
            if prop_type == "Commercial" and 0 < monthly_bill < 400:
                warnings.append(
                    f"Monthly commercial energy bill (${monthly_bill}) is unusually low. "
                    "Confirm this reflects the full building energy cost."
                )

            for msg in errors:
                st.error(f"**Input Error:** {msg}")
            for msg in warnings:
                st.warning(f"**Note:** {msg}")

            if errors:
                st.stop()

            # ── Run all calculations ───────────────────────────────────────────
            score, breakdown = calculate_suitability_score(
                lot_acres, sqft, prop_type, monthly_bill, year_built, hvac_type
            )
            category, icon, cat_desc = get_candidate_category(score)
            loop_type = build_loop_type(lot_acres)
            fin = calculate_financials(sqft, prop_type, monthly_bill)

            score_explanation = build_score_explanation(
                lot_acres, sqft, prop_type, monthly_bill, year_built, hvac_type, breakdown
            )
            risk_factors = generate_risk_factors(
                lot_acres, prop_type, year_built, hvac_type, monthly_bill
            )
            checklist = build_site_checklist(prop_type, lot_acres, year_built)

            recommendation = generate_recommendation_summary(
                prop_type, score, category, lot_acres, sqft, year_built,
                monthly_bill, fin["savings_low"], fin["savings_high"],
                fin["payback_best"], fin["payback_worst"], loop_type, hvac_type,
            )
            proposal = generate_proposal_text(
                address, city, state, zip_code, prop_type, sqft, lot_acres,
                year_built, hvac_type, monthly_bill, score, category,
                fin["install_low"], fin["install_high"],
                fin["savings_low"], fin["savings_high"],
                fin["payback_best"], fin["payback_worst"],
                risk_factors,
            )

            # Store everything so all other tabs can read it
            st.session_state["r"] = {
                "address": address, "city": city, "state": state, "zip_code": zip_code,
                "prop_type": prop_type, "sqft": sqft, "lot_acres": lot_acres,
                "year_built": year_built, "hvac_type": hvac_type, "notes": notes,
                "monthly_bill": monthly_bill, "occupants": occupants,
                "business_type": business_type,
                "score": score, "breakdown": breakdown,
                "category": category, "icon": icon, "cat_desc": cat_desc,
                "loop_type": loop_type,
                "score_explanation": score_explanation,
                "fin": fin,
                "risk_factors": risk_factors,
                "checklist": checklist,
                "recommendation": recommendation,
                "proposal": proposal,
            }

            st.success(
                "Analysis complete! Click the tabs above to explore your results — "
                "start with the **Executive Dashboard**."
            )

    # ── Gate-check helper ──────────────────────────────────────────────────────
    def ready() -> bool:
        return "r" in st.session_state

    def prompt_submit():
        st.info(
            "Complete the **Property Inputs** tab and click **Analyze Property** "
            "to generate results."
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — Executive Dashboard
    # ══════════════════════════════════════════════════════════════════════════
    with tab_dashboard:
        if not ready():
            prompt_submit()
        else:
            r  = st.session_state["r"]
            f  = r["fin"]
            st.subheader(
                f"Executive Dashboard — {r['address']}, {r['city']}, {r['state']} {r['zip_code']}"
            )

            # Category banner
            st.markdown("---")
            col_icon, col_text = st.columns([1, 4])
            with col_icon:
                st.markdown(f"<h1 style='font-size:4rem;text-align:center'>{r['icon']}</h1>",
                            unsafe_allow_html=True)
            with col_text:
                st.markdown(f"### {r['category']}")
                st.markdown(r["cat_desc"])
                st.caption(f"Recommended loop configuration: {r['loop_type']}")

            # Key metric cards
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m4, m5, m6 = st.columns(3)

            m1.metric(
                "Suitability Score",
                f"{r['score']} / 100",
                help="0 = very poor fit, 100 = ideal candidate.",
            )
            m2.metric(
                "Candidate Category",
                r["category"],
            )
            m3.metric(
                "Est. Annual Energy Cost",
                f"${f['annual_cost']:,.0f}",
                help="Current estimated annual energy cost (monthly bill × 12).",
            )
            m4.metric(
                "Est. Installation Cost",
                f"${f['install_low']:,.0f} – ${f['install_high']:,.0f}",
                help="Low-to-high range before incentives. See Financial Analysis for detail.",
            )
            m5.metric(
                "Est. Annual Savings",
                f"${f['savings_low']:,.0f} – ${f['savings_high']:,.0f}",
                help="Conservative to optimistic range. Does not include incentive impact.",
            )
            m6.metric(
                "Est. Payback Period",
                f"{f['payback_best']} – {f['payback_worst']} yrs",
                help="Simple payback before the 30% IRA tax credit. Credit shortens this.",
            )

            # Recommendation text
            st.markdown("---")
            st.markdown("### Recommendation Summary")
            st.markdown(r["recommendation"])

            # Score breakdown
            st.markdown("---")
            st.markdown("### Suitability Score Breakdown")
            bd_df = pd.DataFrame({
                "Factor": list(r["breakdown"].keys()),
                "Points Earned": list(r["breakdown"].values()),
            }).set_index("Factor")
            st.bar_chart(bd_df)

            st.markdown("### Why This Score?")
            st.markdown(r["score_explanation"])

            # Raw inputs summary
            with st.expander("View All Input Values"):
                inp = {
                    "Property Type": r["prop_type"],
                    "Address": f"{r['address']}, {r['city']}, {r['state']} {r['zip_code']}",
                    "Building Size": f"{r['sqft']:,} sq ft",
                    "Lot Size": f"{r['lot_acres']:.2f} acres",
                    "Year Built": r["year_built"],
                    "HVAC Type": r["hvac_type"],
                    "Monthly Energy Bill": f"${r['monthly_bill']:,}",
                }
                if r["prop_type"] == "Residential":
                    inp["Occupants"] = r["occupants"]
                else:
                    inp["Business Type"] = r["business_type"]
                if r["notes"]:
                    inp["Notes"] = r["notes"]
                st.dataframe(
                    pd.DataFrame(list(inp.items()), columns=["Field", "Value"]),
                    width="stretch", hide_index=True,
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — Financial Analysis
    # ══════════════════════════════════════════════════════════════════════════
    with tab_financial:
        if not ready():
            prompt_submit()
        else:
            r = st.session_state["r"]
            f = r["fin"]
            st.subheader("Financial Analysis")
            st.markdown(
                f"**{r['address']}, {r['city']}, {r['state']}** — "
                f"{r['prop_type']}, {r['sqft']:,.0f} sq ft"
            )

            # Scenarios table
            st.markdown("---")
            st.markdown("### Installation Cost & Payback Scenarios")
            scenarios = pd.DataFrame({
                "Scenario": ["Conservative (Low)", "Mid Estimate", "High End"],
                "Installation Cost ($)": [f["install_low"],   f["install_mid"],   f["install_high"]],
                "Annual Savings ($)":    [f["savings_low"],   f["savings_mid"],   f["savings_high"]],
                "Payback Period (yrs)":  [f["payback_worst"], f["payback_mid"],   f["payback_best"]],
            })
            st.dataframe(scenarios, width="stretch", hide_index=True)

            # Chart 1 — current vs geothermal energy cost
            st.markdown("---")
            st.markdown("### Annual Energy Cost — Before vs. After Geothermal (Mid Estimate)")
            cost_df = pd.DataFrame({
                "Scenario": ["Current Annual Cost", "With Geothermal (Mid Est.)"],
                "Annual Energy Cost ($)": [f["annual_cost"], f["geo_cost_mid"]],
            }).set_index("Scenario")
            st.bar_chart(cost_df)
            st.caption(
                f"Current: ${f['annual_cost']:,.0f}/yr  →  "
                f"Geothermal estimate: ${f['geo_cost_mid']:,.0f}/yr  "
                f"(mid savings: ${f['savings_mid']:,.0f}/yr)"
            )

            # Chart 2 — installation cost scenarios
            st.markdown("---")
            st.markdown("### Installation Cost by Scenario")
            install_df = pd.DataFrame({
                "Scenario": ["Low", "Mid", "High"],
                "Installation Cost ($)": [f["install_low"], f["install_mid"], f["install_high"]],
            }).set_index("Scenario")
            st.bar_chart(install_df)

            # Chart 3 — 20-year cumulative savings
            st.markdown("---")
            st.markdown("### 20-Year Net Savings Timeline (Mid Estimate)")
            years      = list(range(0, 21))
            cumulative = [round(f["savings_mid"] * y - f["install_mid"]) for y in years]
            timeline_df = pd.DataFrame({
                "Year": years,
                "Net Cumulative Savings ($)": cumulative,
            }).set_index("Year")
            st.line_chart(timeline_df)
            st.caption(
                f"Midpoint install: ${f['install_mid']:,.0f}  |  "
                f"Midpoint annual savings: ${f['savings_mid']:,.0f}/yr  |  "
                f"Line crosses $0 at the break-even point (~{f['payback_mid']} yrs)."
            )

            # Assumptions
            st.markdown("---")
            st.markdown("### Calculation Assumptions")
            if r["prop_type"] == "Residential":
                st.markdown(
                    f"- **Installation cost:** ${RES_COST_LOW}–${RES_COST_HIGH}/sq ft "
                    f"(minimum ${RES_INSTALL_MIN:,})\n"
                    f"- **Annual savings:** {int(RES_SAVINGS_LOW*100)}–{int(RES_SAVINGS_HIGH*100)}% "
                    "of annual energy cost\n"
                    "- **Federal ITC (30%):** Not applied above — reduces net cost significantly\n"
                    "- State/utility rebates: Not included"
                )
            else:
                st.markdown(
                    f"- **Installation cost:** ${COM_COST_LOW}–${COM_COST_HIGH}/sq ft "
                    f"(minimum ${COM_INSTALL_MIN:,})\n"
                    f"- **Annual savings:** {int(COM_SAVINGS_LOW*100)}–{int(COM_SAVINGS_HIGH*100)}% "
                    "of annual energy cost\n"
                    "- **Federal ITC (30%):** Not applied above — reduces net cost significantly\n"
                    "- State/utility rebates: Not included"
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — Risk Factors
    # ══════════════════════════════════════════════════════════════════════════
    with tab_risks:
        if not ready():
            prompt_submit()
        else:
            r = st.session_state["r"]
            st.subheader("Risk Factors")
            st.markdown(
                "The following risk factors were identified based on the property inputs. "
                "These are not disqualifying — they are areas to investigate and address "
                "during a formal site assessment."
            )
            st.markdown("---")

            icons = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}
            for risk in r["risk_factors"]:
                lvl = risk["level"]
                with st.expander(f"{icons[lvl]}  **{lvl} Risk** — {risk['factor']}"):
                    st.markdown(risk["detail"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — Site Assessment Checklist
    # ══════════════════════════════════════════════════════════════════════════
    with tab_checklist:
        if not ready():
            prompt_submit()
        else:
            r = st.session_state["r"]
            st.subheader("Site Assessment Checklist")
            st.markdown(
                "Use this checklist to prepare for a formal geothermal site assessment. "
                "Share it with the property owner, contractor, or facilities team."
            )
            st.markdown("---")
            for i, item in enumerate(r["checklist"]):
                st.checkbox(item, value=False, key=f"chk_{i}")

            st.markdown("---")
            st.info(
                "**Finding a certified contractor:** Contact your state's geothermal association "
                "or visit the International Ground Source Heat Pump Association (IGSHPA) at "
                "igshpa.org to find certified installers near you. Always request at least two "
                "independent proposals."
            )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — Sales Proposal Draft
    # ══════════════════════════════════════════════════════════════════════════
    with tab_proposal:
        if not ready():
            prompt_submit()
        else:
            r = st.session_state["r"]
            st.subheader("Sales Proposal Draft")
            st.markdown(
                "This auto-generated proposal is ready to download and share. "
                "Review and customize it before sending to the property owner."
            )
            st.markdown("---")

            # Editable preview
            proposal_text = st.text_area(
                "Proposal (editable — customize before sending)",
                value=r["proposal"],
                height=560,
                key="proposal_area",
            )

            col_dl, col_info = st.columns([1, 3])
            with col_dl:
                st.download_button(
                    label="⬇️  Download as .txt",
                    data=proposal_text,
                    file_name=f"GeoIntel_Proposal_{r['zip_code'] or 'property'}.txt",
                    mime="text/plain",
                )
            with col_info:
                st.caption(
                    "The downloaded file uses the text shown above (including any edits you made). "
                    "Future versions will support PDF export."
                )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 7 — Methodology
    # ══════════════════════════════════════════════════════════════════════════
    with tab_methodology:
        st.subheader("Methodology & Assumptions")
        st.markdown(
            "GeoIntel AI Version 0.2 is an **early-stage screening tool**, not a "
            "replacement for a professional site assessment."
        )

        st.markdown("---")
        st.markdown("### What This Tool Does")
        st.markdown(
            "- Collects basic property information through a manual input form\n"
            "- Applies a weighted scoring model to estimate geothermal suitability\n"
            "- Produces rough financial estimates for installation cost, annual savings, "
            "and payback period\n"
            "- Generates a dynamic list of risk factors based on inputs\n"
            "- Produces a draft sales proposal for follow-up with the property owner"
        )

        st.markdown("---")
        st.markdown("### What This Tool Does Not Do")
        st.markdown(
            "- It does **not** replace a licensed geothermal contractor site visit\n"
            "- It does **not** access real parcel, zoning, or permit data\n"
            "- It does **not** pull actual utility rate data or incentive program databases\n"
            "- It does **not** model soil or groundwater conditions\n"
            "- It does **not** size a system — that requires a Manual J load calculation\n"
            "- It does **not** account for financing, tax strategies, or NPV analysis"
        )

        st.markdown("---")
        st.markdown("### Suitability Score Model")
        score_table = pd.DataFrame({
            "Factor": [
                "Lot Size",
                "Building Size",
                "Energy Bill",
                "Year Built",
                "Property Type",
                "HVAC Replacement Opportunity",
            ],
            "Max Points": [30, 20, 20, 10, 10, 10],
            "Rationale": [
                "Larger lots allow lower-cost horizontal loops",
                "Larger buildings can support bigger systems with more savings",
                "Higher energy bills mean more savings potential and better ROI",
                "Newer buildings have better envelopes and simpler retrofits",
                "Commercial loads are more consistent and predictable",
                "Less-efficient systems (electric resistance, propane) show largest gains",
            ],
        })
        st.dataframe(score_table, width="stretch", hide_index=True)

        st.markdown("---")
        st.markdown("### Financial Assumption Summary")
        fin_table = pd.DataFrame({
            "Parameter": [
                "Residential install cost",
                "Commercial install cost",
                "Residential savings",
                "Commercial savings",
                "Federal Investment Tax Credit",
            ],
            "Assumption": [
                f"${RES_COST_LOW}–${RES_COST_HIGH} per sq ft (min ${RES_INSTALL_MIN:,})",
                f"${COM_COST_LOW}–${COM_COST_HIGH} per sq ft (min ${COM_INSTALL_MIN:,})",
                f"{int(RES_SAVINGS_LOW*100)}–{int(RES_SAVINGS_HIGH*100)}% of annual energy cost",
                f"{int(COM_SAVINGS_LOW*100)}–{int(COM_SAVINGS_HIGH*100)}% of annual energy cost",
                "30% of installation cost (Inflation Reduction Act) — not applied automatically",
            ],
            "Source": [
                "Industry benchmark range (IGSHPA, ACCA, contractor surveys)",
                "Industry benchmark range (IGSHPA, ACCA, contractor surveys)",
                "Geothermal heat pump efficiency studies",
                "Commercial GHP performance studies",
                "IRS guidance, IRA Section 25D / 48",
            ],
        })
        st.dataframe(fin_table, width="stretch", hide_index=True)

        st.markdown("---")
        st.markdown("### Version Roadmap")
        roadmap = pd.DataFrame({
            "Version": ["v0.3", "v0.4", "v0.5", "v1.0"],
            "Planned Feature": [
                "PDF proposal export",
                "Maryland incentive estimator (static lookup table)",
                "Property / parcel data lookup (public data sources)",
                "SaaS-style lead generation and formal proposal platform",
            ],
        })
        st.dataframe(roadmap, width="stretch", hide_index=True)

        st.markdown("---")
        st.caption(
            f"GeoIntel AI v{APP_VERSION} — © {CURRENT_YEAR} Xtreme Intelligence Inc. "
            "All estimates are illustrative. A licensed geothermal contractor must "
            "perform a formal site assessment before any installation decision."
        )

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.caption(
        f"🌍 GeoIntel AI &nbsp;|&nbsp; Version {APP_VERSION} — Demo Prototype &nbsp;|&nbsp; "
        f"© {CURRENT_YEAR} Xtreme Intelligence Inc. &nbsp;|&nbsp; "
        "All figures are illustrative estimates. A licensed geothermal contractor must "
        "perform a formal site assessment before any installation decision."
    )


if __name__ == "__main__":
    main()
