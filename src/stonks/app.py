"""Stonks — Stock Analysis Dashboard.

Streamlit application that provides comprehensive stock analysis including
fundamental ratings, market sentiment, technical analysis, swing trading,
Smart Money Concepts (SMC), and algorithmic trade strategies.
"""

from __future__ import annotations

import streamlit as st

from stonks.data import StockData, fetch_stock_data, format_large_number
from stonks.fundamentals import rate_stock
from stonks.sentiment import analyse_sentiment
from stonks.smc import analyse_smc
from stonks.strategies import generate_strategies
from stonks.swing_trade import analyse_swing_trade
from stonks.technicals import analyse_technicals


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Stonks — Stock Analysis",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border-radius: 12px;
        padding: 20px;
        margin: 5px 0;
        border: 1px solid #2a2a4a;
    }
    .pass-badge {
        background: #1b5e20;
        color: #a5d6a7;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .fail-badge {
        background: #b71c1c;
        color: #ef9a9a;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .status-badge-buy {
        background: #1b5e20;
        color: #e8f5e9;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 1.05em;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-sell {
        background: #b71c1c;
        color: #ffebee;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 1.05em;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-neutral {
        background: #e65100;
        color: #fff3e0;
        padding: 6px 14px;
        border-radius: 16px;
        font-size: 1.05em;
        font-weight: 700;
        display: inline-block;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 12px 16px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("📈 Stonks")
    st.caption("Stock Analysis Dashboard")
    st.divider()

    ticker = st.text_input(
        "Enter Ticker Symbol",
        value="",
        placeholder="e.g. AAPL, MSFT, GOOGL",
        help="Enter a valid stock ticker symbol to analyse.",
    ).strip().upper()

    period = st.selectbox(
        "Analysis Period",
        options=["6mo", "1y", "2y", "5y"],
        index=1,
        help="Historical data period for technical, swing trade, and SMC analysis.",
    )

    analyse_btn = st.button("🔍 Analyse", type="primary", use_container_width=True)

    st.divider()
    st.markdown(
        "**Disclaimer:** This is for educational purposes only. "
        "Not financial advice."
    )

# ---------------------------------------------------------------------------
# Main content
# ---------------------------------------------------------------------------

if not ticker or not analyse_btn:
    st.markdown("""
    # 📈 Welcome to Stonks

    Your one-stop **stock analysis dashboard**. Enter a ticker symbol in the
    sidebar to get started.

    ### What you'll get:
    - 💰 **Current Price** & key market metrics
    - 📊 **Fundamental Rating** across 7 quality criteria
    - 🧭 **Market Sentiment** analysis
    - 📉 **Technical Analysis** with interactive charts
    - 🌊 **Swing Trade Strategy** — top-down multi-timeframe analysis (Weekly & Daily structure, supply/demand POIs, min 3:1 R:R)
    - 🧠 **Smart Money Concepts (SMC)** — Order Blocks, Fair Value Gaps (FVG), BOS/CHoCH, and Liquidity Pools
    - 🎯 **All Trade Strategies** with entry/exit points & back-tested success rates
    """)
    st.stop()

# Fetch data
with st.spinner(f"Fetching data for **{ticker}**..."):
    stock = fetch_stock_data(ticker, period=period)

if not stock.valid:
    st.error(f"❌ {stock.error or 'Failed to fetch data. Check the ticker symbol.'}")
    st.stop()

# ---------------------------------------------------------------------------
# Header — Price & key info
# ---------------------------------------------------------------------------

st.title(f"{stock.company_name} ({stock.ticker})")

col1, col2, col3, col4, col5 = st.columns(5)

price = stock.current_price
prev_close = stock.info.get("previousClose")
change = ((price / prev_close) - 1) * 100 if price and prev_close else None

col1.metric("Current Price", f"${price:,.2f}" if price else "N/A",
            f"{change:+.2f}%" if change is not None else None)
col2.metric("Market Cap", format_large_number(stock.market_cap))
col3.metric("Sector", stock.sector)
col4.metric("52W High", f"${stock.info.get('fiftyTwoWeekHigh', 0):,.2f}")
col5.metric("52W Low", f"${stock.info.get('fiftyTwoWeekLow', 0):,.2f}")

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_fundamentals, tab_sentiment, tab_technicals, tab_swing, tab_smc, tab_strategies = st.tabs([
    "📊 Fundamental Rating",
    "🧭 Market Sentiment",
    "📉 Technical Analysis",
    "🌊 Swing Trade (Market Structure)",
    "🧠 Smart Money Concepts (SMC)",
    "🎯 All Strategies",
])

# --- Fundamental Rating ---------------------------------------------------
with tab_fundamentals:
    rating = rate_stock(stock)

    grade_colors = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}
    st.subheader(f"{grade_colors.get(rating.grade, '⚪')} Fundamental Grade: {rating.grade}")
    st.progress(rating.score / rating.max_score)

    cols = st.columns(2)
    for i, criterion in enumerate(rating.criteria):
        with cols[i % 2]:
            status = "✅" if criterion.passed else "❌"
            badge = "PASS" if criterion.passed else "FAIL"
            badge_class = "pass-badge" if criterion.passed else "fail-badge"

            st.markdown(f"""
**{status} {criterion.name}** <span class="{badge_class}">{badge}</span>

{criterion.description}

| Threshold | Actual |
|-----------|--------|
| {criterion.threshold} | {criterion.display_value} |
""", unsafe_allow_html=True)

    st.divider()
    st.subheader("📝 Rating Summary")
    st.markdown(rating.summary)

# --- Sentiment -------------------------------------------------------------
with tab_sentiment:
    sentiment = analyse_sentiment(stock)
    st.markdown(sentiment.summary)

# --- Technical Analysis ----------------------------------------------------
with tab_technicals:
    tech = analyse_technicals(stock)
    st.markdown(tech.summary)

    if tech.chart:
        st.plotly_chart(tech.chart, use_container_width=True)

# --- Swing Trade Strategy (from SWINGTRADE.md) -----------------------------
with tab_swing:
    st.header("🌊 Swing Trade Strategy")
    st.caption("Based on Multi-Timeframe Market Structure, Impulses & Corrections, and Supply/Demand POIs")

    plan = analyse_swing_trade(stock)

    status_class = (
        "status-badge-buy"
        if "BUY" in plan.action
        else "status-badge-sell"
        if "SELL" in plan.action
        else "status-badge-neutral"
    )
    st.markdown(
        f"""
        <div style="margin: 10px 0 20px 0;">
            <span class="{status_class}">{plan.action}</span>
            <span style="margin-left: 15px; font-size: 1.1em; color: #b0bec5;">
                Phase: <b>{plan.phase}</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not plan.is_tradable:
        st.warning(
            "⚠️ **Consolidation Detected — DO NOT TRADE**\n\n"
            "Per the Swing Trade methodology: *'During consolidation phases we simply DO NOT TRADE as there is no clear direction.'*\n\n"
            "The market structure currently shows neither confirmed higher highs/higher lows (uptrend) nor lower highs/lower lows (downtrend). "
            "Wait for a clear structural break before initiating new swing trades."
        )

    # Key Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weekly Trend (1W)", plan.weekly_trend)
    c2.metric("Daily Trend (1D)", plan.daily_trend)
    c3.metric("Entry Price", f"${plan.entry_price:,.2f}" if plan.entry_price else "Waiting")
    c4.metric("Risk / Reward", f"{plan.risk_reward:.2f}:1" if plan.risk_reward else "N/A")

    if plan.is_tradable and plan.entry_price and plan.stop_loss and plan.target_price:
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Stop Loss", f"${plan.stop_loss:,.2f}")
        c6.metric("Target Price (3:1 RR)", f"${plan.target_price:,.2f}")
        c7.metric("Potential Gain", f"+{plan.potential_gain:.1f}%")
        c8.metric("Potential Loss", f"-{plan.potential_loss:.1f}%")

    if plan.chart:
        st.plotly_chart(plan.chart, use_container_width=True)

    st.subheader("📋 5-Step Swing Trade Breakdown")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        with st.expander("1️⃣ Step 1: Top-Down Analysis (Weekly)", expanded=True):
            st.markdown(f"""
            - **Weekly Structure:** `{plan.weekly_trend}`
            - **Trend Bias:** {'Bullish (Buy setup)' if plan.weekly_trend == 'Uptrend' else 'Bearish (Sell setup)' if plan.weekly_trend == 'Downtrend' else 'Neutral / Ranging'}
            - **Concept:** Weekly timeframe determines the macro trend direction. When uptrending (HH & HL) we seek BUYs; when downtrending (LH & LL) we seek SELLs.
            """)

        with col_s2:
            with st.expander("2️⃣ Step 2: Top-Down Analysis (Daily)", expanded=True):
                demand_str = f"${plan.demand_zone.low_price} – ${plan.demand_zone.high_price}" if plan.demand_zone else "N/A"
                supply_str = f"${plan.supply_zone.low_price} – ${plan.supply_zone.high_price}" if plan.supply_zone else "N/A"
                st.markdown(f"""
                - **Daily Structure:** `{plan.daily_trend}`
                - **Demand Zone (POI):** `{demand_str}` (Support)
                - **Supply Zone (POI):** `{supply_str}` (Resistance)
                - **Refinement:** Refine zones and find opportunities inside the larger 1W trend.
                """)

    col_s3, col_s4 = st.columns(2)

    with col_s3:
        with st.expander("3️⃣ Step 3: Confirmation & Execution", expanded=True):
            st.markdown(f"""
            - **Execution Phase:** `{plan.phase}`
            - **Impulse vs Correction:** We aim to enter on **corrections (pullbacks)** into the POI to ride the next **impulsive move**.
            - **Confirmation Trigger:** Execute once price enters the POI and shows price rejection/reversal confirmation.
            """)

        with col_s4:
            with st.expander("4️⃣ Step 4: Trade Management", expanded=True):
                for rule in plan.management_rules:
                    st.markdown(f"- {rule}")

    with st.expander("5️⃣ Step 5: Trade Exits & Risk/Reward Rules", expanded=True):
        for rule in plan.exit_rules:
            st.markdown(f"- {rule}")
        if plan.total_trades > 0:
            st.markdown(
                f"**Back-tested Strategy Win Rate:** `{plan.success_pct:.1f}%` "
                f"(**{plan.wins} wins** out of **{plan.total_trades} trades**)"
            )
        else:
            st.markdown(f"**Back-tested Strategy Win Rate:** `{plan.success_pct:.1f}%`")
        st.progress(plan.success_pct / 100)

# --- Smart Money Concepts (SMC) -------------------------------------------
with tab_smc:
    st.header("🧠 Smart Money Concepts (SMC)")
    st.caption("Institutional Order Flow, Order Blocks (OB), Fair Value Gaps (FVG), BOS/CHoCH, and Liquidity Sweeps")

    smc = analyse_smc(stock)

    smc_status_class = (
        "status-badge-buy"
        if "BUY" in smc.action
        else "status-badge-sell"
        if "SELL" in smc.action
        else "status-badge-neutral"
    )
    st.markdown(
        f"""
        <div style="margin: 10px 0 20px 0;">
            <span class="{smc_status_class}">{smc.action}</span>
            <span style="margin-left: 15px; font-size: 1.1em; color: #b0bec5;">
                Institutional Bias: <b>{smc.bias}</b>
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Confluence score bar
    st.markdown(f"**Institutional Confluence Score:** `{smc.confidence}%`")
    st.progress(smc.confidence / 100)

    # Metrics
    smc1, smc2, smc3, smc4 = st.columns(4)
    smc1.metric("Order Flow Bias", smc.bias)
    smc1_entry = f"${smc.entry_price:,.2f}" if smc.entry_price else "Waiting"
    smc2.metric("Mitigation Entry", smc1_entry)
    smc3.metric("Invalidation (SL)", f"${smc.stop_loss:,.2f}" if smc.stop_loss else "N/A")
    smc4.metric("Liquidity Target (TP)", f"${smc.target_price:,.2f}" if smc.target_price else "N/A")

    if smc.entry_price and smc.stop_loss and smc.target_price:
        smc5, smc6, smc7, smc8 = st.columns(4)
        smc5.metric("Risk / Reward", f"{smc.risk_reward:.2f}:1")
        smc6.metric("Potential Gain", f"+{smc.potential_gain:.1f}%")
        smc7.metric("Potential Loss", f"-{smc.potential_loss:.1f}%")
        win_delta = f"{smc.wins}/{smc.total_trades} wins" if smc.total_trades > 0 else None
        smc8.metric("Historical Win Rate", f"{smc.success_pct:.1f}%", win_delta)

    if smc.chart:
        st.plotly_chart(smc.chart, use_container_width=True)

    st.subheader("💡 SMC Confluence & Market Insights")
    st.markdown(smc.summary)

    st.divider()
    st.subheader("🔍 Institutional Architecture Deep Dive")

    col_ob, col_fvg = st.columns(2)

    with col_ob:
        with st.expander("🧱 Institutional Order Blocks (OB)", expanded=True):
            st.markdown("""
            **What is an Order Block?**
            The last counter-trend candle before a violent institutional expansion (displacement)
            that breaks market structure. Smart money orders remain partially unfulfilled here.
            """)
            if smc.order_blocks:
                ob_data = []
                for ob in smc.order_blocks[-5:]:
                    ob_data.append({
                        "Type": ob.kind,
                        "Range": f"${ob.bottom:,.2f} – ${ob.top:,.2f}",
                        "Volume Ratio": f"{ob.volume_ratio:.1f}x",
                        "Status": "Mitigated" if ob.is_mitigated else "🟢 UNMITIGATED",
                    })
                st.table(ob_data)
            else:
                st.info("No significant order blocks detected.")

    with col_fvg:
        with st.expander("⚡ Fair Value Gaps (FVG / Imbalances)", expanded=True):
            st.markdown("""
            **What is a Fair Value Gap?**
            A 3-candle imbalance where buying or selling was one-sided, leaving an open price void.
            The market gravitates back to these zones for price efficiency (re-balancing).
            """)
            if smc.fvgs:
                fvg_data = []
                for f in smc.fvgs[-5:]:
                    fvg_data.append({
                        "Type": f.kind,
                        "Range": f"${f.bottom:,.2f} – ${f.top:,.2f}",
                        "Size": f"{f.size_pct:.2f}%",
                        "Status": "Mitigated" if f.is_mitigated else "🟡 UNFILLED",
                    })
                st.table(fvg_data)
            else:
                st.info("No active Fair Value Gaps detected.")

    col_struct, col_liq = st.columns(2)

    with col_struct:
        with st.expander("🔄 Market Structure Shifts (BOS & CHoCH)", expanded=True):
            st.markdown("""
            - **CHoCH (Change of Character):** First sign of trend reversal; marks the change of structural order flow.
            - **BOS (Break of Structure):** Trend continuation as price breaches prior swing highs or lows.
            """)
            if smc.choch:
                st.markdown(f"**Latest CHoCH:** `{smc.choch.direction} CHoCH` at `${smc.choch.broken_level:,.2f}`")
                st.caption(smc.choch.description)
            if smc.recent_bos:
                st.markdown("**Recent BOS Events:**")
                for b in smc.recent_bos:
                    st.markdown(f"- `{b.direction} BOS` at `${b.broken_level:,.2f}`")

    with col_liq:
        with st.expander("🎯 Liquidity Pools (BSL & SSL)", expanded=True):
            st.markdown("""
            - **BSL (Buy-Side Liquidity):** Resting buy stops and breakout orders above key swing highs.
            - **SSL (Sell-Side Liquidity):** Resting sell stops and stop-losses below key swing lows.
            Institutions engineer liquidity sweeps before reversing price.
            """)
            if smc.liquidity_pools:
                liq_data = []
                for pool in smc.liquidity_pools[-6:]:
                    liq_data.append({
                        "Pool": pool.kind,
                        "Level": f"${pool.level:,.2f}",
                        "Status": "Swept (Liquidity Grab)" if pool.is_swept else "🎯 OPEN TARGET",
                    })
                st.table(liq_data)

# --- All Trade Strategies ---------------------------------------------------
with tab_strategies:
    st.header("🎯 All Trade Strategies")
    st.caption("Automated technical, institutional (SMC), and market structure strategy setups")

    strategies = generate_strategies(stock)

    if not strategies:
        st.info("Not enough data to generate trade strategies.")
    else:
        for strat in strategies:
            trades_badge = f" ({strat.wins}/{strat.total_trades} wins)" if strat.total_trades > 0 else ""
            with st.expander(
                f"{'🟢' if strat.direction == 'Long' else '🔴'} "
                f"{strat.name} — {strat.direction}  |  "
                f"Win Rate: {strat.success_pct:.1f}%{trades_badge}",
                expanded=True,
            ):
                st.markdown(strat.description)

                sc1, sc2, sc3, sc4 = st.columns(4)
                sc1.metric("Entry Price", f"${strat.entry_price:,.2f}")
                sc2.metric("Stop Loss", f"${strat.stop_loss:,.2f}")
                sc3.metric("Target Price", f"${strat.target_price:,.2f}")
                sc4.metric("Risk/Reward", f"{strat.risk_reward:.2f}")

                col_a, col_b, col_c = st.columns(3)
                col_a.metric("Potential Gain", f"+{strat.potential_gain:.1f}%")
                col_b.metric("Potential Loss", f"-{strat.potential_loss:.1f}%")
                col_c.metric("Timeframe", strat.timeframe)

                # Success rate bar with wins and total trades
                if strat.total_trades > 0:
                    st.markdown(
                        f"**Historical Back-test Performance:** **{strat.success_pct:.1f}%** "
                        f"({strat.wins} wins out of {strat.total_trades} back-tested trades)"
                    )
                else:
                    st.markdown(f"**Historical Back-test Performance:** **{strat.success_pct:.1f}%**")
                st.progress(strat.success_pct / 100)

    st.divider()
    st.caption(
        "⚠️ Strategies are based on back-tested technical patterns, institutional footprints, and market structure. "
        "Past performance does not guarantee future results."
    )
