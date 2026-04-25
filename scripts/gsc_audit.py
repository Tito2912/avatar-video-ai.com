#!/usr/bin/env python3
from __future__ import annotations

import argparse
import bisect
import csv
import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


def _parse_int(value: str) -> int:
    cleaned = value.strip().replace("\u00a0", "").replace(" ", "")
    return int(cleaned) if cleaned else 0


def _parse_float(value: str) -> float:
    cleaned = value.strip().replace("\u00a0", "").replace(" ", "")
    return float(cleaned) if cleaned else 0.0


def _parse_pct(value: str) -> float:
    value = value.strip().replace("%", "")
    return float(value) if value else 0.0


_CTR_CURVE = {
    1: 28.0,
    2: 15.0,
    3: 11.0,
    4: 8.0,
    5: 7.0,
    6: 5.0,
    7: 4.0,
    8: 3.0,
    9: 2.5,
    10: 2.0,
    11: 1.6,
    12: 1.3,
    13: 1.1,
    14: 1.0,
    15: 0.9,
    16: 0.8,
    17: 0.7,
    18: 0.6,
    19: 0.5,
    20: 0.45,
}
_CTR_XS = sorted(_CTR_CURVE)


def _expected_ctr(position: float) -> float:
    if position <= _CTR_XS[0]:
        return _CTR_CURVE[_CTR_XS[0]]
    if position >= _CTR_XS[-1]:
        return max(0.2, _CTR_CURVE[_CTR_XS[-1]] - 0.03 * (position - _CTR_XS[-1]))

    i = bisect.bisect_left(_CTR_XS, position)
    x0, x1 = _CTR_XS[i - 1], _CTR_XS[i]
    y0, y1 = _CTR_CURVE[x0], _CTR_CURVE[x1]
    t = (position - x0) / (x1 - x0)
    return y0 + (y1 - y0) * t


@dataclass(frozen=True)
class MetricRow:
    key: str
    clicks: int
    impressions: int
    ctr_pct: float
    position: float

    @property
    def expected_ctr_pct(self) -> float:
        return _expected_ctr(self.position)

    @property
    def missed_clicks_est(self) -> float:
        exp = self.expected_ctr_pct
        act = self.ctr_pct
        return max(0.0, (exp - act) / 100.0 * self.impressions)


def _read_dim_csv(path: Path) -> list[MetricRow]:
    rows: list[MetricRow] = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return rows
        dim_key = reader.fieldnames[0]
        for row in reader:
            rows.append(
                MetricRow(
                    key=row.get(dim_key, "").strip(),
                    clicks=_parse_int(row.get("Clics", "0")),
                    impressions=_parse_int(row.get("Impressions", "0")),
                    ctr_pct=_parse_pct(row.get("CTR", "0")),
                    position=_parse_float(row.get("Position", "0")),
                )
            )
    return rows


def _read_filters(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row.get("Filtre") or "").strip()
            val = (row.get("Valeur") or "").strip()
            if key:
                out[key] = val
    return out


def _read_graph(path: Path) -> tuple[int, int, float | None, float | None, str | None, str | None]:
    if not path.exists():
        return (0, 0, None, None, None, None)

    clicks = 0
    impressions = 0
    pos_sum = 0.0
    pos_weight = 0
    dates: list[str] = []

    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            c = _parse_int(row.get("Clics", "0"))
            i = _parse_int(row.get("Impressions", "0"))
            p = _parse_float(row.get("Position", "0"))
            clicks += c
            impressions += i
            pos_sum += p * i
            pos_weight += i
            if row.get("Date"):
                dates.append(row["Date"].strip())

    ctr_pct = (clicks / impressions * 100.0) if impressions else None
    avg_pos = (pos_sum / pos_weight) if pos_weight else None
    date_min = min(dates) if dates else None
    date_max = max(dates) if dates else None
    return (clicks, impressions, ctr_pct, avg_pos, date_min, date_max)


def _md_table(headers: list[str], rows: Iterable[list[str]]) -> str:
    out = []
    out.append("| " + " | ".join(headers) + " |")
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return "\n".join(out)


def _fmt_int(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def _fmt_float(n: float | None, digits: int = 2) -> str:
    if n is None:
        return "—"
    return f"{n:.{digits}f}"


def _fmt_pct(n: float | None, digits: int = 2) -> str:
    if n is None:
        return "—"
    return f"{n:.{digits}f}%"


def build_report(folder: Path) -> str:
    filters = _read_filters(folder / "Filtres.csv")
    clicks, impressions, ctr_pct, avg_pos, date_min, date_max = _read_graph(folder / "Graphique.csv")

    pages = _read_dim_csv(folder / "Pages.csv") if (folder / "Pages.csv").exists() else []
    queries = _read_dim_csv(folder / "Requêtes.csv") if (folder / "Requêtes.csv").exists() else []
    countries = _read_dim_csv(folder / "Pays.csv") if (folder / "Pays.csv").exists() else []
    devices = _read_dim_csv(folder / "Appareils.csv") if (folder / "Appareils.csv").exists() else []

    pages_sorted = sorted(pages, key=lambda r: r.impressions, reverse=True)[:10]
    opp_queries = [
        q
        for q in queries
        if q.impressions >= 100 and q.position <= 10 and (q.ctr_pct < 0.5 or q.clicks == 0)
    ]
    opp_queries.sort(key=lambda r: (r.missed_clicks_est, r.impressions), reverse=True)
    opp_queries = opp_queries[:20]

    near_top10 = [q for q in queries if q.impressions >= 100 and 10 < q.position <= 20]
    near_top10.sort(key=lambda r: (r.impressions, -r.position), reverse=True)
    near_top10 = near_top10[:15]

    top_countries = sorted(countries, key=lambda r: r.impressions, reverse=True)[:10]
    top_devices = sorted(devices, key=lambda r: r.impressions, reverse=True)[:10]

    generated = dt.date.today().isoformat()
    scope_lines = []
    if filters:
        scope_lines.append(f"- Type de recherche: {filters.get('Type de recherche', '—')}")
        scope_lines.append(f"- Période (GSC): {filters.get('Date', '—')}")
    if date_min and date_max:
        scope_lines.append(f"- Dates observées (Graphique): {date_min} → {date_max}")

    report = []
    report.append("# Audit SEO (GSC) — avatar-video-ai.com")
    report.append("")
    report.append(f"Date de génération: {generated}")
    report.append("")
    if scope_lines:
        report.append("## Périmètre")
        report.extend(scope_lines)
        report.append("")

    report.append("## KPI")
    report.append(f"- Clics: {_fmt_int(clicks)}")
    report.append(f"- Impressions: {_fmt_int(impressions)}")
    report.append(f"- CTR: {_fmt_pct(ctr_pct, 2)}")
    report.append(f"- Position moyenne (pondérée): {_fmt_float(avg_pos, 2)}")
    report.append("")

    if pages_sorted:
        report.append("## Pages (top impressions)")
        report.append(
            _md_table(
                ["Page", "Impressions", "Clics", "CTR", "Position"],
                [
                    [
                        p.key,
                        _fmt_int(p.impressions),
                        str(p.clicks),
                        _fmt_pct(p.ctr_pct, 2),
                        _fmt_float(p.position, 2),
                    ]
                    for p in pages_sorted
                ],
            )
        )
        report.append("")

    if opp_queries:
        report.append("## Requêtes — opportunités CTR (pos ≤ 10, impr ≥ 100)")
        report.append(
            _md_table(
                ["Requête", "Impr", "Pos", "CTR", "CTR attendu", "Clics manqués (est.)"],
                [
                    [
                        q.key,
                        _fmt_int(q.impressions),
                        _fmt_float(q.position, 2),
                        _fmt_pct(q.ctr_pct, 2),
                        _fmt_pct(q.expected_ctr_pct, 2),
                        _fmt_float(q.missed_clicks_est, 1),
                    ]
                    for q in opp_queries
                ],
            )
        )
        report.append("")

    if near_top10:
        report.append("## Requêtes — proches du top 10 (10 < pos ≤ 20, impr ≥ 100)")
        report.append(
            _md_table(
                ["Requête", "Impr", "Pos", "CTR", "Clics"],
                [
                    [
                        q.key,
                        _fmt_int(q.impressions),
                        _fmt_float(q.position, 2),
                        _fmt_pct(q.ctr_pct, 2),
                        str(q.clicks),
                    ]
                    for q in near_top10
                ],
            )
        )
        report.append("")

    if top_devices:
        report.append("## Appareils (top impressions)")
        report.append(
            _md_table(
                ["Appareil", "Impr", "Clics", "CTR", "Pos"],
                [
                    [
                        d.key,
                        _fmt_int(d.impressions),
                        str(d.clicks),
                        _fmt_pct(d.ctr_pct, 2),
                        _fmt_float(d.position, 2),
                    ]
                    for d in top_devices
                ],
            )
        )
        report.append("")

    if top_countries:
        report.append("## Pays (top impressions)")
        report.append(
            _md_table(
                ["Pays", "Impr", "Clics", "CTR", "Pos"],
                [
                    [
                        c.key,
                        _fmt_int(c.impressions),
                        str(c.clicks),
                        _fmt_pct(c.ctr_pct, 2),
                        _fmt_float(c.position, 2),
                    ]
                    for c in top_countries
                ],
            )
        )
        report.append("")

    report.append("## Notes rapides (CTR)")
    report.append("- Priorité CTR = requêtes déjà en page 1 (pos ~4–9) mais 0 clic: aligner title/meta + sections visibles sur l’intention exacte.")
    report.append("- Quand la position moyenne est >10, l’impact CTR vient surtout d’un gain de positions (passer en top 10) en plus du snippet.")
    report.append("- Le tableau “Clics manqués (est.)” est une approximation (la SERP réelle varie selon features, concurrence, marque, etc.).")
    report.append("")

    return "\n".join(report).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a quick SEO audit from a GSC export folder (FR UI).")
    parser.add_argument("folder", type=Path, help="Path to the GSC export folder (e.g. avatar-video-ai.com-Performance-on-Search-YYYY-MM-DD).")
    parser.add_argument("--out", type=Path, default=None, help="Write the report to this file (Markdown). Defaults to stdout.")
    args = parser.parse_args()

    report = build_report(args.folder)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
