"""Stonks — Stock Analysis Dashboard.

Streamlit application that provides comprehensive stock analysis including
fundamental ratings, earnings results & outlook, analyst forecasts & price targets,
market sentiment, technical analysis, backtested strategies, swing trading,
and Smart Money Concepts (SMC).
"""

from __future__ import annotations

import streamlit as st

from stonks.data import StockData, fetch_stock_data, format_large_number
from stonks.earnings import get_earnings_report
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
    .sector-badge {
        background: rgba(33, 150, 243, 0.15);
        color: #64b5f6;
        border: 1px solid rgba(100, 181, 246, 0.35);
        padding: 5px 14px;
        border-radius: 16px;
        font-size: 0.9em;
        font-weight: 600;
        letter-spacing: 0.5px;
        display: inline-block;
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
    - 🏢 **Company Profile & Sector Badge**
    - 💰 **Key Metric Tiles** — Current Price, Fundamental Grade, Market Cap, Outstanding Shares, Dividend Yield
    - 📋 **Overview** — Fundamentals, latest & upcoming earnings results, quarterly table & market sentiment
    - 🔮 **Forecast** — Wall Street consensus price targets, implied return & technical projected levels
    - 📉 **Technical Analysis** — Detailed indicators (RSI, MACD, BB, MA) & interactive candlestick charts
    - 🎯 **Backtested Strategies** — Actionable strategies with entry/exit points & back-tested success rates
    - 🌊 **Swing Trade Strategy** — Top-down multi-timeframe analysis, supply/demand POIs, and setup explanation
    - 🧠 **SMC Strategy** — Order Blocks, Fair Value Gaps (FVG), BOS/CHoCH, and Liquidity Sweeps
    """)
    st.stop()

# Fetch data
with st.spinner(f"Fetching data for **{ticker}**..."):
    stock = fetch_stock_data(ticker, period=period)

if not stock.valid:
    st.error(f"❌ {stock.error or 'Failed to fetch data. Check the ticker symbol.'}")
    st.stop()

# ---------------------------------------------------------------------------
# Top of page — Company Name, Ticker, and Sector Badge
# ---------------------------------------------------------------------------

st.title(f"{stock.company_name} ({stock.ticker})")

sector_name = stock.sector if stock.sector and stock.sector != "N/A" else "General Sector"
st.markdown(
    f'<div style="margin-top: -12px; margin-bottom: 20px;">'
    f'<span class="sector-badge">🏢 {sector_name}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Section of Tiles — Current Price, Fundamental Grade, Market Cap, Outstanding Shares, Dividend Yield
# ---------------------------------------------------------------------------

# Compute fundamental rating early so grade is available for the tile
rating = rate_stock(stock)

col1, col2, col3, col4, col5 = st.columns(5)

price = stock.current_price
prev_close = stock.info.get("previousClose")
change = ((price / prev_close) - 1) * 100 if price and prev_close else None

# Tile 1: Current Price
col1.metric(
    "Current Price",
    f"${price:,.2f}" if price else "N/A",
    f"{change:+.2f}%" if change is not None else None,
)

# Tile 2: Fundamental Grade
grade_colors = {"A": "🟢", "B": "🟢", "C": "🟡", "D": "🟠", "F": "🔴"}
col2.metric(
    "Fundamental Grade",
    f"{grade_colors.get(rating.grade, '⚪')} Grade {rating.grade}",
    f"{rating.score}/{rating.max_score} Passed",
    delta_color="off",
)

# Tile 3: Market Cap
col3.metric(
    "Market Cap",
    format_large_number(stock.market_cap),
)

# Tile 4: Outstanding Shares
col4.metric(
    "Outstanding Shares",
    format_large_number(stock.shares_outstanding),
)

# Tile 5: Dividend Yield
div_yield = stock.dividend_yield
if div_yield is not None:
    div_val = f"{div_yield:.2f}%"
    div_rate = stock.dividend_rate
    div_sub = f"${div_rate:.2f}/yr" if div_rate else None
else:
    div_val = "N/A"
    div_sub = None

col5.metric(
    "Dividend Yield",
    div_val,
    div_sub,
    delta_color="off",
)

st.divider()

# ---------------------------------------------------------------------------
# Tabbed Views: Overview, Forecast, Technical Analysis, Backtested Strategies,
#               Swing Trade Strategy, SMC Strategy
# ---------------------------------------------------------------------------

tab_overview, tab_forecast, tab_technicals, tab_strategies, tab_swing, tab_smc = st.tabs([
    "Overview",
    "Forecast",
    "Technical Analysis",
    "Backtested Strategies",
    "Swing Trade Strategy",
    "SMC Strategy",
])

# ===========================================================================
# Tab 1: Overview (Fundamentals, Earnings Analysis & Market Sentiment)
# ===========================================================================
with tab_overview:
    # --- Fundamental Analysis Section ---
    st.subheader(f"{grade_colors.get(rating.grade, '⚪')} Fundamental Analysis (Grade {rating.grade})")
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

    st.subheader("📝 Rating Summary")
    st.markdown(rating.summary)

    st.divider()

    # --- Earnings Analysis Section (Latest, Upcoming & Quarterly Table) ---
    st.subheader("📅 Earnings Results & Outlook")
    st.caption("Latest reported earnings performance, upcoming scheduled release, and quarterly historical breakdown.")

    earnings = get_earnings_report(stock)

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        st.markdown("##### 🏁 Latest Earnings Result")
        if earnings.latest:
            latest = earnings.latest
            status_emoji = "🟢" if latest.status == "Beat" else "🔴" if latest.status == "Miss" else "🟡"
            st.markdown(f"**Report Date:** `{latest.date}`")

            le1, le2, le3 = st.columns(3)
            le1.metric("Reported EPS", f"${latest.reported_eps:.2f}" if latest.reported_eps is not None else "N/A")
            le2.metric("EPS Estimate", f"${latest.estimated_eps:.2f}" if latest.estimated_eps is not None else "N/A")

            surp_label = f"{latest.surprise_pct:+.2f}%" if latest.surprise_pct is not None else None
            le3.metric("Surprise", f"{status_emoji} {latest.status}", surp_label)
        else:
            st.info("No recent earnings result reported.")

    with col_e2:
        st.markdown("##### ⏰ Upcoming Earnings Report")
        if earnings.upcoming and earnings.upcoming.date:
            up = earnings.upcoming
            st.markdown(f"**Estimated Release Date:** `{up.date}`")

            ue1, ue2 = st.columns(2)
            ue1.metric("Release Date", up.date)
            est_str = f"${up.estimated_eps:.2f}" if up.estimated_eps is not None else "Pending"
            ue2.metric("Consensus EPS Estimate", est_str)
        else:
            st.info("No upcoming earnings date scheduled.")

    # Table of Quarterly Earnings
    st.markdown("##### 📊 Quarterly Earnings History")
    if earnings.quarters:
        table_rows = []
        for q in earnings.quarters:
            badge = (
                "🟢 Beat"
                if q.status == "Beat"
                else "🔴 Miss"
                if q.status == "Miss"
                else "🟡 Met"
                if q.status == "Met"
                else "⏰ Upcoming"
            )
            diff_display = (
                f"{'+' if q.difference > 0 else ''}${q.difference:.2f}"
                if q.difference is not None
                else "—"
            )
            surp_display = f"{q.surprise_pct:+.2f}%" if q.surprise_pct is not None else "—"
            table_rows.append({
                "Earnings Date": q.date,
                "Reported EPS": f"${q.reported_eps:.2f}" if q.reported_eps is not None else "Pending",
                "EPS Estimate": f"${q.estimated_eps:.2f}" if q.estimated_eps is not None else "N/A",
                "Difference": diff_display,
                "Surprise": surp_display,
                "Outcome": badge,
            })
        st.table(table_rows)
    else:
        st.info("No historical quarterly earnings data available for this ticker.")

    st.divider()

    # --- Market Sentiment Section ---
    st.subheader("🧭 Market Sentiment")
    sentiment = analyse_sentiment(stock)
    st.markdown(sentiment.summary)


# ===========================================================================
# Tab 2: Forecast (Projected Price & Price Targets)
# ===========================================================================
with tab_forecast:
    st.header("🔮 Forecast & Price Targets")
    st.caption("Wall Street analyst consensus price targets, implied return expectations, and technical projected levels.")

    tech = analyse_technicals(stock)
    proj = tech.projected_price

    if proj:
        # Analyst Consensus Price Targets
        p1, p2, p3, p4 = st.columns(4)

        mean_str = f"${proj.target_mean:,.2f}" if proj.target_mean else "N/A"
        upside_str = (
            f"{proj.upside_pct:+.1f}% implied return"
            if proj.upside_pct is not None
            else None
        )
        p1.metric("Projected Mean Target", mean_str, upside_str)

        p2.metric(
            "High Target (Bull Case)",
            f"${proj.target_high:,.2f}" if proj.target_high else "N/A",
        )

        p3.metric(
            "Low Target (Bear Case)",
            f"${proj.target_low:,.2f}" if proj.target_low else "N/A",
        )

        if proj.target_median:
            coverage_label = f"{proj.num_analysts} Analysts" if proj.num_analysts else None
            p4.metric("Median Target", f"${proj.target_median:,.2f}", coverage_label, delta_color="off")
        elif proj.num_analysts:
            p4.metric("Analyst Coverage", f"{proj.num_analysts} Analysts")
        else:
            p4.metric("Technical Pivot", f"${proj.pivot:,.2f}" if proj.pivot else "N/A")

        # 12-Month Forecast Graph
        if proj.chart:
            st.divider()
            st.subheader("📈 12-Month Price Forecast Chart")
            st.plotly_chart(proj.chart, use_container_width=True)

        # Price Target Comparison Table
        st.divider()
        st.markdown("##### 🎯 Target Price vs Current Price")
        curr_price = stock.current_price or 0.0
        target_rows = []
        if proj.target_low:
            low_diff = ((proj.target_low / curr_price) - 1.0) * 100 if curr_price else 0
            target_rows.append({"Target Level": "🔴 Low Target (Bear Case)", "Price": f"${proj.target_low:,.2f}", "Implied Return": f"{low_diff:+.1f}%"})
        if curr_price:
            target_rows.append({"Target Level": "📍 Current Price", "Price": f"${curr_price:,.2f}", "Implied Return": "0.0% (Current)"})
        if proj.target_median:
            med_diff = ((proj.target_median / curr_price) - 1.0) * 100 if curr_price else 0
            target_rows.append({"Target Level": "🟡 Median Target", "Price": f"${proj.target_median:,.2f}", "Implied Return": f"{med_diff:+.1f}%"})
        if proj.target_mean:
            mean_diff = ((proj.target_mean / curr_price) - 1.0) * 100 if curr_price else 0
            target_rows.append({"Target Level": "🟢 Mean Target (Consensus)", "Price": f"${proj.target_mean:,.2f}", "Implied Return": f"{mean_diff:+.1f}%"})
        if proj.target_high:
            high_diff = ((proj.target_high / curr_price) - 1.0) * 100 if curr_price else 0
            target_rows.append({"Target Level": "🟢 High Target (Bull Case)", "Price": f"${proj.target_high:,.2f}", "Implied Return": f"{high_diff:+.1f}%"})
        if target_rows:
            st.table(target_rows)

        # Technical Projected Resistance & Support Levels
        st.divider()
        st.subheader("📐 Technical Projected Levels (Pivot & Range Targets)")
        st.caption("Support and resistance projections derived from classic floor pivots and recent price structure.")
        if proj.resistance_1 or proj.support_1:
            t1, t2, t3, t4 = st.columns(4)
            t1.metric("Resistance 2 (Extended Target)", f"${proj.resistance_2:,.2f}" if proj.resistance_2 else "N/A")
            t2.metric("Resistance 1 (Near-term Target)", f"${proj.resistance_1:,.2f}" if proj.resistance_1 else "N/A")
            t3.metric("Support 1 (Floor Level)", f"${proj.support_1:,.2f}" if proj.support_1 else "N/A")
            t4.metric("Support 2 (Invalidation Floor)", f"${proj.support_2:,.2f}" if proj.support_2 else "N/A")
    else:
        st.info("No forecast or price target data available for this ticker.")


# ===========================================================================
# Tab 3: Technical Analysis (Detailed Technical Analysis & Interactive Chart)
# ===========================================================================
with tab_technicals:
    st.header("📉 Technical Analysis")
    tech = analyse_technicals(stock)

    # Detailed technical analysis summary & signals
    st.markdown(tech.summary)

    # Interactive Chart
    st.divider()
    st.subheader("📊 Interactive Technical Chart")
    if tech.chart:
        st.plotly_chart(tech.chart, use_container_width=True)


# ===========================================================================
# Tab 4: Backtested Strategies
# ===========================================================================
with tab_strategies:
    st.header("🎯 Backtested Strategies")
    st.caption("Actionable algorithmic trade setups with entry/exit levels, risk/reward ratios, and historical back-tested success rates.")

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


# ===========================================================================
# Tab 5: Swing Trade Strategy
# ===========================================================================
with tab_swing:
    st.header("🌊 Swing Trade Strategy")
    st.caption("Top-down multi-timeframe market structure strategy (Weekly & Daily structure, Supply/Demand POIs, min 3:1 R:R)")

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

    # Details of the swing trade setup
    st.subheader("📋 Swing Trade Setup Details")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Weekly Structure (1W)", plan.weekly_trend)
    c2.metric("Daily Structure (1D)", plan.daily_trend)
    c3.metric("Entry Price", f"${plan.entry_price:,.2f}" if plan.entry_price else "Waiting for POI")
    c4.metric("Risk / Reward", f"{plan.risk_reward:.2f}:1" if plan.risk_reward else "N/A")

    if plan.is_tradable and plan.entry_price and plan.stop_loss and plan.target_price:
        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Stop Loss", f"${plan.stop_loss:,.2f}")
        c6.metric("Target Price (3:1 RR)", f"${plan.target_price:,.2f}")
        c7.metric("Potential Gain", f"+{plan.potential_gain:.1f}%")
        c8.metric("Potential Loss", f"-{plan.potential_loss:.1f}%")

    # Demand & Supply POI zones
    cz1, cz2 = st.columns(2)
    demand_str = (
        f"${plan.demand_zone.low_price:,.2f} – ${plan.demand_zone.high_price:,.2f}"
        if plan.demand_zone else "No active demand POI"
    )
    supply_str = (
        f"${plan.supply_zone.low_price:,.2f} – ${plan.supply_zone.high_price:,.2f}"
        if plan.supply_zone else "No active supply POI"
    )
    cz1.info(f"🟢 **Demand Zone (Support POI):** `{demand_str}`")
    cz2.info(f"🔴 **Supply Zone (Resistance POI):** `{supply_str}`")

    # Interactive Chart
    if plan.chart:
        st.plotly_chart(plan.chart, use_container_width=True)

    # Explanation of the Setup
    st.divider()
    st.subheader("💡 Swing Trade Setup Explanation")

    if plan.is_tradable:
        bias_desc = (
            "bullish (seeking BUY / long opportunities)"
            if "BUY" in plan.action
            else "bearish (seeking SELL / short opportunities)"
        )
        poi_kind = "Demand (Support)" if "BUY" in plan.action else "Supply (Resistance)"
        poi_zone = plan.demand_zone if "BUY" in plan.action else plan.supply_zone
        poi_range = (
            f"${poi_zone.low_price:,.2f} – ${poi_zone.high_price:,.2f}"
            if poi_zone else "key structural levels"
        )

        st.markdown(f"""
- **1. Multi-Timeframe Structural Bias:** The macro Weekly structure is currently in a **{plan.weekly_trend}** and the refined Daily structure is in a **{plan.daily_trend}**, establishing an overall **{plan.effective_trend}** bias. Under this alignment, our rules dictate focusing exclusively on {bias_desc}.
- **2. Impulse vs. Correction Rationale:** Rather than buying into overextended impulse moves, the setup waits for a corrective pullback into the {poi_kind} Point of Interest (POI) at `{poi_range}`. This provides institutional value and aligns our entry with the resumption of the pro-trend impulse wave.
- **3. Risk/Reward Asymmetry:** The trade enters at **${plan.entry_price:,.2f}** with a strict Stop Loss anchored beyond structural invalidation at **${plan.stop_loss:,.2f}**. The profit target is set at **${plan.target_price:,.2f}**, producing an asymmetric **{plan.risk_reward:.2f}:1** Risk/Reward ratio (meeting the minimum 3:1 guideline to balance market variance).
- **4. Trade Execution & Management:** Position execution triggers upon price testing the POI and confirming reversal rejection. Once in profit, risk is systematically reduced by trailing stops to breakeven after structural progression, ensuring disciplined capital preservation.
""")
    else:
        st.markdown(f"""
- **1. Market Structure Status:** The market structure is currently in **Consolidation**, oscillating sideways without confirmed higher highs/higher lows (uptrend) or lower highs/lower lows (downtrend).
- **2. Setup Rationale:** Per core swing trading methodology: *'During consolidation phases we simply DO NOT TRADE as there is no clear direction.'* Taking trades in consolidation exposes capital to chop and false breakouts with low statistical edge.
- **3. Key Levels to Watch:** Price is bounded between the Demand POI (`{demand_str}`) and Supply POI (`{supply_str}`). Wait for a clear Break of Structure (BOS) beyond these boundaries before initiating new swing trade positions.
""")

    if plan.total_trades > 0:
        st.markdown(
            f"**Historical Strategy Performance:** `{plan.success_pct:.1f}%` win rate "
            f"({plan.wins} wins out of {plan.total_trades} back-tested trades)"
        )
        st.progress(plan.success_pct / 100)


# ===========================================================================
# Tab 6: SMC Strategy
# ===========================================================================
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
