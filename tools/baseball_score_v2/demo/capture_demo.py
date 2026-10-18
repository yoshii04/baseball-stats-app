"""デモ画面のスクリーンショットと画面録画（webm）を撮る。

前提: demo/docker-compose.yml を起動済み（http://localhost:8090）。
      pip install playwright && playwright install chromium

使い方:
    python demo/capture_demo.py <出力ディレクトリ>
出力:
    dashboard.png / players.png / player-detail.png / pitchers.png / analytics.png / demo.webm
"""
import os
import shutil
import sys

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8090"
VIEWPORT = {"width": 1280, "height": 820}

SHOTS = [
    ("dashboard", "/"),
    ("players", "/players"),
    ("player-detail", "/players/4"),
    ("pitchers", "/pitchers"),
    ("analytics", "/analytics"),
]


def _open(page, path: str, wait_ms: int = 1500) -> None:
    page.goto(BASE_URL + path, wait_until="networkidle")
    page.wait_for_timeout(wait_ms)  # グラフの描画アニメーションを待つ


def _scroll_through(page, steps: int = 4, pause_ms: int = 1200) -> None:
    height = page.evaluate("document.body.scrollHeight")
    for i in range(1, steps + 1):
        page.evaluate(f"window.scrollTo({{top: {height * i // (steps + 1)}, behavior: 'smooth'}})")
        page.wait_for_timeout(pause_ms)
    page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
    page.wait_for_timeout(600)


def take_screenshots(out_dir: str) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_context(viewport=VIEWPORT).new_page()
        for name, path in SHOTS:
            _open(page, path)
            page.screenshot(path=os.path.join(out_dir, f"{name}.png"))
        browser.close()


def record_video(out_dir: str) -> None:
    """ダッシュボード → 打撃成績 → 選手詳細 → 投手成績 → 試合一覧 → 分析 → 実行履歴 の順に巡る。"""
    tmp_dir = os.path.join(out_dir, "_video")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport=VIEWPORT, record_video_dir=tmp_dir, record_video_size=VIEWPORT,
        )
        page = context.new_page()
        _open(page, "/", 2500)
        _scroll_through(page)
        for label in ["打撃成績", "投手成績", "試合一覧", "分析", "実行履歴"]:
            page.get_by_role("link", name=label, exact=True).click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(2000)
            if label == "打撃成績":
                _scroll_through(page, steps=2)
                page.locator("tbody tr").first.click()  # 先頭の選手の詳細へ
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(2500)
                _scroll_through(page, steps=3)
            elif label in ("投手成績", "分析"):
                _scroll_through(page, steps=3)
        context.close()  # 動画ファイルはここで書き出される
        browser.close()
    videos = [f for f in os.listdir(tmp_dir) if f.endswith(".webm")]
    shutil.move(os.path.join(tmp_dir, videos[0]), os.path.join(out_dir, "demo.webm"))
    shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(output, exist_ok=True)
    take_screenshots(output)
    record_video(output)
