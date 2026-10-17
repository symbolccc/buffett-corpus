# CI 启用说明
本仓库的 GitHub Actions token 当时没有 workflow scope，push 被拒，故 workflow 先放在 ci/ci.yml。
网络恢复后执行：
1. gh auth refresh-token -s workflow
2. mkdir -p .github/workflows && cp ci/ci.yml .github/workflows/ci.yml（并从 .gitignore 移除该行）
3. git push —— Actions 将自动跑 validate.py + tests/