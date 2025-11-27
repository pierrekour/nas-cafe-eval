from pathlib import Path
from hebrew_config import LABELS, DEFAULTS
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Page Config
st.set_page_config(page_title=LABELS.get("page_title", "Cafe NAS Valuation"), layout="wide")

# RTL CSS
st.markdown("""
<style>
    .stApp {
        direction: rtl;
        text-align: right;
    }
    .stMarkdown, .stText, .stHeader, .stSubheader, .stInfo, .stSuccess, .stError, .stMetricLabel {
        text-align: right !important;
    }
    /* Adjust metric value alignment if needed, though usually LTR for numbers is fine */
    div[data-testid="stMetricValue"] {
        direction: rtl; 
        text-align: right !important;;
    }
    /* Reduce spacing */
    div.block-container {
        padding-top: 3rem;
        padding-bottom: 1rem;
    }
    div[data-testid="stVerticalBlock"] > div {
        gap: 0.1rem;
    }
    /* Reduce spacing between label and input in columns */
    div[data-testid="column"] {
        padding: 0;
    }

    /* Compact Metrics */
    div[data-testid="stMetricLabel"] {
        font-size: rem !important;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
col_head1, col_head2 = st.columns([0.5, 5])
with col_head1:
    st.image(Path(__file__).parent / "nas_logo.png", width=60)
with col_head2:
    st.markdown(LABELS["header_title"], unsafe_allow_html=True)

# --- Sidebar: Inputs ---
# revenue_scenario = st.sidebar.selectbox(LABELS["scenario_select"], LABELS["scenarios"], index=1)
revenue_scenario ="realistic"
asking_price = st.sidebar.number_input(LABELS["asking_price"], value=DEFAULTS["asking_price"], step=5000)
assets_value = st.sidebar.number_input(LABELS["equipment_value"], value=int(DEFAULTS["assets_value"] * (1 - DEFAULTS["impairment_mult"])), step=2000)
stock_value = st.sidebar.number_input(LABELS['stock'], value=DEFAULTS["stock_value"], step=1000)


# Sidebar inputs for arnona
arnona_area_key = f"{revenue_scenario}_arnona_area"
arnona_price_per_sqm = DEFAULTS["arnona_price_per_sqm"]
if arnona_area_key not in st.session_state:
    st.session_state[arnona_area_key] = DEFAULTS["arnona_area"]
area = st.sidebar.number_input(LABELS['arnona_area'], value=st.session_state[arnona_area_key], min_value=1, step=1)
st.sidebar.markdown(f"{LABELS['arnona_price_per_sqm']}: <b>{arnona_price_per_sqm}₪</b>", unsafe_allow_html=True)
arnona_val = area * arnona_price_per_sqm
st.session_state[f"{revenue_scenario}_arnona"] = arnona_val
vat_rate = 17.0 / 100.0
# poi_active = st.sidebar.checkbox("לכלול עבודה אישית?", value=False)
# poi_cost = st.sidebar.number_input("עלות עבודה אישית (POI שנתי)", value=16800, step=1000)
# tax_rate = st.sidebar.number_input("מס שולי (לחישוב נטו)", value=47.0, step=1.0) / 100.0
tax_rate = 47.0 / 100.0
# --- Main Dashboard ---

# Placeholder for metrics
metrics_container = st.container()

# Layout: P&L (Left) | Valuation Analysis (Right)
col_right, col_left = st.columns([1, 1])

with col_right: # Visually Right in RTL
    st.subheader(LABELS["PL_statement"])

    # Helper to display a row
    def pl_row(key, step=1000, is_header=False, is_total=False, indent=False, checkbox=False, default_val=None):
        label = LABELS.get(key, key)
        # Initialize session state if needed
        full_key = f"{revenue_scenario}_{key}"
        if full_key not in st.session_state:
            st.session_state[full_key] = default_val
            
        # Checkbox state
        cb_key = f"{full_key}_active"
        if checkbox and cb_key not in st.session_state:
            st.session_state[cb_key] = False

        pl_col1, pl_col2, pl_col3 = st.columns([2, 1, 1]) # Avoid shadowing outer col1, col2, col3
        with pl_col1:
            if is_header:
                st.markdown(f"**{label}**")
            elif is_total:
                st.markdown(f"**{label}**")
            else:
                prefix = "&nbsp;&nbsp;&nbsp;&nbsp;" if indent else ""
                if checkbox:
                    st.checkbox(f"{prefix}{label}", key=cb_key)
                else:
                    st.markdown(f"{prefix}{label}", unsafe_allow_html=True)
        with pl_col2:
            if is_header:
                pass
            elif is_total:
                pl_val = st.session_state.get(full_key, default_val) # It might be calculated outside
                st.markdown(f"**₪{pl_val:,.0f}**")
            else:
                # Input - Show Positive
                current_val = st.session_state.get(full_key, default_val)
                st.number_input(label, value=current_val, key=full_key, step=step, label_visibility="collapsed")
        with pl_col3:
            if not is_header:
                # Calculate %
                pl_val = st.session_state.get(full_key, default_val)
                if checkbox and not st.session_state[cb_key]:
                    pl_val = 0
                rev = st.session_state.get(f"{revenue_scenario}_revenue", DEFAULTS["revenue"])
                pct = (pl_val / rev * 100) if rev != 0 else 0
                fmt = f"**{pct:.1f}%**" if is_total else f"{pct:.1f}%"
                st.markdown(fmt)
        # Return value for calculation
        final_val = st.session_state.get(full_key, default_val)
        if checkbox and not st.session_state[cb_key]:
            final_val = 0
        return final_val

    # 1. Revenue
    # We need specific handling for Revenue to trigger updates if needed, but standard is fine.
    rev_key = f"{revenue_scenario}_revenue"
    if rev_key not in st.session_state:
        st.session_state[rev_key] = DEFAULTS.get("revenue", 0)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"##### {LABELS['revenue']}")
    with col2:
        revenue = st.number_input(LABELS["revenue"], key=rev_key, step=10000, label_visibility="collapsed")
    with col3:
        st.markdown("100.0%")

    # 2. Food Cost (Synced)
    cogs_amt_key = f"{revenue_scenario}_cogs_amount"
    cogs_pct_key = f"{revenue_scenario}_cogs_pct"
    
    # Callbacks
    def update_cogs_amount():
        pct = st.session_state[cogs_pct_key]
        rev = st.session_state[rev_key]
        st.session_state[cogs_amt_key] = rev * (pct / 100.0) # Positive

    def update_cogs_pct():
        amt = st.session_state[cogs_amt_key]
        rev = st.session_state[rev_key]
        if rev != 0:
            st.session_state[cogs_pct_key] = (amt / rev) * 100.0 # Positive

    # Init (Positive values now)
    if cogs_amt_key not in st.session_state:
        st.session_state[cogs_amt_key] = DEFAULTS["revenue"] * (DEFAULTS["food_cost_pct"] / 100.0)
    if cogs_pct_key not in st.session_state:
        st.session_state[cogs_pct_key] = DEFAULTS["food_cost_pct"]

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{LABELS['food_cost']}**")
    with col2:
        cogs = st.number_input(LABELS["food_cost"], key=cogs_amt_key, step=1000, on_change=update_cogs_pct, label_visibility="collapsed")
    with col3:
        cogs_pct = st.number_input("%", key=cogs_pct_key, step=0.2, on_change=update_cogs_amount, label_visibility="collapsed", format="%.1f")

    # 3. Gross Profit
    gross_profit = revenue - cogs # Subtract positive expense
    gp_pct = (gross_profit / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{LABELS['gross_profit']}**")
    with col2:
        st.markdown(f"**₪{gross_profit:,.0f}**")
    with col3: 
        st.markdown(f"**{gp_pct:.1f}%**")
        
    # 4. Salaries
    # Positive defaults
    with st.expander(LABELS["salaries_total"], expanded=False):
        sal_manager = pl_row("sal_manager", indent=True, default_val=DEFAULTS["sal_manager"])
        sal_rami = pl_row("sal_rami", indent=True, default_val=DEFAULTS["sal_rami"])
        sal_staff = pl_row("sal_staff", indent=True, default_val=DEFAULTS["sal_staff"])
    
    salaries = sal_manager + sal_rami + sal_staff
    sal_pct = (salaries / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{LABELS['salaries_total']}**")
    with col2:
        st.markdown(f"**₪{salaries:,.0f}**")
    with col3:
        st.markdown(f"**{sal_pct:.1f}%**")

    # 5. OpEx
    # Define OpEx items (Positive defaults)
    opex_keys = ["rent", "arnona", "utils", "comm", "marketing", "maint", "legal", "fees", "misc"]
    opex_sum = 0
    opex_vat_sum = 0
    rent = 0 # Need to extract rent specifically for waterfall
    with st.expander(LABELS["opex"], expanded=False):
        for key in opex_keys:
            use_checkbox = (key == "utils")
            def_val = DEFAULTS.get(key, 0)
            if key == "arnona":
                def_val = arnona_val
                is_tot = True
            else:
                is_tot = False
            val = pl_row(key, indent=True, checkbox=use_checkbox, default_val=def_val, is_total=is_tot)
            opex_sum += val
            if key == "arnona" or key == "fees":
                continue
            if key == "rent":
                rent = val
            opex_vat_sum += val

    opex_pct = (opex_sum / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{LABELS['opex']}**")
    with col2:
        st.markdown(f"**₪{opex_sum:,.0f}**")
    with col3:
        st.markdown(f"**{opex_pct:.1f}%**")
    
    # Total Expenses
    total_expenses = salaries + opex_sum
        
    # EBITDA
    ebitda = gross_profit - total_expenses # Subtract positive expenses
    ebitda_pct = (ebitda / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(LABELS["ebitda"])
    with col2:
        st.markdown(f"₪{ebitda:,.0f}")
    with col3:
        st.markdown(f"{ebitda_pct:.1f}%")
    
    # Depreciation
    depreciation = pl_row("depreciation", default_val=DEFAULTS["depreciation"]) # Positive
    
    # Net Profit Pre-Tax
    net_profit_pretax = ebitda - depreciation # Subtract
    nppt_pct = (net_profit_pretax / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**{LABELS['net_profit_pretax']}**")
    with col2:
        st.markdown(f"**₪{net_profit_pretax:,.0f}**")
    with col3:
        st.markdown(f"**{nppt_pct:.1f}%**")
        
    # Assign opex for compatibility with waterfall
    opex = opex_sum

# --- Final Calculations for Valuation/Metrics ---
investor_share_pct = 0.50
# Net Profit After VAT is now the bottom line for cash flow purposes roughly
# But for valuation, we usually use EBITDA or Net Profit Pre-Tax.
# The user asked for "Total after VAT", so let's use that for the "Net Profit" metric.
# net_profit_after_vat is already calculated above

investor_gross_share = net_profit_pretax * investor_share_pct

# Tax & Net
# Tax is on profit. VAT is already deducted.
# Assuming tax_rate is Income Tax.
investor_tax = investor_gross_share * tax_rate
investor_net_after_tax = investor_gross_share - investor_tax
# investor_economic_profit = investor_net_after_tax - poi_cost * int(poi_active)

# Investment with VAT
investment_cost = asking_price * (1 + vat_rate)

# ROI & Payback
roi = (investor_net_after_tax / investment_cost) * 100 if investment_cost > 0 else 0
payback_years = investment_cost / investor_net_after_tax if investor_net_after_tax > 0 else 999

# Valuation
valuation_multiple_low = DEFAULTS["valuation_multiple_low"]
valuation_multiple_high = DEFAULTS["valuation_multiple_high"]
assets_value = assets_value - depreciation 
val_low = (ebitda * valuation_multiple_low) +  assets_value + stock_value
val_high = (ebitda * valuation_multiple_high) + assets_value + stock_value
stake_val_low = val_low * 0.5
stake_val_high = val_high * 0.5

# --- Populate Metrics ---
with metrics_container:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(LABELS["ebitda"], f"₪{ebitda:,.0f}", help=LABELS["ebitda"])
    col2.metric(LABELS["net_profit_pretax"], f"₪{net_profit_pretax:,.0f}")
    col3.metric(LABELS["investor_net_after_tax"], f"₪{investor_net_after_tax:,.0f}", help=f"After {tax_rate*100:.0f}% tax deduction")
    col4.metric(LABELS["payback_years"], f"{payback_years:.1f} שנים")

with col_left: # Visually Left in RTL
    st.subheader(LABELS["valuation"])

    # Valuation Table
    val_data = {
        "high": [ebitda, valuation_multiple_high, ebitda*valuation_multiple_high, assets_value, stock_value, val_high, stake_val_high],
        "low": [ebitda, valuation_multiple_low, ebitda*valuation_multiple_low, assets_value, stock_value, val_low, stake_val_low],
        "metric": [LABELS["ebitda"], LABELS.get("multiple", "Multiple"), LABELS.get("operational_value", "Operational Value"), LABELS["equipment"], LABELS["stock"], LABELS["total_business_value"], LABELS["stake_value"]],
    }
    df_val = pd.DataFrame(val_data)
    # Formatting
    format_currency = lambda x: f"{x:,.0f} ₪"  # Plain text, currency on right
    format_float = lambda x: f"{x:.1f}x"  # Plain text
    df_val["low"] = df_val.apply(lambda row: format_float(row["low"]) if row["metric"] == LABELS.get("multiple", "Multiple") else format_currency(row["low"]), axis=1)
    df_val["high"] = df_val.apply(lambda row: format_float(row["high"]) if row["metric"] == LABELS.get("multiple", "Multiple") else format_currency(row["high"]), axis=1)
    st.dataframe(df_val, use_container_width=True, hide_index=True)

    # Sensitivity Table
    st.subheader(LABELS.get("roi_vs_price", "ROI vs Purchase Price"))

    prices = [100000, 120000, 140000, 150000, 180000]
    rois = [(investor_net_after_tax / p) * 100 for p in prices]
    paybacks = [p / investor_net_after_tax if investor_net_after_tax > 0 else 0 for p in prices]
    df_sens = pd.DataFrame({
        LABELS.get("payback_years_col", "Payback (Years)"): paybacks,
        LABELS.get("roi_col", "ROI %"): rois,
        LABELS.get("investment_col", "Investment"): prices,
    })
    st.dataframe(df_sens.style.format({
        LABELS.get("investment_col", "Investment"): "₪{:,.0f}",
        LABELS.get("roi_col", "ROI %"): "{:.1f}%",
        LABELS.get("payback_years_col", "Payback (Years)"): "{:.1f}"
    }), hide_index=True, use_container_width=True)

# Visualizations

# Calculate Other OpEx for Waterfall (Total OpEx minus Rent and Salaries which are shown separately)
# Note: All expenses are positive numbers now, so we subtract
other_opex = opex - rent

# Waterfall Chart for Costs
# We need to negate expenses for the waterfall chart to show them as drops
fig_waterfall = go.Figure(go.Waterfall(
    name = "20", orientation = "v",
    measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
    x = [LABELS["revenue"], LABELS["food_cost"], LABELS["gross_profit"], LABELS["salaries_total"], LABELS["rent"], LABELS["opex"], LABELS["ebitda"]],
    textposition = "outside",
    text = [f"{x/1000:.0f}k" for x in [revenue, -cogs, gross_profit, -salaries, -rent, -other_opex, ebitda]],
    y = [revenue, -cogs, gross_profit, -salaries, -rent, -other_opex, ebitda],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig_waterfall.update_layout(showlegend = False)
st.plotly_chart(fig_waterfall, use_container_width=True)
