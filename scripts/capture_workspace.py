"""Capture real workspace screens and a short tour from a running demo server.

Run with DEMO_MODE=1 LLM_PROVIDER=none; then:
python scripts/capture_workspace.py --base http://127.0.0.1:8766
Requires the existing capture extras and Playwright Chromium. Uses a fresh,
isolated browser with shipped fictional data; never calls a live model.
"""

import argparse
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "static/workspace/assets"


def capture(base):
    OUT.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)

        def open_view(fragment):
            page.goto(f"{base}/static/workspace/index.html#{fragment}")
            page.wait_for_function("document.querySelector('#engine-label').textContent.includes('Python')")
            page.locator("#main h1").wait_for()

        open_view("system/example-grid_ops_agent/overview")
        page.locator(".result-panel .risk-high").wait_for()
        page.screenshot(path=str(OUT / "workspace-overview.png"))

        open_view("case/meridian")
        page.locator('[data-start-case="meridian"]').click()
        page.locator('.detail-tabs a[href$="/proposals"]').click()
        page.locator(".proposal-card").first.wait_for()
        page.screenshot(path=str(OUT / "workspace-evidence.png"))

        open_view("system/example-grid_ops_agent/documents")
        page.locator('[data-report="security"]').click()
        page.locator("#document-dialog[open] #document-content h1").wait_for()
        page.screenshot(path=str(OUT / "workspace-report.png"))
        browser.close()

    frames = [Image.open(OUT / f"workspace-{name}.png").convert("RGB")
              for name in ("overview", "evidence", "report")]
    frames[0].save(OUT / "workspace-tour.gif", save_all=True, append_images=frames[1:],
                   duration=[3500, 4500, 4500], loop=0, optimize=True)
    print("Captured three actual workspace screens and workspace-tour.gif")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://127.0.0.1:8766")
    capture(parser.parse_args().base.rstrip("/"))
