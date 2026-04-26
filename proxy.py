import requests
from flask import Flask, Response, request, render_template_string
import re, os

app = Flask(__name__)
TARGET = "https://max.ru"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>MAX.ru Desktop</title>
<style>
body{margin:0;background:#0a0a0f;display:flex;align-items:center;
justify-content:center;min-height:100vh;font-family:monospace;}
.box{text-align:center;color:#f0f0f5;padding:20px;}
h1{font-size:48px;color:#e63946;margin-bottom:8px;}
p{color:#6b6b8a;margin-bottom:32px;letter-spacing:2px;}
a{display:inline-block;padding:16px 40px;background:#e63946;color:#fff;
text-decoration:none;font-size:14px;letter-spacing:2px;border-radius:4px;}
</style></head>
<body><div class="box">
<h1>MAX.RU</h1>
<p>DESKTOP MODE</p>
<a href="/proxy/">ОТКРЫТЬ САЙТ</a>
</div></body></html>"""

SESSION = requests.Session()

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/proxy/", defaults={"path": ""})
@app.route("/proxy/<path:path>")
def proxy(path):
    url = f"{TARGET}/{path}"
    if request.query_string:
        url += f"?{request.query_string.decode()}"
    try:
        r = SESSION.get(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.9",
            "Accept-Language": "ru-RU,ru;q=0.9",
        }, allow_redirects=True, timeout=15)
    except Exception as e:
        return f"<p>Ошибка: {e}</p>", 502

    ct = r.headers.get("Content-Type", "text/html")

    if "text/html" in ct:
        # requests автоматически декодирует gzip через .text
        html = r.text

        html = re.sub(
            r'(href|src|action)=["\']https?://(?:www\.)?max\.ru(/[^"\']*)?["\']',
            lambda m: f'{m.group(1)}="/proxy{m.group(2) or "/"}"', html)
        html = re.sub(
            r'(href|src|action)=["\'](/[^"\']*)["\']',
            lambda m: f'{m.group(1)}="/proxy{m.group(2)}"', html)

        return Response(html, content_type="text/html; charset=utf-8")

    return Response(r.content, content_type=ct, status=r.status_code)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
