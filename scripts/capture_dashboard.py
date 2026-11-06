"""Capture les écrans du dashboard avec Playwright (Chrome installé)."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
BASE = "http://localhost:8007"


def wait_assets(page):
    page.wait_for_timeout(1200)
    try:
        page.wait_for_function(
            "() => Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
            timeout=30000,
        )
    except Exception:
        pass
    page.wait_for_timeout(1200)


def open_menu(page, slug: str, heading: str):
    page.goto(f"{BASE}/?menu={slug}", wait_until="networkidle", timeout=60000)
    page.locator("h1", has_text=heading).first.wait_for(timeout=30000)
    wait_assets(page)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe")
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        page.emulate_media(reduced_motion="reduce")

        open_menu(page, "overview", "QuantAgent")
        page.screenshot(path=str(DOCS / "dashboard_home.png"), full_page=True)
        print("dashboard_home.png")

        open_menu(page, "agent", "Agent hybride")
        textarea = page.locator("textarea").first
        textarea.fill("Quel est l'impact estimé d'un choc de +100 pb sur les taux EUR pour le portefeuille Core Europe, et quelles positions contribuent le plus ?")
        page.get_by_role("button", name="Lancer l'analyse").click()
        page.locator("h3", has_text="Réponse de QuantAgent").first.wait_for(timeout=30000)
        page.wait_for_timeout(1500)
        page.screenshot(path=str(DOCS / "dashboard_agent.png"), full_page=True)
        print("dashboard_agent.png")

        open_menu(page, "security", "Sécurité & Red Team")
        page.screenshot(path=str(DOCS / "dashboard_security.png"), full_page=True)
        print("dashboard_security.png")

        open_menu(page, "stats", "Statistiques & évaluation")
        page.screenshot(path=str(DOCS / "dashboard_stats.png"), full_page=True)
        print("dashboard_stats.png")

        open_menu(page, "graph", "Graphe de connaissances")
        try:
            page.wait_for_selector(".js-plotly-plot", timeout=30000)
        except Exception:
            pass
        page.wait_for_timeout(1200)
        page.screenshot(path=str(DOCS / "dashboard_graph.png"), full_page=True)
        print("dashboard_graph.png")

        browser.close()


if __name__ == "__main__":
    main()
