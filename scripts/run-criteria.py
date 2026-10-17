#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run-criteria.py - Buffett criteria executor (the judge).

Deterministic pipeline: financials JSON -> field policy (confidence>=0.9,
not_disclosed never guessed) -> 20 criteria -> thresholds firing -> verdict JSON.
Qualitative criteria default to uncertain unless an analyst notes file provides
status + justification (recorded as annotated, never silently).
"""
import json, re, os, sys, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MISSING = ("not_disclosed", "derived_uncertain")

def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)

def fmap(fin):
    return {f["key"]: f for f in fin["fields"]}

def num(fm, key):
    """return (value, usable, conf); usable = numeric and conf >= 0.9."""
    f = fm.get(key)
    if f is None:
        return None, False, None
    v, c = f.get("value"), f.get("confidence", 1.0)
    if isinstance(v, str):          # not_disclosed / derived_uncertain
        return None, False, c
    return float(v), (c >= 0.9), c

def signed_sum(items):
    total = 0.0
    for s in items or []:
        if isinstance(s, (int, float)):
            total += float(s); continue
        for m in re.finditer(r"([-+])\s?(\d+(?:\.\d+)?)", str(s)):
            total += float(m.group(2)) * (1 if m.group(1) == "+" else -1)
    return total

class Judge:
    def __init__(self, fin, notes, crit, thr):
        self.fin, self.notes = fin, notes or {}
        self.thr = {t["id"]: t for t in thr["thresholds"]}
        self.fm = fmap(fin)
        self.log = []
        self.res = {}
        self.missing, self.lowconf = [], []
        for k, f in self.fm.items():
            if isinstance(f.get("value"), str) and f["value"] in MISSING:
                self.missing.append(k)
            elif isinstance(f.get("value"), (int, float)) and f.get("confidence", 1) < 0.9:
                self.lowconf.append({"field": k, "confidence": f["confidence"]})

    def set(self, cid, status, evidence, tags=None):
        auto = status
        n = self.notes.get(cid)
        annotated = False
        if n and n.get("status") != status:
            status = n["status"]; annotated = True
            evidence = "analyst: " + n.get("justification", "")
        self.res[cid] = {"status": status, "evidence": evidence,
                         "tags": tags or [], "auto_status": auto, "annotated": annotated}

    def firing(self, tid, observed, action):
        t = self.thr[tid]
        self.log.append({"threshold": tid, "metric": t["metric"], "bound": t["value"],
                         "direction": t["direction"], "observed": round(observed, 4),
                         "decision_weight": t["decision_weight"], "action": action})

    # ---- auto-evaluable financial criteria ----
    def eval_financials(self):
        ni, ni_ok, _ = num(self.fm, "net_income")
        ocf, ocf_ok, _ = num(self.fm, "ocf")
        det = self.fm.get("non_recurring_detail", {}).get("value")
        det_conf = self.fm.get("non_recurring_detail", {}).get("confidence", 1.0)

        # T-cash-conversion + C-earnings-quality
        tags = []
        if ni_ok and ocf_ok:
            cc = ocf / ni
            self.firing("T-cash-conversion", cc, "cash conversion check")
            eq_status = "pass" if cc >= self.thr["T-cash-conversion"]["value"] else "uncertain"
        else:
            cc, eq_status = None, "uncertain"
            tags.append("ocf_or_ni_not_disclosed")
        if det is not None and ni:
            ratio = abs(signed_sum(det)) / ni
            vio = ratio > self.thr["T-nonrecurring-ratio"]["value"]
            self.firing("T-nonrecurring-ratio", ratio, "excess->earnings-quality review" if vio else "within bound")
            if det_conf < 0.9:
                tags.append("uncertain_source(conf<0.9)")
            if vio:
                eq_status = "uncertain"
        self.set("C-earnings-quality", eq_status,
                 "OCF/NI={0} nonrec_ratio={1}".format(round(cc, 3) if cc else "n/a",
                                                      round(ratio, 4) if det is not None and ni else "n/a"),
                 tags)

        # C-owner-earnings
        da, da_ok, _ = num(self.fm, "da")
        capm, capm_ok, _ = num(self.fm, "capex_maintenance")
        capx, capx_ok, _ = num(self.fm, "capex_total")
        wc, wc_ok, wc_conf = num(self.fm, "working_capital_delta")
        cap = capm if capm is not None else capx
        cap_ok = capm_ok if capm is not None else capx_ok
        oe_tags = []
        if capm is None and capx is not None:
            oe_tags.append("conservative_total_capex(capex_maintenance not_disclosed)")
        if wc is not None and not wc_ok:
            oe_tags.append("low_conf_working_capital(conf={0})".format(wc_conf))
        if ni and ni_ok and da is not None and da_ok and cap is not None and cap_ok:
            oe = ni + da - cap - (wc if wc is not None else 0.0)
            self.set("C-owner-earnings", "pass" if oe > 0 else "fail",
                     "NI+D&A-capex(-WC)={0}".format(round(oe, 3)), oe_tags)
        else:
            self.set("C-owner-earnings", "uncertain",
                     "inputs not_disclosed/low-conf", oe_tags + ["missing_inputs"])

        # C-debt-survival
        debt, debt_ok, _ = num(self.fm, "interest_bearing_debt")
        ebitda, ebit_ok, _ = num(self.fm, "ebitda")
        cash, cash_ok, _ = num(self.fm, "cash_and_equivalents")
        na, na_ok, _ = num(self.fm, "net_assets_attributable")
        if debt is not None and debt_ok and ebitda is not None and ebit_ok:
            lev = debt / ebitda
            self.firing("T-leverage-ebitda", lev, "within bound" if lev <= self.thr["T-leverage-ebitda"]["value"] else "excess->review")
            ok_lev = lev <= self.thr["T-leverage-ebitda"]["value"]
            net_cash = (cash - debt) if cash is not None else None
            ok_cash = (net_cash is None) or (net_cash > 0)
            ds_tags = []
            ie, ie_ok, _ = num(self.fm, "interest_expense")
            if ie is None:
                ds_tags.append("interest_coverage_skipped(not_disclosed)")
            self.set("C-debt-survival", "pass" if (ok_lev and ok_cash) else "fail",
                     "debt/ebitda={0} net_cash={1}".format(round(lev, 3), round(net_cash, 3) if net_cash is not None else "n/a"),
                     ds_tags)
        else:
            self.set("C-debt-survival", "uncertain",
                     "debt/ebitda/cash not_disclosed or low-conf", ["missing_inputs"])

        # T-receivables + T-customer-concentration
        ar, ar_ok, _ = num(self.fm, "receivables")
        pre, pre_ok, _ = num(self.fm, "prepayments")
        if ar is not None and ar_ok and na is not None and na_ok:
            rr = (ar + (pre if pre is not None and pre_ok else 0.0)) / na
            self.firing("T-receivables-net-assets", rr, "within bound" if rr <= 3.0 else "excess->review")
            tg = [] if pre is not None else ["prepayments_not_disclosed"]
            self.set("C-receivables-risk", "pass" if rr <= self.thr["T-receivables-net-assets"]["value"] else "uncertain",
                     "(AR+pre)/NA={0}".format(round(rr, 3)), tg)
        else:
            self.set("C-receivables-risk", "uncertain", "inputs not_disclosed", ["missing_inputs"])
        cc_top, cc_ok, _ = num(self.fm, "customer_concentration_top1")
        if cc_top is None:
            self.firing("T-customer-concentration", -1, "not_disclosed -> uncertain (rule: no guessing)")
            self.set("C-customer-risk", "uncertain", "top1 concentration not_disclosed")
        else:
            self.set("C-customer-risk", "pass" if cc_top <= 0.5 else "uncertain",
                     "top1={0}".format(cc_top))

    def run(self):
        crit = load(os.path.join(ROOT, "criteria", "criteria.json"))
        ids = [c["id"] for c in crit["criteria"]]
        # gate (analyst-only by design)
        gate = self.notes.get("C-circle-competence", {}).get("status", "not_scorable")
        self.res["gate_C-circle-competence"] = {"status": gate,
            "evidence": self.notes.get("C-circle-competence", {}).get("justification", ""),
            "tags": [], "auto_status": "not_scorable", "annotated": "C-circle-competence" in self.notes}
        if gate != "pass":
            for i in ids: self.res.setdefault(i, {"status": "not_scored", "evidence": "gate not passed", "tags": [], "auto_status": "n/a", "annotated": False})
            return self.overall("not_scorable")
        self.eval_financials()
        # qualitative defaults: uncertain unless annotated
        qual = {
            "C-inversion": "needs analyst top-3 loss paths",
            "C-time-horizon": "needs 10y endgame statement",
            "C-durability": "needs disruption list + lifecycle evidence",
            "C-moat-replicability": "needs 5-type moat elimination evidence",
            "C-moat-trend": "needs >=5y margin/share trend (cyclical confusion guard)",
            "C-pricing-power": "needs raise-price history + elasticity",
            "C-wonderful-at-fair": "needs franchise/commodity classification",
            "C-institutional-imperative": "needs M&A history + capital allocation review",
            "C-mgmt-integrity": "needs audited disclosure review (quarterly=review only)",
            "C-risk-three-class": "needs three explicit risks",
            "C-margin-of-safety": "no valuation input -> uncertain (rule: no buy/sell without price)",
            "C-price-vs-value": "no intrinsic value range -> uncertain",
            "C-sell-1-overvalued": "no price vs value range",
            "C-sell-2-moat-destroyed": "depends on C-moat-trend",
            "C-sell-3-integrity": "no fraud evidence file",
            "C-sell-4-better-opportunity": "no candidate list",
        }
        for i, why in qual.items():
            self.set(i, "uncertain", why)
        # map analyst keys for criteria that also match ids (e.g. notes used same ids)
        return self.overall(None)

    def overall(self, forced):
        if forced:
            return self.out(forced, [])
        veto_fail = [k for k in ("C-mgmt-integrity", "C-sell-3-integrity") if self.res.get(k, {}).get("status") == "fail"]
        cores = [k for k, v in self.res.items() if v["status"] in ("fail", "uncertain", "flag")]
        if veto_fail:
            ov = "建议打回"
        elif any(self.res[k]["status"] == "fail" for k in self.res):
            ov = "建议打回"
        elif cores:
            ov = "需人工核验"
        else:
            ov = "建议通过"
        return self.out(ov, cores)

    def out(self, overall, review_needed):
        return {
            "case": self.fin.get("company"), "period": self.fin.get("period"),
            "schema_version": "1.0",
            "overall": overall,
            "field_handling": {"usable": len(self.fm) - len(self.missing) - len(self.lowconf),
                                "not_disclosed": self.missing, "low_confidence": self.lowconf,
                                "rule": "conf<0.9 or not_disclosed never counts as evidence"},
            "threshold_firing": self.log,
            "criteria": self.res,
            "review_needed_criteria": review_needed,
            "notes_applied": sorted([k for k, v in self.res.items() if v.get("annotated")]),
        }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--financials", required=True)
    ap.add_argument("--notes")
    ap.add_argument("--out")
    a = ap.parse_args()
    fin = load(a.financials)
    notes = {}
    if a.notes:
        for n in load(a.notes):
            notes[n["criterion"]] = n
    verdict = Judge(fin, notes, None, load(os.path.join(ROOT, "criteria", "thresholds.json"))).run()
    text = json.dumps(verdict, ensure_ascii=False, indent=2)
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("WROTE", a.out)
    print("OVERALL:", verdict["overall"], "| cases:", verdict["case"])
    fails = [k for k, v in verdict["criteria"].items() if v["status"] == "fail"]
    print("FAIL:", fails or "-")
    print("FIRING:", [(t["threshold"], t["observed"]) for t in verdict["threshold_firing"]])
    return 0

if __name__ == "__main__":
    sys.exit(main())