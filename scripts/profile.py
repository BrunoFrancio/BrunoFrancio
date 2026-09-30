"""Generate self-contained SVG artwork for the GitHub profile."""
from __future__ import annotations
import argparse, html, json, re, urllib.request
from datetime import UTC, date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USERNAME = "BrunoFrancio"
GREEN, TEXT, MUTED, BG = "#39d353", "#c9d1d9", "#8b949e", "#0d1117"

class ContributionParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.days = {}; self.tooltips = {}; self._for = None; self._text = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "td" and attrs.get("data-date"):
            self.days[attrs.get("id")] = {"date": attrs["data-date"], "level": int(attrs.get("data-level", 0))}
        elif tag == "tool-tip" and attrs.get("for"):
            self._for, self._text = attrs["for"], []
    def handle_data(self, data):
        if self._for: self._text.append(data)
    def handle_endtag(self, tag):
        if tag == "tool-tip" and self._for:
            self.tooltips[self._for] = " ".join(self._text); self._for = None

def parse_contributions(source):
    parser = ContributionParser(); parser.feed(source)
    if not parser.days: raise ValueError("No contribution days found in GitHub response")
    result = []
    for day_id, day in parser.days.items():
        label = parser.tooltips.get(day_id)
        if not label: raise ValueError(f"Missing contribution count for {day['date']}")
        match = re.search(r"(?:(\d[\d,]*) contributions?|No contributions)", label)
        if not match: raise ValueError(f"Invalid contribution label for {day['date']}: {label}")
        count = 0 if match.group(1) is None else int(match.group(1).replace(",", ""))
        result.append({**day, "count": count})
    return sorted(result, key=lambda item: item["date"])

def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "BrunoFrancio-profile/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response: return response.read()

def xml(value): return html.escape(str(value), quote=True)
def write(path, content):
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True); (ROOT / path).write_text(content, encoding="utf-8")

def fetch_contributions():
    days = parse_contributions(fetch(f"https://github.com/users/{USERNAME}/contributions").decode())
    payload = {"updated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"), "days": days}
    write("data/contributions.json", json.dumps(payload, ensure_ascii=False, indent=2) + "\n"); return days

def stats(days):
    counts = {date.fromisoformat(d["date"]): d["count"] for d in days}; cursor = max(counts); current = 0
    while counts.get(cursor, 0) > 0: current += 1; cursor -= timedelta(days=1)
    longest = running = 0
    for day in sorted(counts):
        running = running + 1 if counts[day] > 0 else 0; longest = max(longest, running)
    return sum(d["count"] for d in days), current, longest, max(days, key=lambda d: d["count"])

def render_heatmap(days):
    total, current, longest, best = stats(days); first = date.fromisoformat(days[0]["date"])
    palette = ["#161b22", "#0e4429", "#006d32", "#26a641", GREEN]; boxes, labels, seen = [], [], set()
    months = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    for item in days:
        d = date.fromisoformat(item["date"]); week = (d-first).days//7; weekday = (d.weekday()+1)%7; x, y = 46+week*15, 52+weekday*15
        delay = min((week+weekday)*.012, .72)
        boxes.append(f'<rect class="day" x="{x}" y="{y}" width="11" height="11" rx="2" fill="{palette[item["level"]]}" style="animation-delay:{delay:.3f}s"><title>{item["date"]}: {item["count"]} contribuições</title></rect>')
        key = (d.year, d.month)
        if d.day <= 7 and key not in seen: seen.add(key); labels.append(f'<text x="{x}" y="36">{months[d.month-1]}</text>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="860" height="205" viewBox="0 0 860 205" role="img" aria-label="Calendário de contribuições de Bruno Francio"><style>text{{font:12px ui-monospace,SFMono-Regular,Consolas,monospace;fill:{MUTED}}}.title{{font-size:14px;fill:{TEXT}}}.day{{opacity:0;transform:translateY(-7px);animation:show .35s ease forwards}}@keyframes show{{to{{opacity:1;transform:translateY(0)}}}}@media(prefers-reduced-motion:reduce){{.day{{opacity:1;transform:none;animation:none}}}}</style><rect width="860" height="205" rx="12" fill="{BG}" stroke="#30363d"/><text class="title" x="24" y="25">atividade / últimos 12 meses</text>{''.join(labels)}<text x="18" y="78">seg</text><text x="18" y="108">qua</text><text x="18" y="138">sex</text>{''.join(boxes)}<text x="24" y="181">{total:,} contribuições</text><text x="255" y="181">sequência atual: {current} dias</text><text x="475" y="181">recorde: {longest} dias</text><text x="665" y="181">melhor dia: {best['count']}</text></svg>'''
    return svg.replace(f"{total:,}", f"{total:,}".replace(",", "."))

def render_info():
    rows = [("função","desenvolvedor full-stack"),("foco","produtos, APIs e integrações"),("trabalho","PHP · Laravel · JS/TS · React"),("explorando","IA aplicada · automação · mobile"),("princípio","software simples de manter e evoluir"),("local","Passo Fundo · RS · Brasil")]
    lines = [f'<g class="line" style="animation-delay:{.28+i*.13:.2f}s"><text class="key" x="30" y="{88+i*35}">{xml(k)}</text><text x="145" y="{88+i*35}">{xml(v)}</text></g>' for i,(k,v) in enumerate(rows)]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="330" viewBox="0 0 500 330" role="img" aria-label="Sobre Bruno Francio"><style>text{{font:15px ui-monospace,SFMono-Regular,Consolas,monospace;fill:{TEXT}}}.prompt,.key{{fill:{GREEN}}}.muted{{fill:{MUTED}}}.line{{opacity:0;transform:translateX(-8px);animation:enter .4s ease forwards}}.cursor{{animation:blink 1s steps(1) infinite}}@keyframes enter{{to{{opacity:1;transform:none}}}}@keyframes blink{{50%{{opacity:0}}}}@media(prefers-reduced-motion:reduce){{.line{{opacity:1;transform:none;animation:none}}.cursor{{animation:none}}}}</style><rect width="500" height="330" rx="12" fill="{BG}" stroke="#30363d"/><circle cx="22" cy="22" r="6" fill="#ff5f56"/><circle cx="42" cy="22" r="6" fill="#ffbd2e"/><circle cx="62" cy="22" r="6" fill="#27c93f"/><text class="muted" x="190" y="27">bruno@github</text><text class="prompt" x="30" y="61">$ whoami</text>{''.join(lines)}<text class="prompt" x="30" y="306">$</text><rect class="cursor" x="49" y="293" width="9" height="16" fill="{GREEN}"/></svg>'''

def render_tech_carousel():
    groups = [
        ("Back-end", ["PHP", "Laravel", "Node.js", "Meteor.js", "APIs REST"]),
        ("Front-end", ["React", "Next.js", "Vue.js", "TypeScript", "Tailwind CSS"]),
        ("Dados & automação", ["MySQL", "MongoDB", "Docker", "n8n", "Git & GitHub"]),
    ]
    panels = []
    for index, (title, technologies) in enumerate(groups):
        chips = []
        for item_index, technology in enumerate(technologies):
            column, row = item_index % 2, item_index // 2
            x, y = 24 + column * 148, 112 + row * 58
            width = 136 if column == 0 else 124
            chips.append(
                f'<g><rect x="{x}" y="{y}" width="{width}" height="38" rx="8" '
                f'fill="#161b22" stroke="#30363d"/><text class="tech" x="{x + 12}" '
                f'y="{y + 24}">{xml(technology)}</text></g>'
            )
        panels.append(
            f'<g class="panel panel-{index}"><text class="counter" x="24" y="66">'
            f'0{index + 1} / 03</text><text class="title" x="24" y="94">{xml(title)}</text>'
            f'{"".join(chips)}</g>'
        )
    dots = ''.join(
        f'<circle class="dot dot-{index}" cx="{148 + index * 22}" cy="300" r="4"/>'
        for index in range(3)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="340" height="330" viewBox="0 0 340 330" role="img" aria-label="Carrossel de tecnologias usadas por Bruno Francio"><style>text{{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}}.label{{font-size:12px;fill:{MUTED}}}.counter{{font-size:12px;fill:{GREEN}}}.title{{font-size:20px;font-weight:700;fill:{TEXT}}}.tech{{font-size:13px;fill:{TEXT}}}.panel{{opacity:0;animation:slide 12s ease-in-out infinite}}.panel-1{{animation-delay:-8s}}.panel-2{{animation-delay:-4s}}.dot{{fill:#30363d;animation:dot 12s steps(1) infinite}}.dot-1{{animation-delay:-8s}}.dot-2{{animation-delay:-4s}}@keyframes slide{{0%,27%{{opacity:1;transform:translateX(0)}}30%{{opacity:0;transform:translateX(-12px)}}31%,96%{{opacity:0;transform:translateX(12px)}}100%{{opacity:1;transform:translateX(0)}}}}@keyframes dot{{0%,27%{{fill:{GREEN}}}28%,100%{{fill:#30363d}}}}@media(prefers-reduced-motion:reduce){{.panel,.dot{{animation:none}}.panel{{opacity:0}}.panel-0{{opacity:1}}.dot-0{{fill:{GREEN}}}}}</style><rect width="340" height="330" rx="12" fill="{BG}" stroke="#30363d"/><text class="label" x="24" y="28">stack --rotate</text><path d="M24 42H316" stroke="#30363d"/>{''.join(panels)}{dots}</svg>'''

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--contributions-only",action="store_true"); args=parser.parse_args()
    days=fetch_contributions(); write("assets/contrib-heatmap.svg",render_heatmap(days))
    if not args.contributions_only:
        write("assets/info-card.svg",render_info()); write("assets/tech-carousel.svg",render_tech_carousel())
if __name__ == "__main__": main()
