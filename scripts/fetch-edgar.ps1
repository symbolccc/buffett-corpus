# fetch-edgar.ps1 - pull BRK filing INDEX (no full text) into track-record/
# usage: powershell -File fetch-edgar.ps1 [-Cik 0001067983] [-Max 200]
param([string]$Cik = "0001067983", [int]$Max = 200)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$out = Join-Path $root "track-record"
if (-not (Test-Path -LiteralPath $out)) { New-Item -ItemType Directory -Path $out -Force | Out-Null }
$ua = "research-contact@example.com"
$url = "https://data.sec.gov/submissions/CIK$Cik.json"
$r = Invoke-RestMethod -Uri $url -UserAgent $ua -TimeoutSec 60
$f = $r.filings.recent
$rows = @()
for ($i = 0; $i -lt $f.form.Count; $i++) {
  if ($f.form[$i] -match '^(13F-HR|13F-HR/A|SC 13D|SC 13D/A|SC 13G|SC 13G/A|4|10-K|10-K/A)$') {
    $rows += [pscustomobject]@{
      form = $f.form[$i]; filingDate = $f.filingDate[$i]; reportDate = $f.reportDate[$i]
      accession = $f.accessionNumber[$i]; primaryDoc = $f.primaryDocument[$i]
    }
  }
  if ($rows.Count -ge $Max) { break }
}
$payload = [pscustomobject]@{
  cik = $Cik; name = $r.name; tickers = $r.tickers
  fetched_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
  window_note = "EDGAR submissions recent window only; oldest in this pull: " + (($rows | ForEach-Object { $_.filingDate } | Sort-Object)[0])
  count = $rows.Count; filings = $rows
}
$dst = Join-Path $out "holdings-index.json"
$payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $dst -Encoding UTF8
$hist = @{}
foreach ($x in $rows) { $hist[$x.form] = 1 + [int]$hist[$x.form] }
Write-Output ("wrote " + $dst)
Write-Output ("  total=" + $rows.Count)
$hist.GetEnumerator() | Sort-Object Value -Descending | ForEach-Object { Write-Output ("   " + $_.Key.PadRight(10) + " x" + $_.Value) }