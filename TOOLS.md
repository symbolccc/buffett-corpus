# TOOLS.md · 仓库体检与导出工具链

> 用途：任何人（或任何 AI）接手本仓库前，先用这套开源工具把仓库"看穿"。全部免费，无账号要求。

## 1. 一键打包给 AI 读：repomix（约 28.9k 星）

```sh
npx repomix
```

生成 repomix-output.txt：全仓库合并为单文件（含结构树），可直接粘给任意 AI 当上下文。只要判据层时：

```sh
npx repomix --include "criteria/**,corpus-index/**,trial/**"
```

## 2. 网页速览：gitingest（约 15.9k 星）

把 GitHub 域名里的 hub 换成 ingest：<https://gitingest.com/symbolccc/buffett-corpus>

无需安装，浏览器打开即得 prompt 友好的全仓文本。

## 3. 死链检查：lychee（约 4k 星）

索引层全是链接，死链=数据腐烂。定期跑：

```sh
lychee --exclude-mail README.md SOURCES.md corpus-index/
```

CI 内可用 lycheeverse/lychee-action 自动检查。

## 4. CI 激活（当前唯一被拦的环节）

GitHub OAuth token 缺 workflow scope，push `.github/workflows/` 会被拒。激活步骤：

```sh
gh auth refresh -h github.com -s workflow
git mv ci/ci.yml .github/workflows/ci.yml
# 从 .gitignore 删除 .github/workflows/ 行
git commit -m "activate CI" && git push
```

CI 会自动跑 `validate.py` + 全部回归测试。

## 5. 每次改动的最小验证

```sh
python scripts/validate.py
python -m unittest discover -s tests
```

两条全绿才允许 push。

## 6. 用本仓库的方法炼化另一个人

复制 `person-agent-template/` 到新目录，按其 README 五步执行；巴菲特版（本仓库）即是填完数据的成品范例。
