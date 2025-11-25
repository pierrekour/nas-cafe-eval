import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# Page Config
st.set_page_config(page_title="הערכת שווי - קפה נאס", layout="wide")

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
        direction: ltr; 
        text-align: right;
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
    try:
        st.image("nas_logo.png", width=60)
    except:
        pass
with col_head2:
    st.markdown("<h2 style='margin-top: 0; padding-top: 0;'>קפה נאס - הערכת השקעה</h2>", unsafe_allow_html=True)

# --- Sidebar: Inputs ---
st.sidebar.header("1. הגדרות כלליות")
revenue_scenario = st.sidebar.selectbox("בחר תרחיש (לאתחול)", ["שמרני", "ריאלי", "אופטימי"], index=1)

# Defaults based on scenario
if revenue_scenario == "שמרני":
    def_rev = 1300000
    def_cogs_pct = 47.0
elif revenue_scenario == "ריאלי":
    def_rev = 1714000
    def_cogs_pct = 44.0
else:
    def_rev = 2000000
    def_cogs_pct = 40.0

st.sidebar.header("2. מבנה העסקה")
asking_price = st.sidebar.number_input("מחיר מבוקש ל-50%", value=140000, step=5000)
vat_rate = 17.0 / 100.0
poi_active = st.sidebar.checkbox("לכלול עבודה אישית?", value=False)
poi_cost = st.sidebar.number_input("עלות עבודה אישית (POI שנתי)", value=16800, step=1000)
tax_rate = st.sidebar.number_input("מס שולי (לחישוב נטו)", value=47.0, step=1.0) / 100.0

# --- Main Dashboard ---

# Placeholder for metrics
metrics_container = st.container()

# Layout: P&L (Left) | Valuation Analysis (Right)
col_right, col_left = st.columns([1, 1])

with col_right: # Visually Right in RTL
    st.subheader("דו״ח רווח והפסד")

    # Helper to display a row
    def pl_row(label, key, default_val, step=1000, bold=False, is_header=False, is_total=False, indent=False, checkbox=False):
        # Initialize session state if needed
        full_key = f"{revenue_scenario}_{key}"
        if full_key not in st.session_state:
            st.session_state[full_key] = default_val
            
        # Checkbox state
        cb_key = f"{full_key}_active"
        if checkbox and cb_key not in st.session_state:
            st.session_state[cb_key] = False

        col1, col2, col3 = st.columns([2, 1, 1]) # Reduced spacing between label and input
        
        with col1:
            if is_header:
                st.markdown(f"**{label}**")
            elif is_total:
                st.markdown(f"**{label}**")
            else:
                prefix = "&nbsp;&nbsp;&nbsp;&nbsp;" if indent else ""
                if checkbox:
                    # Checkbox near label
                    active = st.checkbox(f"{prefix}{label}", key=cb_key)
                else:
                    st.markdown(f"{prefix}{label}", unsafe_allow_html=True)
                    active = True
                
        with col2:
            if is_header:
                pass
            elif is_total:
                # Calculated total, just display
                val = st.session_state.get(full_key, default_val) # It might be calculated outside
                st.markdown(f"**₪{val:,.0f}**")
            else:
                # Input - Show Positive
                current_val = st.session_state.get(full_key, default_val)
                
                new_val = st.number_input(label, value=current_val, key=full_key, step=step, label_visibility="collapsed")
        
        with col3:
            if not is_header:
                # Calculate %
                val = st.session_state.get(full_key, default_val)
                if checkbox and not st.session_state[cb_key]:
                    val = 0
                
                rev = st.session_state.get(f"{revenue_scenario}_revenue", def_rev)
                pct = (val / rev * 100) if rev != 0 else 0
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
    if rev_key not in st.session_state: st.session_state[rev_key] = def_rev
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("##### הכנסות")
    with col2: revenue = st.number_input("הכנסות", key=rev_key, step=10000, label_visibility="collapsed")
    with col3: st.markdown("100.0%")

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
    if cogs_amt_key not in st.session_state: st.session_state[cogs_amt_key] = def_rev * (def_cogs_pct / 100.0)
    if cogs_pct_key not in st.session_state: st.session_state[cogs_pct_key] = def_cogs_pct

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**עלות סחורה**")
    with col2: cogs = st.number_input("עלות מכר", key=cogs_amt_key, step=1000, on_change=update_cogs_pct, label_visibility="collapsed")
    with col3: cogs_pct = st.number_input("%", key=cogs_pct_key, step=0.5, on_change=update_cogs_amount, label_visibility="collapsed", format="%.1f")

    # 3. Gross Profit
    gross_profit = revenue - cogs # Subtract positive expense
    gp_pct = (gross_profit / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**רווח גולמי**")
    with col2: st.markdown(f"**₪{gross_profit:,.0f}**")
    with col3: st.markdown(f"**{gp_pct:.1f}%**")
        
    # 4. Salaries
    # Positive defaults
    with st.expander("משכורות", expanded=False):
        sal_manager = pl_row("מנהל בית קפה", "sal_manager", 180000, indent=True)
        sal_rami = pl_row("רמי", "sal_rami", 150000, indent=True)
        sal_staff = pl_row("עובדים נוספים", "sal_staff", 300000, indent=True)
    
    salaries = sal_manager + sal_rami + sal_staff
    sal_pct = (salaries / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**סה״כ משכורות**")
    with col2: st.markdown(f"**₪{salaries:,.0f}**")
    with col3: st.markdown(f"**{sal_pct:.1f}%**")

    # 5. OpEx
    # Define OpEx items (Positive defaults)
    opex_items = {
        "rent": ("שכירות", int(def_rev * 0.07)),
        "arnona": ("ארנונה", 45*288),
        "utils": ("חשמל ומים", 22000),
        "comm": ("תקשורת", 2400),
        "marketing": ("שיווק", 1200),
        "maint": ("תחזוקה", 15000),
        "legal": ("הנה״ח ומשרדיות", 12000),
        "fees": ("עמלות/אגרות", 3000), # Added Fees
        "misc": ("שונות", 2000)
    }
    
    opex_sum = 0
    opex_vat_sum = 0
    rent = 0 # Need to extract rent specifically for waterfall
    
    with st.expander("הוצאות תפעול", expanded=False):
        for key, (label, default) in opex_items.items():
            # Checkbox for utils
            use_checkbox = (key == "utils")
            val = pl_row(label, f"opex_{key}", default, indent=True, checkbox=use_checkbox)
            opex_sum += val
            if key == "arnona" or key == "fees":
                continue
            if key == "rent":
                rent = val
            opex_vat_sum += val

    opex_pct = (opex_sum / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**סה״כ הוצאות תפעול**")
    with col2: st.markdown(f"**₪{opex_sum:,.0f}**")
    with col3: st.markdown(f"**{opex_pct:.1f}%**")
    
    # Total Expenses
    total_expenses = salaries + opex_sum
        
    # EBITDA
    ebitda = gross_profit - total_expenses # Subtract positive expenses
    ebitda_pct = (ebitda / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("רווח לפני ריבית, מיסים, פחת והפחתות")
    with col2: st.markdown(f"₪{ebitda:,.0f}")
    with col3: st.markdown(f"{ebitda_pct:.1f}%")
    
    # Depreciation
    depreciation = pl_row("פחת", "depreciation", 12750) # Positive
    
    # Net Profit Pre-Tax
    net_profit_pretax = ebitda - depreciation # Subtract
    nppt_pct = (net_profit_pretax / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**רווח נקי (לפני מס)**")
    with col2: st.markdown(f"**₪{net_profit_pretax:,.0f}**")
    with col3: st.markdown(f"**{nppt_pct:.1f}%**")
    
    # VAT
    # Base = Revenue - COGS - OpEx (Salaries and Depr excluded)
    # All are positive now, so we subtract expenses
    cost_vat_amt = cogs + opex_vat_sum
    cost_vat_base = revenue - cost_vat_amt
    vat_payment = int(cost_vat_base * vat_rate)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("הוצאות מוכרות למע\"מ")
    with col2: st.markdown(f"₪{cost_vat_amt:,.0f}")
    with col3: st.markdown(f"{(cost_vat_amt / revenue * 100) if revenue else 0:.1f}%")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("מע״מ (משוער)")
    with col2: st.markdown(f"₪{vat_payment:,.0f}")
    
    # Net Profit After VAT
    net_profit_after_vat = net_profit_pretax - vat_payment
    npav_pct = (net_profit_after_vat / revenue * 100) if revenue else 0
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1: st.markdown("**רווח נקי (אחרי מע״מ)**")
    with col2: st.markdown(f"**₪{net_profit_after_vat:,.0f}**")
    with col3: st.markdown(f"**{npav_pct:.1f}%**")
    
    # Assign opex for compatibility with waterfall
    opex = opex_sum

# --- Final Calculations for Valuation/Metrics ---
investor_share_pct = 0.50
# Net Profit After VAT is now the bottom line for cash flow purposes roughly
# But for valuation, we usually use EBITDA or Net Profit Pre-Tax.
# The user asked for "Total after VAT", so let's use that for the "Net Profit" metric.
# net_profit_after_vat is already calculated above

investor_gross_share = net_profit_after_vat * investor_share_pct

# Tax & Net
# Tax is on profit. VAT is already deducted.
# Assuming tax_rate is Income Tax.
investor_tax = investor_gross_share * tax_rate
investor_net_after_tax = investor_gross_share - investor_tax
investor_economic_profit = investor_net_after_tax - poi_cost * int(poi_active)

# Investment with VAT
investment_cost = asking_price * (1 + vat_rate)

# ROI & Payback
roi = (investor_net_after_tax / investment_cost) * 100 if investment_cost > 0 else 0
payback_years = investment_cost / investor_net_after_tax if investor_net_after_tax > 0 else 999

# Valuation
valuation_multiple_low = 1.0
valuation_multiple_high = 1.5
assets_value = 85000 
stock_value = 8000

val_low = (ebitda * valuation_multiple_low) + assets_value + stock_value
val_high = (ebitda * valuation_multiple_high) + assets_value + stock_value
stake_val_low = val_low * 0.5
stake_val_high = val_high * 0.5

# --- Populate Metrics ---
with metrics_container:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("EBITDA", f"₪{ebitda:,.0f}", help="רווח לפני ריבית, מיסים, פחת והפחתות. מדד לביצועים התפעוליים של העסק.")
    
    # Conditional coloring
    col2.metric("רווח נקי (אחרי מע״מ)", f"₪{net_profit_after_vat:,.0f}", )
    col3.metric("הרווח הנקי שלך (אחרי מס)", f"₪{investor_net_after_tax:,.0f}", help=f"בניכוי {tax_rate*100:.0f}% מס. רווח כלכלי (בניכוי POI): ₪{investor_economic_profit:,.0f}")
    
    col4.metric("תקופת החזר השקעה", f"{payback_years:.1f} שנים")

with col_left: # Visually Left in RTL
    st.subheader("ניתוח שווי")

    # Valuation Table
    val_data = {
        "גבוה": [ebitda, valuation_multiple_high, ebitda*valuation_multiple_high, assets_value, stock_value, val_high, stake_val_high],
        "נמוך": [ebitda, valuation_multiple_low, ebitda*valuation_multiple_low, assets_value, stock_value, val_low, stake_val_low],
        "מדד": ["EBITDA", "מכפיל", "שווי תפעולי", "ציוד", "מלאי", "שווי עסק כולל", "שווי הנתח שלך (50%)"],
    }
    df_val = pd.DataFrame(val_data)
    
    # Formatting
    format_currency = lambda x: f"{x:,.0f} ₪"  # Plain text, currency on right
    format_float = lambda x: f"{x:.1f}x"  # Plain text
    
    df_val["נמוך"] = df_val.apply(lambda row: format_float(row["נמוך"]) if row["מדד"] == "מכפיל" else format_currency(row["נמוך"]), axis=1)
    df_val["גבוה"] = df_val.apply(lambda row: format_float(row["גבוה"]) if row["מדד"] == "מכפיל" else format_currency(row["גבוה"]), axis=1)

    st.dataframe(df_val, use_container_width=True, hide_index=True)

    # Sensitivity Table
    st.subheader("תשואה (ROI) מול מחיר רכישה")

    prices = [100000, 120000, 140000, 150000, 180000]
    rois = [(investor_net_after_tax / p) * 100 for p in prices]
    paybacks = [p / investor_net_after_tax if investor_net_after_tax > 0 else 0 for p in prices]

    df_sens = pd.DataFrame({
        "החזר (שנים)": paybacks,
        "תשואה %": rois,
        "השקעה": prices,
    })
    st.dataframe(df_sens.style.format({"השקעה": "₪{:,.0f}", "תשואה %": "{:.1f}%", "החזר (שנים)": "{:.1f}"}), hide_index=True, use_container_width=True)

# Visualizations

# Calculate Other OpEx for Waterfall (Total OpEx minus Rent and Salaries which are shown separately)
# Note: All expenses are positive numbers now, so we subtract
other_opex = opex - rent

# Waterfall Chart for Costs
# We need to negate expenses for the waterfall chart to show them as drops
fig_waterfall = go.Figure(go.Waterfall(
    name = "20", orientation = "v",
    measure = ["relative", "relative", "total", "relative", "relative", "relative", "total"],
    x = ["הכנסות", "עלות מכר", "רווח גולמי", "שכירות", "משכורות", "שאר הוצאות", "EBITDA"],
    textposition = "outside",
    text = [f"{x/1000:.0f}k" for x in [revenue, -cogs, gross_profit, -rent, -salaries, -other_opex, ebitda]],
    y = [revenue, -cogs, gross_profit, -rent, -salaries, -other_opex, ebitda],
    connector = {"line":{"color":"rgb(63, 63, 63)"}},
))

fig_waterfall.update_layout(showlegend = False)
st.plotly_chart(fig_waterfall, use_container_width=True)
