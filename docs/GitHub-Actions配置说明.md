# GitHub Actions CI/CD配置说明

由于当前Personal Access Token缺少workflow scope，无法自动推送workflow文件。
请手动将以下配置文件添加到GitHub仓库。

---

## 配置文件位置

`.github/workflows/ci.yml`
`.github/workflows/docker.yml`

---

## CI配置文件内容

```yaml
# PM Digital Employee - CI Pipeline
name: CI

on:
  push:
    branches: [ master, main ]
  pull_request:
    branches: [ master, main ]

jobs:
  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install pytest pytest-asyncio pytest-cov pytest-mock
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short --cov=app --cov-report=term-missing

  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ruff black
      - run: ruff check app/ tests/
      - run: black --check app/ tests/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install bandit
      - run: bandit -r app/ -ll --skip B101
```

---

## 操作步骤

1. 打开GitHub仓库: https://github.com/zhangyiyuqirose-eng/pm-digital-employee
2. 点击"Add file" → "Create new file"
3. 输入路径: `.github/workflows/ci.yml`
4. 复制上述YAML内容到文件
5. 点击"Commit new file"
6. 重复步骤创建docker.yml（可选）

---

**创建时间**: 2026-04-17 10:00 GMT+8