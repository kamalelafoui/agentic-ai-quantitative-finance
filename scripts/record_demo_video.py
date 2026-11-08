"""Enregistre la vidéo de démonstration Playground de QuantAgent."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)
BASE = "http://localhost:8007"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"


def wait_assets(page):
    page.wait_for_timeout(1500)
    try:
        page.wait_for_function(
            "() => Array.from(document.images).every(img => img.complete && img.naturalWidth > 0)",
            timeout=30000,
        )
    except Exception:
        pass
    page.wait_for_timeout(800)


def open_menu(page, slug, heading):
    page.goto(f"{BASE}/?menu={slug}", wait_until="networkidle", timeout=60000)
    page.locator("h1", has_text=heading).first.wait_for(timeout=30000)
    wait_assets(page)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="quantagent_video_"))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=CHROME)
            context = browser.new_context(
                viewport={"width": 1600, "height": 1000},
                record_video_dir=str(tmp),
                record_video_size={"width": 1600, "height": 1000},
            )
            page = context.new_page()
            page.emulate_media(reduced_motion="reduce")

            # 1. Accueil + graphiques
            open_menu(page, "overview", "QuantAgent")
            page.wait_for_timeout(1800)
            page.mouse.wheel(0, 520)
            page.wait_for_timeout(2200)
            page.mouse.wheel(0, -520)
            page.wait_for_timeout(1000)

            # 2. Agent : question + réponse
            open_menu(page, "agent", "Agent hybride")
            page.locator("textarea").first.fill(
                "Quel est l'impact estimé d'un choc de +100 pb sur les taux EUR pour le portefeuille Core Europe, "
                "et quelles positions contribuent le plus ?"
            )
            page.wait_for_timeout(600)
            page.get_by_role("button", name="Lancer l'analyse").click()
            page.locator("h3", has_text="Réponse de QuantAgent").first.wait_for(timeout=30000)
            page.wait_for_timeout(3500)

            # 3. Onglet JSON
            try:
                page.get_by_role("tab", name="Traçabilité JSON").click()
                page.wait_for_timeout(3000)
            except Exception:
                pass

            # 4. Onglet HITL
            try:
                page.get_by_role("tab", name="HITL & audit").click()
                page.wait_for_timeout(3000)
            except Exception:
                pass

            # 5. Sécurité
            open_menu(page, "security", "Sécurité & Red Team")
            page.wait_for_timeout(2200)

            # 6. Statistiques
            open_menu(page, "stats", "Statistiques & évaluation")
            page.wait_for_timeout(2200)

            video = page.video
            context.close()
            browser.close()
            webm = Path(video.path())
            print("WEBM", webm)

        mp4 = DOCS / "demo_playground.mp4"
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run(
            [ffmpeg, "-y", "-i", str(webm), "-c:v", "libx264", "-preset", "medium", "-crf", "23",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(mp4)],
            check=True,
            capture_output=True,
        )
        poster = DOCS / "demo_playground_poster.png"
        subprocess.run([ffmpeg, "-y", "-ss", "2", "-i", str(mp4), "-vframes", "1", str(poster)], check=True, capture_output=True)
        print("MP4", mp4, mp4.stat().st_size)
        print("POSTER", poster)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
