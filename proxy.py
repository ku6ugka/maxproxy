import requests
from flask import Flask, Response, request, render_template_string
from urllib.parse import urljoin, urlparse
import re

app = Flask(__name__)

TARGET = "https://max.ru"

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

PROXY_HEADERS = {
    "User-Agent": DESKTOP_UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
}

# ─── WebApp HTML-страница ───────────────────────────────────────────────────

WEBAPP_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>MAX.ru — Десктоп</title>
  <script src="https://telegram.org/js/telegram-web-app.js"></script>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }

    :root {
      --bg: #0a0a0f;
      --surface: #13131a;
      --border: #1e1e2e;
      --accent: #e63946;
      --accent2: #ff6b6b;
      --text: #f0f0f5;
      --muted: #6b6b8a;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Courier New', monospace;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 24px;
      overflow: hidden;
    }

    /* Animated grid background */
    body::before {
      content: '';
      position: fixed;
      inset: 0;
      background-image:
        linear-gradient(rgba(230,57,70,0.04) 1px, transparent 1px),
        linear-gradient(90deg, rgba(230,57,70,0.04) 1px, transparent 1px);
      background-size: 40px 40px;
      z-index: 0;
      animation: gridPulse 4s ease-in-out infinite;
    }

    @keyframes gridPulse {
      0%, 100% { opacity: 0.5; }
      50% { opacity: 1; }
    }

    .container {
      position: relative;
      z-index: 1;
      width: 100%;
      max-width: 360px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 32px;
    }

    .logo-block {
      text-align: center;
    }

    .logo-tag {
      font-size: 10px;
      letter-spacing: 4px;
      color: var(--accent);
      text-transform: uppercase;
      margin-bottom: 8px;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 0.2s;
    }

    .logo {
      font-size: 52px;
      font-weight: 900;
      letter-spacing: -2px;
      color: var(--text);
      line-height: 1;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 0.4s;
    }

    .logo span {
      color: var(--accent);
    }

    .logo-sub {
      font-size: 11px;
      letter-spacing: 6px;
      color: var(--muted);
      margin-top: 8px;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 0.6s;
    }

    @keyframes fadeUp {
      from { opacity: 0; transform: translateY(16px); }
      to   { opacity: 1; transform: translateY(0); }
    }

    .status-bar {
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 12px 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 0.8s;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #4ade80;
      flex-shrink: 0;
      animation: blink 1.5s ease-in-out infinite;
    }

    @keyframes blink {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.3; }
    }

    .status-text {
      font-size: 11px;
      color: var(--muted);
      letter-spacing: 1px;
    }

    .status-text strong {
      color: var(--text);
    }

    .btn-open {
      width: 100%;
      padding: 18px;
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 3px;
      text-transform: uppercase;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 1.0s;
      transition: background 0.2s, transform 0.1s;
    }

    .btn-open::before {
      content: '';
      position: absolute;
      top: 0; left: -100%;
      width: 100%; height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
      transition: left 0.4s ease;
    }

    .btn-open:hover::before { left: 100%; }
    .btn-open:hover { background: var(--accent2); }
    .btn-open:active { transform: scale(0.98); }

    .note {
      font-size: 10px;
      color: var(--muted);
      text-align: center;
      line-height: 1.8;
      letter-spacing: 0.5px;
      opacity: 0;
      animation: fadeUp 0.6s ease forwards 1.2s;
    }

    .note a {
      color: var(--accent);
      text-decoration: none;
    }

    #frame-container {
      display: none;
      position: fixed;
      inset: 0;
      z-index: 100;
      flex-direction: column;
      background: #000;
    }

    #frame-container.visible { display: flex; }

    .frame-bar {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }

    .frame-bar-title {
      font-size: 11px;
      letter-spacing: 2px;
      color: var(--muted);
    }

    .frame-close {
      background: var(--accent);
      color: #fff;
      border: none;
      border-radius: 2px;
      font-family: 'Courier New', monospace;
      font-size: 11px;
      letter-spacing: 1px;
      padding: 6px 12px;
      cursor: pointer;
    }

    iframe {
      flex: 1;
      border: none;
      width: 100%;
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="logo-block">
      <div class="logo-tag">// proxy active</div>
      <div class="logo">MA<span>X</span>.RU</div>
      <div class="logo-sub">DESKTOP · MODE</div>
    </div>

    <div class="status-bar">
      <div class="status-dot"></div>
      <div class="status-text">
        User-Agent: <strong>Windows Chrome 120</strong>
      </div>
    </div>

    <button class="btn-open" onclick="openSite()">
      ⬛ Открыть сайт
    </button>

    <div class="note">
      Сайт откроется с десктопным User-Agent.<br/>
      <a href="/webapp">Встроенный просмотр</a> · <a href="https://max.ru" target="_blank">Оригинал</a>
    </div>
  </div>

  <div id="frame-container">
    <div class="frame-bar">
      <span class="frame-bar-title">MAX.RU // DESKTOP MODE</span>
      <button class="frame-close" onclick="closeFrame()">✕ ЗАКРЫТЬ</button>
    </div>
    <iframe id="proxy-frame" src="" title="MAX.ru Desktop"></iframe>
  </div>

  <script>
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      tg.setHeaderColor('#0a0a0f');
      tg.setBackgroundColor('#0a0a0f');
    }

    function openSite() {
      // Открываем прокси-версию в iframe
      const frame = document.getElementById('frame-container');
      const iframe = document.getElementById('proxy-frame');
      iframe.src = '/proxy/';
      frame.classList.add('visible');
    }

    function closeFrame() {
      const frame = document.getElementById('frame-container');
      const iframe = document.getElementById('proxy-frame');
      iframe.src = '';
      frame.classList.remove('visible');
    }
  </script>
</body>
</html>"""


# ─── Маршруты ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Главная страница — редирект на прокси."""
    return render_template_string(WEBAPP_HTML)


@app.route("/webapp")
def webapp():
    """WebApp страница для Telegram."""
    return render_template_string(WEBAPP_HTML)


@app.route("/proxy/", defaults={"path": ""})
@app.route("/proxy/<path:path>")
def proxy(path):
    """Прокси-маршрут — проксирует запросы к max.ru с десктопным UA."""
    url = f"{TARGET}/{path}"
    if request.query_string:
        url += f"?{request.query_string.decode()}"

    try:
        resp = requests.get(
            url,
            headers=PROXY_HEADERS,
            allow_redirects=True,
            timeout=15,
            stream=True,
        )
    except requests.exceptions.RequestException as e:
        return f"<h2>Ошибка прокси</h2><p>{e}</p>", 502

    content_type = resp.headers.get("Content-Type", "text/html")

    # Для HTML — переписываем ссылки, чтобы они шли через прокси
    if "text/html" in content_type:
        html = resp.content.decode("utf-8", errors="replace")

        # Переписываем абсолютные ссылки
        html = re.sub(
            r'(href|src|action)=["\']https?://max\.ru(/[^"\']*)?["\']',
            lambda m: f'{m.group(1)}="/proxy{m.group(2) or "/"}"',
            html,
        )
        # Переписываем относительные ссылки
        html = re.sub(
            r'(href|src|action)=["\'](/[^"\']*)["\']',
            lambda m: f'{m.group(1)}="/proxy{m.group(2)}"',
            html,
        )
        return Response(html, content_type="text/html; charset=utf-8")

    # Для остальных ресурсов (CSS, JS, изображения) — передаём как есть
    return Response(
        resp.iter_content(chunk_size=8192),
        content_type=content_type,
        status=resp.status_code,
        headers={
            k: v for k, v in resp.headers.items()
            if k.lower() not in ("content-encoding", "transfer-encoding", "content-length")
        },
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"✅ Прокси-сервер запущен на http://localhost:{port}")
    print(f"   WebApp: http://localhost:{port}/webapp")
    print(f"   Прокси: http://localhost:{port}/proxy/")
    app.run(host="0.0.0.0", port=port, debug=False)
