"""Capture the README screenshots and the hero GIF from the running app.

Reproducible demo capture (the assets in docs/img/ are real UI captures, not
mock-ups). Run the app first, then this script:

    uvicorn app.main:app --port 8000      # in one terminal
    python scripts/capture_demo.py        # in another

Requires the dev extras with the capture tools:
    pip install -e ".[dev,capture]" && playwright install chromium

Drives the same UI a user would: load an example from the dropdown, classify,
and click through the report tabs. Writes PNGs + demo.gif into docs/img/.
"""

import io
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8000"
OUT = Path(__file__).resolve().parent.parent / "docs" / "img"
VIEWPORT = {"width": 1280, "height": 860}
DSF = 2


def load_and_classify(page, example_value):
    page.goto(BASE, wait_until="networkidle")
    page.add_style_tag(content=".toast{display:none !important}")  # keep captures clean
    page.wait_for_selector(f"#example-select option[value='{example_value}']",
                           state="attached")
    page.eval_on_selector(
        "#example-select",
        "(el, v) => { el.value = v; el.dispatchEvent(new Event('change', {bubbles:true})); }",
        example_value,
    )
    page.wait_for_function("() => document.querySelector('#sys_name').value.length > 0")
    page.click("#btn-assess")
    page.wait_for_function("() => document.querySelector('.tier-badge')")
    page.wait_for_load_state("networkidle")


def select_report(page, rtype, expect_heading):
    page.click(f".report-tabs .tab[data-type='{rtype}']")
    page.wait_for_function(
        "(t) => { const p = document.querySelector('#report-preview');"
        " return p && !p.classList.contains('hidden') && p.innerText.includes(t); }",
        arg=expect_heading,
    )
    page.wait_for_load_state("networkidle")


def scroll_to(page, selector_contains_text, css="#report-preview h2", block="start"):
    page.evaluate(
        "([sel, txt, block]) => { const h = Array.from(document.querySelectorAll(sel))"
        ".find(e => e.textContent.includes(txt)); if (h) h.scrollIntoView({block});"
        " window.scrollBy(0, -16); }",
        [css, selector_contains_text, block],
    )
    time.sleep(0.35)


def shot(page, name):
    path = OUT / name
    page.screenshot(path=str(path))
    print(f"  wrote {path.name} ({path.stat().st_size // 1024} KB)")


def frame(page):
    """Capture the current viewport as an in-memory PIL frame for the GIF."""
    return Image.open(io.BytesIO(page.screenshot())).convert("RGB")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=DSF)
        page = ctx.new_page()
        frames = []

        # --- support_chatbot: severity -> test (offense) -> control (defense)
        #     -> the offense<->defense loop -> data security -> framework matrix -
        load_and_classify(page, "support_chatbot")
        select_report(page, "risk", "EU AI Act classification")   # wait until rendered
        scroll_to(page, "EU AI Act classification")
        frames.append(frame(page))                      # F1: classification + tier

        select_report(page, "security", "Severity overview")
        scroll_to(page, "Severity overview")
        shot(page, "security.png")
        frames.append(frame(page))                      # F2: severity overview table

        select_report(page, "redteam", "Prioritised test cases")
        scroll_to(page, "Summary")
        shot(page, "redteam.png")                       # (unchanged shot point)
        scroll_to(page, "Cross-tenant", css="#report-preview h3")
        frames.append(frame(page))                      # F3: a Critical red-team test (offense)

        select_report(page, "controls", "Prioritised controls")
        scroll_to(page, "Summary")
        shot(page, "controls.png")
        frames.append(frame(page))                      # F4: control catalogue priority summary (defense)

        scroll_to(page, "per-request authorization", css="#report-preview h3")
        frames.append(frame(page))                      # F5: the matching control (validated by the red-team test)

        select_report(page, "datasec", "Applicable data-security risks")
        scroll_to(page, "Applicable data-security risks")
        shot(page, "datasec.png")
        frames.append(frame(page))                      # F6: OWASP GenAI Data Security (DSGAI) findings

        select_report(page, "framework-matrix", "Integration matrix")
        scroll_to(page, "Integration matrix")
        shot(page, "framework-matrix.png")
        frames.append(frame(page))                      # F7: integration matrix (final, lingers)

        # --- hiring (high-risk): classification result + conformity tracker -
        load_and_classify(page, "hiring_cv_screening")
        # Element screenshot of the result content, cropped to a clean banner
        # (tier badge + summary + first findings); avoids empty page background.
        png = page.locator("#result-content").screenshot()
        img = Image.open(io.BytesIO(png))
        img.crop((0, 0, img.width, min(img.height, 760 * DSF))).save(OUT / "result.png")
        print(f"  wrote result.png ({(OUT / 'result.png').stat().st_size // 1024} KB)")

        select_report(page, "compliance", "Penalties")
        scroll_to(page, "Penalties (Art. 99)")
        shot(page, "report.png")

        # --- assemble the hero GIF ------------------------------------------
        gif = [f.resize((f.width // 2, f.height // 2)) for f in frames]  # 1280x860
        gif[0].save(
            OUT / "demo.gif", save_all=True, append_images=gif[1:],
            duration=[2200, 2400, 2600, 2400, 2800, 2600, 3200], loop=0, optimize=True,
        )
        print(f"  wrote demo.gif ({(OUT / 'demo.gif').stat().st_size // 1024} KB, {len(gif)} frames)")

        browser.close()


if __name__ == "__main__":
    sys.exit(main())
