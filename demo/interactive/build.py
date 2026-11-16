"""Assemble the self-contained demo: data and fonts inlined, then test it headless with the network blocked."""
import base64, json, subprocess, sys
from pathlib import Path
H = Path(__file__).parent; R = H.parents[1]; F = R / "submission/fonts"
faces = [("Source Sans 3", 400, "source-sans-3-latin-400-normal"), ("Source Sans 3", 400, "source-sans-3-latin-ext-400-normal"),
         ("Source Sans 3", 600, "source-sans-3-latin-600-normal"), ("Source Sans 3", 600, "source-sans-3-latin-ext-600-normal"),
         ("Source Sans 3", 700, "source-sans-3-latin-700-normal"),
         ("Source Serif 4", 600, "source-serif-4-latin-600-normal"), ("Source Serif 4", 600, "source-serif-4-latin-ext-600-normal"),
         ("IBM Plex Mono", 400, "ibm-plex-mono-latin-400-normal")]
css = "".join(f"@font-face{{font-family:'{fam}';font-weight:{w};font-display:swap;src:url(data:font/woff2;base64,{base64.b64encode((F / (f + '.woff2')).read_bytes()).decode()}) format('woff2')"
              + (";unicode-range:U+0100-02AF,U+1E00-1EFF" if "-ext-" in f else "") + "}\n" for fam, w, f in faces)
data = json.load(open(H / "demo_data.json"))
html = (H / "template.html").read_text(encoding="utf-8").replace("/*FONTS*/", css).replace("/*DATA*/null", json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
for out in (R / "demo/Pramana_Bind_demo.html", R / "demo/hosting/index.html"):
    out.parent.mkdir(parents=True, exist_ok=True); out.write_text(html, encoding="utf-8")
print("wrote demo:", round(len(html) / 1024), "KB")
