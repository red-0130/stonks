"""Earnings analysis module for quarterly results and upcoming report dates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from stonks.data import StockData


@dataclass
class EarningsRecord:
    """A single quarterly earnings record."""

    date: str
    reported_eps: float | None = None
    estimated_eps: float | None = None
    difference: float | None = None
    surprise_pct: float | None = None
    status: str = "Pending"  # "Beat", "Miss", "Met", "Upcoming"


@dataclass
class EarningsOverview:
    """Aggregated earnings report: latest result, upcoming report, and quarters table."""

    latest: EarningsRecord | None = None
    upcoming: EarningsRecord | None = None
    quarters: list[EarningsRecord] = field(default_factory=list)


def get_earnings_report(stock: StockData) -> EarningsOverview:
    """Extract latest result, upcoming report, and historical quarterly earnings."""
    overview = EarningsOverview()
    cal = stock.calendar or {}
    ed = stock.earnings_dates

    all_records: list[EarningsRecord] = []

    if ed is not None and not ed.empty:
        surprise_col = [c for c in ed.columns if "surprise" in c.lower()]
        for idx, row in ed.iterrows():
            d_str = str(idx.date() if hasattr(idx, "date") else idx)[:10]
            rep = float(row["Reported EPS"]) if pd.notna(row.get("Reported EPS")) else None
            est = float(row["EPS Estimate"]) if pd.notna(row.get("EPS Estimate")) else None
            surp = (
                float(row[surprise_col[0]])
                if surprise_col and pd.notna(row.get(surprise_col[0]))
                else None
            )

            diff = (rep - est) if rep is not None and est is not None else None

            if rep is not None:
                if surp is not None:
                    status = "Beat" if surp > 0.1 else ("Miss" if surp < -0.1 else "Met")
                elif diff is not None:
                    status = "Beat" if diff > 0.001 else ("Miss" if diff < -0.001 else "Met")
                else:
                    status = "Reported"
            else:
                status = "Upcoming"

            all_records.append(
                EarningsRecord(
                    date=d_str,
                    reported_eps=rep,
                    estimated_eps=est,
                    difference=diff,
                    surprise_pct=surp,
                    status=status,
                )
            )

    # Past reported records
    past = [r for r in all_records if r.reported_eps is not None]
    if past:
        overview.latest = past[0]

    # Future / upcoming records
    future = [r for r in all_records if r.reported_eps is None]
    if future:
        # The upcoming record is typically the one with date closest to now
        overview.upcoming = future[-1] if len(future) == 1 else future[0]
        # If estimate is missing from future row, check calendar fallback
        if overview.upcoming.estimated_eps is None and isinstance(cal, dict) and "Earnings Average" in cal:
            overview.upcoming.estimated_eps = cal.get("Earnings Average")
    elif isinstance(cal, dict) and "Earnings Date" in cal and cal["Earnings Date"]:
        ed_list = cal["Earnings Date"]
        u_date = str(ed_list[0]) if isinstance(ed_list, list) and ed_list else str(ed_list)
        u_est = cal.get("Earnings Average")
        overview.upcoming = EarningsRecord(date=u_date, estimated_eps=u_est, status="Upcoming")

    overview.quarters = all_records[:8]
    return overview

