# End‑to‑End Ad‑Load Performance Tester

A command‑line tool for measuring full‑page and ad‑slot load performance under real‑world browser conditions. Injects JavaScript into publisher pages (including iframe‑based ads), tracks Web Vitals and Prebid.js events, captures screenshots, and outputs a rich set of metrics for regression testing, optimization, and CI integration.

---

## Table of Contents

1. [Features](#features)
2. [Requirements](#requirements)
3. [Installation (Dev)](#installation-dev)
4. [Quick Start](#quick-start)
5. [CLI Usage](#cli-usage)
6. [Configuration](#configuration)
7. [Testing](#testing)
8. [Project Layout](#project-layout)

---

## Features

* **Headless Chrome** automation via Chrome DevTools Protocol
* **Web Vitals** metrics: TTFB, FCP, LCP, DOMContentLoaded, load event
* **Ad‑slot instrumentation** with Prebid.js event listeners (auction, bids, wins, render success/failure)
* **Multi‑frame support** (nested iframes, cross‑origin attach)
* **Real‑time console logs** and optional screenshot capture
* **CLI‑first**: simple commands, subcommands, and flags
* **CI/CD ready**: reproducible, scriptable runs for regression testing

---

## Requirements

* **Python** ≥ 3.11
* **Chromium** or **Chrome** installed on the host
* (Optional) `chromedriver` or ability to launch Chrome via DevTools

---

## Installation (Dev)

To set up for local development and get the latest code changes instantly:

```bash
git clone https://gitlab.infr.zglbl.net/VLin/ad-load-performance-testing
cd ad-load-performance-testing
pip install -e .
```

This installs your package in "editable" mode; edits under `src/ad_load/…` and top‑level assets are picked up immediately.

---

## Quick Start

Run a bare Disqus thread only page:

```bash
ad-load run boxing --bare
```

Run full‑page:

```bash
ad-load run https://example.com
```

List built‑in site shortcuts:

```bash
ad-load list
```

---

## CLI Usage

```
ad-load [OPTIONS] COMMAND [ARGS]...
```

### Commands

| Command | Description                               |
| :------ | :---------------------------------------- |
| `run`   | Execute performance test for URL/shortcut |
| `list`  | Display available site shortcuts          |

### `run` Options

```
Usage: ad-load run [OPTIONS] TARGET

Arguments:
  TARGET         site key or URL

Options:
  --bare         only render Disqus embed (skip full‑page assets)
  --headless     launch Chrome in headless mode
  -h, --help     show this message and exit
```

---

## Configuration

Chrome launch flags are defined in `ad_load/utils/make_chrome_options.py`. By default:

* `--disable-blink-features=AutomationControlled`
* `--disable-web-security`
* `--no-sandbox`
* `--disable-dev-shm-usage`

To customize flags, edit `make_chrome_options.py` or extend via future CLI options.

---

## Testing

Run all tests:

```bash
pytest -q
```

---

## Project Layout

```
├── templates/                 # HTML templates disqus only
├── injected_scripts/          # JavaScript snippets for injection
├── pyproject.toml             # package metadata, entry points
├── src/
│   └── ad_load/
│       ├── cli.py             # console entry point
│       ├── modes/             # workflows (disqus_only, full_page)
│       ├── loaders/           # script, template, site loaders
│       └── utils/             # helpers (Injector, Chrome options, etc...)
├── tests/                     # pytest test suite
└── README.md                  # this file
```

Note that **`templates/`** and **`injected_scripts/`** live at the top level, not under `src/`.