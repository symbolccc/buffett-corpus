import json, subprocess, sys, os, tempfile, unittest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_case(name):
    out = os.path.join(tempfile.gettempdir(), name + ".verdict.json")
    r = subprocess.run([sys.executable, os.path.join(ROOT,"scripts","run-criteria.py"),
                    "--financials", os.path.join(ROOT,"trial",name+".financials.json"),
                    "--notes", os.path.join(ROOT,"trial",name+".notes.json"),
                    "--out", out], capture_output=True)
    assert r.returncode == 0, r.stderr.decode("utf-8","replace")
    with open(out, encoding="utf-8") as fh:
        return json.load(fh)

class TestSamsung(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = run_case("samsung-2Q26")
    def test_overall_manual_review(self):
        self.assertEqual(self.v["overall"], "需人工核验")
    def test_gate_pass(self):
        self.assertEqual(self.v["criteria"]["C-circle-competence"]["status"], "pass")
    def test_earnings_quality_pass_with_tag(self):
        c = self.v["criteria"]["C-earnings-quality"]
        self.assertEqual(c["status"], "pass")
        self.assertTrue(any("uncertain_source" in t for t in c["tags"]))
    def test_owner_earnings_positive(self):
        self.assertEqual(self.v["criteria"]["C-owner-earnings"]["status"], "pass")
    def test_debt_survival_pass(self):
        self.assertEqual(self.v["criteria"]["C-debt-survival"]["status"], "pass")
    def test_moat_trend_uncertain_cyclical(self):
        self.assertEqual(self.v["criteria"]["C-moat-trend"]["status"], "uncertain")
    def test_no_valuation_uncertain(self):
        self.assertEqual(self.v["criteria"]["C-margin-of-safety"]["status"], "uncertain")
    def test_firing_values(self):
        f = {x["threshold"]: x["observed"] for x in self.v["threshold_firing"]}
        self.assertAlmostEqual(f["T-cash-conversion"], 1.4676, places=3)
        self.assertLess(f["T-nonrecurring-ratio"], 0.30)
        self.assertAlmostEqual(f["T-leverage-ebitda"], 0.2206, places=3)

class TestSKHynix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = run_case("skhynix-2Q26")
    def test_overall_manual_review(self):
        self.assertEqual(self.v["overall"], "需人工核验")
    def test_earnings_quality_uncertain(self):
        self.assertEqual(self.v["criteria"]["C-earnings-quality"]["status"], "uncertain")
    def test_nonrecurring_firing_above_threshold(self):
        f = {x["threshold"]: x["observed"] for x in self.v["threshold_firing"]}
        self.assertGreater(f["T-nonrecurring-ratio"], 0.30)
        self.assertLess(f["T-nonrecurring-ratio"], 0.40)
    def test_debt_survival_annotated(self):
        c = self.v["criteria"]["C-debt-survival"]
        self.assertEqual(c["auto_status"], "uncertain")
        self.assertTrue(c["annotated"])
    def test_not_disclosed_at_least_12(self):
        self.assertGreaterEqual(len(self.v["field_handling"]["not_disclosed"]), 12)
    def test_customer_concentration_uncertain_no_guess(self):
        self.assertEqual(self.v["criteria"]["C-customer-risk"]["status"], "uncertain")

if __name__ == "__main__":
    unittest.main()