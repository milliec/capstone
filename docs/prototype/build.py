"""Builds the static mock-up pages in this folder.

Run:  python3 build.py
It writes plain .html files next to app.css. The pages have no JavaScript and no logic: every
number, date and status is typed in here as fictional demo data (fund FND-DEMO-01).
Edit the text here and run it again, so the sidebar and header stay the same on every page.
"""
import re
from datetime import date
from pathlib import Path

OUT = Path(__file__).parent
FUND = "Bramblegate Credit Opportunities SICAV"

# Icons are from Iconoir (iconoir.com, MIT licence). The SVG files live in icons/ and are placed
# inline in each page, so nothing is loaded from the network and CSS can colour them.
def _icon(name):
    svg = (OUT / "icons" / f"{name}.svg").read_text()
    inner = re.sub(r'\s(stroke|stroke-width)="[^"]*"', "", svg[svg.index(">") + 1:svg.rindex("</svg>")])
    return f'<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">{inner.strip()}</svg>'


ICON = {k: _icon(v) for k, v in {"cal": "calendar", "book": "book", "list": "list", "next": "clock", "move": "arrow-right",
                                 "care": "warning-triangle", "doc": "page", "check": "check", "flag": "white-flag", "fund": "building"}.items()}


def chip(text, kind=""):
    return f'<span class="chip {kind}">{text}</span>'


def kpi(k, v, m="", icon="cal", cls="", text=False, href=""):
    val = f'<a href="{href}" style="color:inherit">{v}</a>' if href else v
    return (f'<div class="kpi {cls}"><div class="k">{k}</div><div class="v num{" text" if text else ""}">{val}</div>'
            f'<div class="m">{m}</div><span class="ic" aria-hidden="true">{ICON[icon]}</span></div>')


def page(title, body, active="calendar", role="specialist", waiting=True, style="", fund=None, fund_note="Luxembourg UCI Part II · year end 31 Dec"):
    """The shared frame: white sidebar panel + main column."""
    cur = lambda k: ' aria-current="page"' if k == active else ""
    if role == "specialist":
        nav = (f'<nav class="nav" aria-label="Main">'
               f'<a href="calendar.html"{cur("calendar")}>{ICON["cal"]}Calendar</a>'
               f'<a href="funds.html"{cur("funds")}>{ICON["fund"]}Funds</a>'
               f'<a href="frameworks.html"{cur("frameworks")}>{ICON["book"]}Filing rules<span class="chip you" style="margin-left:auto">Your turn</span></a></nav>')
        wait = ""
        who = '<span class="avatar" aria-hidden="true">CS</span><div><div class="n">Compliance specialist</div><div class="r">Demo with mock data</div></div>'
    else:
        nav = (f'<nav class="nav" aria-label="Main"><a href="gp-calendar.html" aria-current="page">{ICON["cal"]}Calendar</a></nav>')
        wait = ""
        who = '<span class="avatar" aria-hidden="true">GP</span><div><div class="n">General Partner / Fund Manager</div><div class="r">Bramblegate Partners · view only · demo with mock data</div></div>'
    switch = ""
    return f"""<!doctype html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · ACME Compliance calendar (demo)</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500&family=Inter:wght@400;500;600&family=DM+Mono&display=swap">
<link rel="stylesheet" href="app.css?v=__V__">
{f"<style>{style}</style>" if style else ""}
</head>
<body>
<div class="shell">
  <aside class="side">
    <a class="brand" href="index.html" aria-label="ACME, all mock-ups"><b>acme</b><i></i></a>
    <div class="product">Compliance calendar</div>
    <div class="fund"><div class="k">Fund</div><div class="v">{fund or FUND}</div><div class="m">{fund_note}</div>{switch}</div>
    {nav}
    {wait}
    <div class="side-foot">
      <div class="who">{who}</div>
      <form method="post" action="sign-in.html"><button class="ghost sm" type="submit">Sign out</button></form>
    </div>
  </aside>
  <main class="main" id="main">
{body}
  </main>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------- calendar data (the 22 entries)
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
PERIODS = ["December 2026"] + [f"{m} 2027" for m in ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November"]]

OBL = {
    "u11": dict(name="Monthly financial report U1.1", to="CSSF", who="Fund administrator", freq="Monthly",
                src="SRC-CSSF15627-P2", quote="no later than 10 calendar days after the end of each month",
                why="The fund is subject to Part II of the Law of 17 December 2010."),
    "tax": dict(name="Subscription tax return and payment", to="AED", who="Fund administrator", freq="Quarterly",
                src="SRC-UCILAW-P2", quote="within 20 calendar days following the end of each calendar quarter",
                why="The fund is established in Luxembourg."),
    "annual": dict(name="Audited annual report", to="CSSF", who="Fund administrator", freq="Annually",
                   src="SRC-UCILAW-P3", quote="within six months of the end of the period to which it relates",
                   why="The fund is subject to Part II of the Law of 17 December 2010."),
    "a01": dict(name="Statistical report A01 (Spain)", to="CNMV", who="Local reporting agent (Spain)", freq="Quarterly",
                src="SRC-CNMV-P1", quote="within two months after the last calendar day of the quarter",
                why="This filing may not be required. The report is only due if the fund is registered with the CNMV in Spain, and nobody has confirmed that. It stays on the calendar until someone does."),
    "rbe": dict(name="Beneficial-owner information update", to="Luxembourg Business Registers", who="AIFM", freq="On occurrence",
                src="SRC-RBELAW-P1", quote="within one month of becoming aware of the event that made the change necessary",
                why="The fund is a registered entity. It became aware of a change in its beneficial owners on Sun 31 Jan 2027."),
}
# (obligation, due date, mark, period text, moved-from day)
E = []
for i, (d, frm) in enumerate([(11, 10), (10, 0), (10, 0), (12, 10), (10, 0), (10, 0), (12, 10), (10, 0), (10, 0), (11, 10), (10, 0), (10, 0)]):
    E.append(("u11", date(2027, i + 1, d), "moved" if frm else "", f"For {PERIODS[i]}", frm))
for m, p in [(1, "October to December 2026"), (4, "January to March 2027"), (7, "April to June 2027"), (10, "July to September 2027")]:
    E.append(("tax", date(2027, m, 20), "", f"For {p}", 0))
E.append(("annual", date(2027, 6, 30), "", "For the year to 31 December 2026", 0))
for (m, d, frm), p in zip([(2, 26, 28), (5, 31, 0), (8, 31, 0), (11, 30, 0)], ["October to December 2026", "January to March 2027", "April to June 2027", "July to September 2027"]):
    E.append(("a01", date(2027, m, d), "prec", f"For {p}", frm))
E.append(("rbe", date(2027, 2, 26), "moved", "After a change on 20 January 2027", 28))
assert len(E) == 22
E.sort(key=lambda e: (e[1], e[0]))
fmt = lambda d: f"{DOW[d.weekday()]} {d.day} {MONTHS[d.month - 1]} {d.year}"


def yeargrid(specialist):
    """Obligations down the side, months across: every dated entry is one small tile."""
    rows = ["u11", "tax", "annual", "a01", "rbe"]
    h = ['<div class="rowh mh" style="justify-content:flex-end"><span class="muted small">What is filed · who files it</span></div>']
    h += [f'<div class="mh{" now" if i == 0 else ""}">{m}</div>' for i, m in enumerate(MONTHS)]
    for r, key in enumerate(rows):
        last = " last" if r == len(rows) - 1 else ""
        o = OBL[key]
        # The OQ-7 open-question mark is specialist-only (SAD CR-027, H-031): the same chip as on G1
        # and the specialist calendar, once in the row label because a tile is too small for a chip.
        oq7 = specialist and key == "tax"
        oq7_chip = f'<div class="tags" style="margin-top:6px">{chip("Depends on open question OQ-7", "plain")}</div>' if oq7 else ""
        h.append(f'<div class="rowh{last}"><b>{o["name"]}</b><span>{o["who"]} → {o["to"]}</span>{oq7_chip}</div>')
        for m in range(1, 13):
            cell = ""
            for k, d, mark, _, frm in E:
                if k == key and d.month == m:
                    # Moved marks are specialist-only (CR-012): the GP's tile shows no "moved" colour.
                    cls = "" if (mark == "moved" and not specialist) else mark
                    # Each OBL-02 tile also carries the mark itself, for screen readers and on hover.
                    oq7_note = " · Depends on open question OQ-7" if oq7 else ""
                    oq7_sr = '<span class="sr">Depends on open question OQ-7</span>' if oq7 else ""
                    cell = (f'<span class="day {cls}" title="{fmt(d)}{oq7_note}"><small>{DOW[d.weekday()]}</small>'
                            f'<b class="num">{d.day}</b>{oq7_sr}</span>')
            h.append(f'<div class="{last.strip()}">{cell}</div>')
    moved_key = '<span><i class="moved"></i>Moved off a weekend</span>' if specialist else ""  # specialist-only
    legend = ('<div class="legend"><span><i></i>Due on the calculated date</span>'
              + moved_key +
              '<span><i class="prec"></i>May not be required</span>' + "</div>")
    return f'<div class="yeargrid">{"".join(h)}</div>{legend}'


def entry_marks(key, d, mark, frm, specialist):
    marks = []
    if frm and specialist:  # the "Moved from" chip is specialist-only (CR-012)
        marks.append(chip(f"Moved from {DOW[date(d.year, d.month, frm).weekday()]} {frm} {MONTHS[d.month - 1]}", "agent"))
    if mark == "prec":
        marks.append(chip("May not be required", "you"))
    if specialist and key == "tax":
        marks.append(chip("Depends on open question OQ-7", "plain"))
    return "".join(marks)


def entries_table(specialist, limit=9):
    out = []
    for n, (key, d, mark, period, frm) in enumerate(E[:limit]):
        o = OBL[key]
        opened = n == 3
        nd = ' class="next-date"' if n == 0 else ""
        link = f'<a class="more" href="#entries">{"Hide" if opened else "Why"}</a>'
        out.append(f'<tr id="r-{n}" class="{"open" if opened else ""}"><td><b class="num"><span{nd}>{fmt(d)}</span></b></td>'
                   f'<td><span class="t">{o["name"]}</span><span class="m">{period}</span></td>'
                   f'<td>{o["to"]}</td><td>{o["who"]}</td><td><div class="tags">{entry_marks(key, d, mark, frm, specialist)}</div></td>'
                   f'<td>{link}</td></tr>')
        if opened:
            out.append(f'<tr class="open"><td></td><td colspan="5"><div class="why"><div><h3>Why this fund must file it</h3><p>{o["why"]}</p></div>'
                       f'<div><h3>Where the deadline comes from</h3><p><span class="id">{o["src"]}</span><br>“{o["quote"]}”</p></div></div></td></tr>')
    return ('<table><thead><tr><th scope="col">Due</th><th scope="col">What</th><th scope="col">Sent to</th>'
            '<th scope="col">Who files</th><th scope="col">Notes</th><th scope="col"><span class="sr">More</span></th></tr></thead>'
            f'<tbody>{"".join(out)}</tbody></table>')


# ---------------------------------------------------------------- small charts (adapted from the case-study mock-up)
def dotchart(mode="specialist"):
    """One dot per filing, stacked by month. Dots appear one after another when the page loads."""
    out, n = ['<line x1="6" y1="98" x2="366" y2="98" stroke="#e4e4e4"/>'], 0
    for m in range(1, 13):
        x = 21 + (m - 1) * 30
        for level, (key, d, mark, period, frm) in enumerate([e for e in E if e[1].month == m]):
            o = OBL[key]
            note, look = "", 'fill="var(--brass)"'
            if frm and mode == "specialist":  # the GP's chart shows no moved dots (CR-012, DL-49)
                note, look = " · moved off a weekend", 'fill="var(--orange)"'
            elif mark == "prec":
                note, look = " · may not be required", 'fill="#fff" stroke="var(--brass)" stroke-width="1.6"'
            out.append(f'<circle class="dot" cx="{x}" cy="{84 - level * 22}" r="7" {look} style="animation-delay:{n * 40}ms"><title>{o["name"]} · due {fmt(d)}{note}</title></circle>')
            n += 1
        out.append(f'<text x="{x}" y="117" text-anchor="middle" font-size="10.5" fill="#4d4d4d">{MONTHS[m - 1][0]}</text>')
    moved_key = '<span><i class="k2"></i>Moved off a weekend</span>' if mode == "specialist" else ""
    legend = '<span><i class="k1"></i>Due date</span>' + moved_key + '<span><i class="k3"></i>May not be required</span>'
    # Spoken description: count the dots the same way they are coloured above, so screen-reader
    # users get the same information as the key (moved dots are counted for the specialist only).
    n_moved = sum(1 for e in E if e[4] and mode == "specialist")
    n_prec = sum(1 for e in E if e[2] == "prec" and not (e[4] and mode == "specialist"))
    label = f"{len(E)} filing dates across 2027, one to three in each month"
    if n_moved:
        label += f"; {n_moved} moved off a weekend"
    label += f"; {n_prec} may not be required (hollow dots)"
    return (f'<svg class="dots" viewBox="0 0 372 124" role="img" aria-label="{label}">{"".join(out)}</svg>'
            f'<div class="dots-key">{legend}</div>')


def ring(done, total, size=56):
    """A ring that fills to done/total when the page loads."""
    c = 2 * 3.14159 * 22
    return (f'<svg class="ring" viewBox="0 0 56 56" width="{size}" height="{size}" aria-hidden="true"><circle cx="28" cy="28" r="22" fill="none" stroke="var(--panel)" stroke-width="6"/>'
            f'<circle class="ring-arc" cx="28" cy="28" r="22" fill="none" stroke="var(--brass)" stroke-width="6" stroke-linecap="round" transform="rotate(-90 28 28)" '
            f'stroke-dasharray="{c:.1f}" style="--c:{c:.1f};stroke-dashoffset:{c * (1 - done / total):.1f}"/></svg>')


def bars(a_label, a_val, a_pct, b_label, b_val, b_pct):
    """Two bars that grow to show how far apart two sources are."""
    row = lambda cls, lbl, val, pct: f'<div class="bar {cls}"><span class="lbl">{lbl}</span><span class="track"><i style="--w:{pct}%"></i></span><b>{val}</b></div>'
    return f'<div class="bars">{row("law", a_label, a_val, a_pct)}{row("guide", b_label, b_val, b_pct)}</div>'


FACTS = """<div class="facts">
      <div><div class="k">Framework</div><div class="v">Luxembourg UCI Part II</div></div>
      <div><div class="k">Year end</div><div class="v">31 December</div></div>
      <div><div class="k">Domicile</div><div class="v">Luxembourg</div></div>
      <div><div class="k">Marketed in</div><div class="v">Luxembourg, Germany, Spain</div></div>
    </div>"""
# U11 (operator decision, 2026-11-14): the GP keeps the short grey style, but the line must carry all
# three FR-020 points: approved reading, not legal advice, date counting not yet checked.
GP_LEGAL = ('<p class="small muted" style="margin-top:18px">These dates are the specialist\'s approved reading of the rules. '
            'Not legal advice. Date counting hasn\'t yet been checked against the legal texts.</p>')
LEGAL = '<p class="note" style="margin-top:20px">This calendar is not legal advice. Before anyone relies on these dates: the way deadlines are counted (for example, the day “six months after year end” falls on) has not yet been checked against the legal texts.</p>'


SHORT = {"u11": "U1.1", "tax": "Sub. tax", "annual": "Annual", "a01": "A01", "rbe": "Owners"}


def month_view(specialist=True):
    """January 2027 with the chosen day explained beside it. Shared by both roles;
    the "Why this date" (moved) line is specialist-only (CR-012)."""
    jan = [(n, e) for n, e in enumerate(E) if e[1].month == 1]
    cells = "".join(f'<div class="dow">{d}</div>' for d in DOW)
    cells += "".join(f'<div class="cell out">{d}</div>' for d in (28, 29, 30, 31))  # 1 Jan 2027 is a Friday
    for day in range(1, 32):
        todays = [(n, e) for n, e in jan if e[1].day == day]
        if todays:
            n, (key, d, mark, period, frm) = todays[0]
            cells += (f'<a class="cell{" sel-default" if n == 0 else ""}" id="g-{n}" href="#d{day}"><span class="d{" next" if n == 0 else ""}">{day}</span>'
                      f'<span class="e"><span class="long">{OBL[key]["name"]}</span><span class="short">{SHORT[key]}</span><small>{OBL[key]["who"]}</small></span></a>')
        else:
            cells += f'<div class="cell">{day}</div>'
    panels = ""
    for n, (key, d, mark, period, frm) in jan:
        o = OBL[key]
        moved = '<div><dt>Why this date</dt><dd>The deadline fell on Sunday 10 January, so it moves to the next working day.</dd></div>' if (frm and specialist) else ""
        panels += f"""<div class="dayp{" default" if n == 0 else ""}" id="d{d.day}">
            <div class="id">{fmt(d)}{" · due next" if n == 0 else ""}</div><h3>{o["name"]}</h3><p class="small muted">{period}</p>
            <dl><div><dt>Who files it</dt><dd>{o["who"]}, with the {o["to"]}.</dd></div>{moved}
            <div><dt>Why the fund must file it</dt><dd>{o["why"]}</dd></div>
            <div><dt>Where the deadline comes from</dt><dd>“{o["quote"]}”<br><span class="id">{o["src"]}</span></dd></div></dl></div>"""
    return (f'<div class="monthbar"><h3>January 2027</h3><span class="muted small">Select a day to see what is due and why</span>'
            f'<a class="more" href="#entries" style="margin-left:auto">February</a></div>'
            f'<div class="cal-two"><div class="month">{cells}</div><div class="detail">{panels}</div></div>')


def calendar_page(specialist):
    """One calendar for both roles: the same summary and the same Month / Year / List switch.
    The only differences are the header line, and a few marks that only the specialist sees."""
    if specialist:
        lead = f"Everything {FUND} must file in 2027, with the date and who files it."
        trust = "You published this on Fri 13 Nov 2026. The GP sees the same dates."
        actions = '<div class="actions"><a class="ghost" href="frameworks.html">See the rules behind it</a></div>'
        who_note = "Across 5 obligations and 3 filing parties"
    else:
        lead = f"What {FUND} must file in 2027, when, and who files it for you."
        trust = "Published by the compliance specialist · Fri 13 Nov 2026"
        actions = ""
        who_note = "Your service providers file all of them"
    return f"""
    <header class="head">
      <div><h1>Compliance calendar</h1><p>{lead}</p>
      <div class="trust">{ICON["check"]}{trust}</div></div>
      {actions}
    </header>
    {FACTS}
    {LEGAL if specialist else GP_LEGAL}
    <div class="kpis{"" if specialist else " three"}" aria-label="Summary">
      {kpi("Due next", "Mon 11 Jan", "Monthly financial report U1.1, filed by the fund administrator", "next", "dark", text=True, href="#d11")}
      <div class="kpi"><div class="k">Filings in 2027: 22</div>{dotchart("specialist" if specialist else "public")}</div>
      {kpi("Moved off a weekend", "6", "4 to the Monday after, 2 to the Friday before", "move") if specialist else ""}
      {kpi("May not be required", "4", "Spain report A01. Nobody has confirmed the fund must file it.", "care", "you")}
    </div>

    <section class="section switch" id="entries" aria-labelledby="cal-h">
      <div class="sec-h"><div><h2 class="sq" id="cal-h">Filings in 2027</h2><div class="sub">{who_note}</div></div>
        <div class="tabs" role="radiogroup" aria-label="Show filings as">
          <label><input class="sr" type="radio" name="view" id="v-month" checked>Month</label>
          <label><input class="sr" type="radio" name="view" id="v-year">Year</label>
          <label><input class="sr" type="radio" name="view" id="v-list">List</label></div></div>
      <div class="view month card">{month_view(specialist)}</div>
      <div class="view year card scroll">{yeargrid(specialist)}</div>
      <div class="view list card">
        <form class="filters" method="get" action="#entries">
          <div class="field"><label for="f-who">Who files</label><select id="f-who" name="who"><option>Everyone</option><option>Fund administrator</option><option>AIFM</option><option>Local reporting agent (Spain)</option></select></div>
          <div class="field"><label for="f-to">Sent to</label><select id="f-to" name="to"><option>All authorities</option><option>CSSF</option><option>AED</option><option>CNMV</option><option>Luxembourg Business Registers</option></select></div>
          <div class="field"><label for="f-when">When</label><select id="f-when" name="when"><option>Next 3 months (9)</option><option>All of 2027 (22)</option><option>May not be required (4)</option></select></div>
          <button class="ghost sm" type="submit">Apply</button>
        </form>
        {entries_table(specialist)}
      </div>
    </section>"""


def gp_empty():
    return f"""
    <header class="head"><div><h1>Compliance calendar</h1><p>What {FUND} must file, when, and who files it for you.</p></div></header>
    <section class="section"><div class="card empty"><h2>No calendar has been published yet</h2>
      <p>You'll see deadlines here once compliance has signed them off.</p></div></section>"""


# ---------------------------------------------------------------- run pages
def run_head(title, lead, step, refline=""):
    states = [("AI drafts the rules", "", False), ("You check the rules", "Gate 1", True),
              ("You confirm what applies", "Gate 2", True), ("You publish the calendar", "Gate 3", True)]
    pages = ["run-status.html", "review-rules.html", "applicability.html", "publish.html"]
    lis = []
    for i, (t, gate_name, gate) in enumerate(states):
        if i < step:
            cls, word, cur = "done", "Done", ""
        elif i == step:
            cls, word, cur = "", ("In progress" if i == 0 else "Your turn"), ' aria-current="step"'
        else:
            cls, word, cur = "", "Not started", ""
        label = f"Step {i + 1}"
        lis.append(f'<li class="{cls}"{cur}><div class="n">{label}</div><div class="t">{t}</div><div class="s">{word}</div></li>')
    return f"""
    <div class="crumb"><a href="frameworks.html">Filing rules</a><span>›</span><span>Luxembourg UCI Part II</span><span>›</span><span>Review 4</span></div>
    <header class="head">
      <div><h1>{title}</h1><p>{lead}</p></div>
    </header>
    {refline}
    <ol class="steps" aria-label="Where this review is">{"".join(lis)}</ol>"""


def evidence(src, para, draft, verified="Quote found in the source", kind="done", is_open=False, badge=""):
    # badge: ready-made chip HTML that replaces the single "verified" chip (used by rule 7, the demo row).
    rows = "".join(f'<dt>{k}</dt><dd class="{"gap" if kind_ == "gap" else ""}">{f"<span class=match>{v}</span>" if kind_ == "match" else v}</dd>' for k, v, kind_ in draft)
    return (f'<details class="src"{" open" if is_open else ""}><summary>{badge or chip(verified, kind)}<span class="linkbtn"></span></summary>'
            f'<div class="evidence"><div><h3>The source says</h3><span class="id">{src}</span><p class="para">{para}</p></div>'
            f'<div><h3>The AI\'s reading</h3><dl class="draft">{rows}</dl></div></div></details>')


def opts(name, values, big=False, required=False):
    req = " required" if required else ""
    return '<div class="opts">' + "".join(f'<label class="opt{" big" if big else ""}"><input type="radio" name="{name}" value="{v}"{req}>{v}</label>' for v in values) + "</div>"


PARTIES = ["AIFM", "Fund administrator", "Auditor", "Local reporting agent (Spain)", "Tax advisor", "Not known"]


def design_note(text):
    """An annotation for reviewers of the mock-up, NOT product copy. Styled apart (.design-note in app.css)."""
    return f'<aside class="design-note" aria-label="Design note"><span>Design note</span>{text}</aside>'


def decide_rule(n, flagged, who_needed, message="", bd_note=""):
    """A9 REVERSED (operator decision, 2026-11-14, after reviewing the two-form layout): answer first.
    One form; the specialist picks Approve or Reject, and only that answer's fields appear (CSS :has(),
    with a fallback in app.css that shows both sets where :has() is unsupported).
    Still no browser "required": if a field is missing, the SERVER refuses on the page
    (BUSINESS_DAY_RULE_REQUIRED, REASON_REQUIRED). Nothing is pre-selected."""
    who = f'<fieldset><legend>Who files this? The source doesn\'t say.</legend>{opts(f"who{n}", PARTIES)}</fieldset>' if who_needed else ""
    reason = (f'<div class="field"><label for="ra{n}">Why are you approving it although the checker flagged it?</label><textarea id="ra{n}" name="reason"></textarea>'
              '<span class="hint">Saved in the audit log with your name and the time.</span></div>') if flagged else ""
    # A7 (operator decision, 2026-11-14): on the demo row, Approve is always clickable and the SERVER
    # refuses it on the page, never a browser pop-up. So this one button:
    #   formmethod="get" a static mock-up can't receive a POST, so we reload the page instead
    #   formaction="#blocked"  lands on the refusal, which app.css reveals with #blocked:target
    refuse = ' formaction="#blocked" formmethod="get"' if message else ""
    return f"""<form class="decision" method="post" action="#row-{n}">{message}
          <fieldset><legend>What's your decision on this rule?</legend>
            <div class="opts"><label class="opt big"><input type="radio" name="d{n}" value="yes">Approve</label>
            <label class="opt big"><input type="radio" name="d{n}" value="no">Reject</label></div></fieldset>
          <div class="if yes">
            <fieldset><legend>If the deadline falls on a weekend or holiday (choose one to approve)</legend>{opts(f"bd{n}", ["Move to the following working day", "Move to the preceding working day", "Keep the date"])}</fieldset>
            {bd_note}{who}{reason}
            <div><button class="btn" type="submit"{refuse}>Approve rule</button></div></div>
          <div class="if no">
            <div class="field"><label for="rr{n}">Why are you rejecting it?</label><textarea id="rr{n}" name="reason"></textarea>
            <span class="hint">If you reject it, no filing dates are created from this rule.</span></div>
            <div><button class="btn" type="submit">Reject rule</button></div></div>
        </form>"""


def review_rules():
    index = [(1, "Monthly financial report U1.1", chip("Approved", "done")), (2, "Subscription tax return", chip("Approved", "done")),
             (3, "Audited annual report", chip("Sources disagree", "you")), (4, "Statistical report A01 (Spain)", chip("To decide")),
             (5, "Beneficial-owner update", chip("Sources disagree", "you")), (6, "Annual VAT return", chip("To decide")),
             (7, "IT security attestation", chip("To decide", "todo") + chip("Approval blocked", "you blocked"))]
    rail = "".join(f'<a href="#row-{n}"{" class=\"cur\"" if n == 3 else ""}><span>{n}. {t}</span><span>{c}</span></a>' for n, t, c in index)

    def settled(n, name, line, extra=""):
        return (f'<article class="rule-card" id="row-{n}"><header><div><div class="n">Rule {n} of 7</div><h2 class="sq">{name}</h2></div>'
                f'<div class="tags">{chip("Approved", "done")}{extra}</div></header><div class="decided"><span>{line}</span></div></article>')

    row3 = f"""<article class="rule-card gate" id="row-3"><header><div><div class="n">Rule 3 of 7</div><h2 class="sq you">Audited annual report</h2>
          <div class="sub">Sent to the CSSF · due 6 months after the financial year ends · the source doesn't say who files it</div></div></header>
        {evidence("SRC-UCILAW-P3 · the law itself", 'An undertaking for collective investment subject to Part II of this law shall publish an audited annual report and file it with the CSSF <mark tabindex="0">within six months of the end of the period to which it relates</mark>.',
                  [("How often", "Once a year", ""), ("Counted from", "The financial year end", "match"), ("Due", "6 months later", "match"), ("Sent to", "CSSF", ""),
                   ("Who files", "The source doesn't say. You choose below.", "gap"), ("Applies if", "The fund is subject to Part II of the Law of 17 December 2010", "")],
                  verified="Two sources disagree", kind="you", is_open=True)}
        <!-- A5 is post-MVP (DL-22): the specialist can't pick a source. The two quotes are shown read-only;
             the rule follows the law, and the specialist approves with a reason or rejects with a reason. -->
        <div class="resolve"><h3 class="resolve-h">Flagged by the AI checker</h3>
          <p>The checker points out disagreements but never settles them. This rule follows the law. Approve it with a reason despite the flag, or reject it with a reason.</p>
          <div class="picks">
            <div class="pick static"><span><b>6 months, from the law itself</b><span class="id">SRC-UCILAW-P3 · the rule follows this</span>
              <q>within six months of the end of the period</q>{bars("Deadline after year end", "6 mo", 100, "", "", 0).replace('<div class="bar guide">', '<div class="bar guide" hidden>')}</span></div>
            <div class="pick static"><span><b>4 months, from a practice guide</b><span class="id">SRC-PRACT-P1 · someone's summary of the law</span>
              <q>within four months of financial year-end</q>{bars("", "", 0, "Deadline after year end", "4 mo", 66.6).replace('<div class="bar law">', '<div class="bar law" hidden>')}</span></div>
          </div></div>
        {decide_rule(3, True, True, bd_note=design_note("Real app: approving without an option shows the <code>BUSINESS_DAY_RULE_REQUIRED</code> refusal on the page."))}</article>"""

    def closed(n, name, sub, tag):
        return (f'<details class="rule-card gate" id="row-{n}"><summary><div><div class="n">Rule {n} of 7 · {sub}</div><h2>{name}</h2></div>'
                f'<div class="tags">{tag}<span class="more">Review</span></div></summary></details>')

    caught = f"""<div class="caught" id="blocked" role="alert"><b>Approval blocked: no legal basis.</b>
            This rule doesn't appear in the regulation text. Reject it with a reason.
            <div class="log">{ICON["check"]}<i>Recorded in the audit trail.</i></div></div>"""
    row7 = f"""<article class="rule-card gate" id="row-7"><header><div><div class="n">Rule 7 of 7</div><h2 class="sq you">Quarterly IT security attestation</h2>
          <div class="sub">Sent to the CSSF every quarter</div></div><div class="tags">{chip("To decide")}</div></header>
        {evidence("SRC-CSSF15627-P3 · CSSF Circular 15/627", 'The report shall be transmitted <mark tabindex="0">through the CSSF\'s secure electronic reporting channel</mark>. The fund administrator may transmit the report on behalf of the undertaking.',
                  [("How often", "Every quarter", ""), ("Counted from", "The quarter end", ""), ("Due", "30 calendar days later", ""), ("Sent to", "CSSF", "match"),
                   ("Who files", "Fund administrator", ""), ("Applies if", "The fund reports through the secure channel", "match")], is_open=True,
                  # A4 (operator decision, 2026-11-14): no "Quote found in the source" on the demo row. The chip reads
                  # "Approval blocked", matching the refusal, and swaps in with it (app.css: .chip.todo / .chip.blocked).
                  badge=chip("To decide", "todo") + chip("Approval blocked", "you blocked"))}
        {decide_rule(7, False, False, caught)}</article>"""

    refline = f'<div class="refline">{chip("1 action was refused", "you")}<span>Your approval of rule 7 was blocked: no legal basis.</span><a href="#row-7">Go to rule 7</a></div>'
    return run_head("Check the rules", "AI drafted 7 rules from the sources. Check each one against the words it came from, then approve or reject it. Nothing reaches the calendar until you approve it.", 1, refline) + f"""
    <div class="layout-rail">
      <nav class="rail" aria-label="Rules"><div class="ring-row left">{ring(2, 7, 48)}<div><b>5 of 7 left</b>You've approved 2</div></div>{rail}</nav>
      <div class="stack">
        {settled(1, "Monthly financial report U1.1", "You approved this at 14:06. A weekend deadline moves to the following working day. The <b>fund administrator</b> files it, as the source says.")}
        {settled(2, "Subscription tax return and payment", "You approved this at 14:09. The date stays put on a weekend. You chose the <b>fund administrator</b> to file it.", chip("Depends on open question OQ-7", "plain"))}
        {row3}
        {closed(4, "Statistical report A01 (Spain)", "Sent to the CNMV every quarter", chip("To decide"))}
        {closed(5, "Beneficial-owner information update", "Sent to the Luxembourg Business Registers when owners change", chip("Sources disagree", "you"))}
        {closed(6, "Annual VAT return", "Sent to the AED once a year", chip("To decide"))}
        {row7}
        <details class="rule-card"><summary><div><div class="n">Check nothing was missed</div><h2>7 paragraphs that no rule uses</h2></div><div class="tags"><span class="more">Show</span></div></summary>
          <table><tbody><tr><td><span class="id">SRC-CSSF15627-P1</span></td><td>Says who the circular covers</td></tr><tr><td><span class="id">SRC-CSSF15627-P3</span></td><td>Says how to send the report and who may send it</td></tr>
          <tr><td><span class="id">SRC-UCILAW-P1</span></td><td>Defines “financial year-end”</td></tr><tr><td><span class="id">SRC-CNMV-P2</span></td><td>Says who may submit report A01</td></tr>
          <tr><td><span class="id">SRC-PRACT-P1 to P3</span></td><td>The practitioner guide. AI checks against it but never drafts rules from it.</td></tr></tbody></table></details>
        <section class="card pad" id="finish"><h2 class="sq you">5 rules left to decide</h2>
          <p style="margin:10px 0 16px;max-width:64ch">Decide every rule to move on. AI then works out which rules apply to the fund.</p>
          <form method="post" action="applicability.html"><button class="btn" type="submit">Finish checking</button></form></section>
      </div>
    </div>"""


def applicability():
    def compact(n, name, text, fact, answer="applies", kind="agent"):
        return (f'<article class="rule-card" id="verdict-{n}"><header><div><div class="n">Rule {n} of 6</div><h2 class="sq">{name}</h2></div>'
                f'<div class="tags">{chip("AI: " + answer, kind)}{chip("You confirmed", "done")}</div></header>'
                f'<div class="decided"><span>{text} <span class="id">{fact}</span></span></div></article>')

    unsure = f"""<article class="rule-card gate" id="verdict-4"><header><div><div class="n">Rule 4 of 6</div><h2 class="sq you">Statistical report A01 (Spain)</h2>
          <div class="sub">Sent to the CNMV every quarter. That's four filings in 2027 if it applies.</div></div>
          <div class="tags">{chip("AI: can't tell", "you")}</div></header>
        <div class="evidence"><div><h3>The rule applies if</h3><span class="id">SRC-CNMV-P1</span>
            <p class="para">Foreign undertakings for collective investment <mark tabindex="0">registered with the CNMV for marketing in Spain</mark> shall submit statistical report A01 to the CNMV each quarter.</p>
            <h3 style="margin-top:20px">Why the AI couldn't decide</h3>
            <p>The rule depends on CNMV registration. The fund is marketed in Spain, but the fund records don't say whether it is registered. Being marketed there is not the same as being registered.</p></div>
          <div><h3>The fund's facts</h3>
            <div class="factcards" style="grid-template-columns:1fr">
              <div class="factcard"><span class="id">FACT-03</span><div class="small">Countries where marketed</div><div class="v">Luxembourg, Germany, Spain</div></div>
              <div class="factcard gap"><span class="id">FACT-04</span><div class="small"><span class="match">Registered with the CNMV for marketing in Spain</span></div><div class="v">Unknown. Not confirmed in the fund records.</div></div>
            </div></div></div>
        <!-- A9 reversed (operator decision, 2026-11-14): answer first, then only that answer's fields. -->
        <form class="decision" method="post" action="#verdict-4">
          <fieldset><legend>Nobody has confirmed the fund's registration in Spain. Should this rule go on the calendar?</legend>
            <div class="opts"><label class="opt big"><input type="radio" name="v4" value="yes">Yes, add it until someone confirms</label>
            <label class="opt big"><input type="radio" name="v4" value="no">No, leave it off</label></div></fieldset>
          <div class="if yes"><p class="lead">Choose this if you can't confirm the registration. Four filings are added to the calendar, each marked “May not be required”. Filing a report that wasn't needed costs little. Missing one that was needed is a breach.</p>
            <div class="field"><label for="p4">Why are you adding it?</label><textarea id="p4" name="reason"></textarea><span class="hint">The GP will read this as the reason for the four filings.</span></div>
            <div><button class="btn" type="submit">Add to the calendar</button></div></div>
          <div class="if no"><p class="lead">Choose this only if you know the fund is not registered with the CNMV. No filings are added for this rule.</p>
            <div class="field"><label for="n4">How do you know it doesn't apply?</label><textarea id="n4" name="reason"></textarea><span class="hint">Saved in the audit log. The GP won't see it.</span></div>
            <div><button class="btn" type="submit">Leave it off</button></div></div>
        </form></article>"""

    return run_head("Confirm what applies", "AI checked the 6 rules you approved against the fund's facts. Confirm each answer or overrule it.", 2) + f"""
    <div class="layout-rail">
      <nav class="rail" aria-label="Rules"><div class="ring-row left">{ring(4, 6, 48)}<div><b>2 of 6 left</b>You've confirmed 4</div></div>
        <a href="#verdict-1"><span>1. Monthly financial report</span><span>{chip("You confirmed", "done")}</span></a>
        <a href="#verdict-2"><span>2. Subscription tax return</span><span>{chip("You confirmed", "done")}</span></a>
        <a href="#verdict-3"><span>3. Audited annual report</span><span>{chip("You confirmed", "done")}</span></a>
        <a href="#verdict-4" class="cur"><span>4. Statistical report A01 (Spain)</span><span>{chip("AI: can't tell", "you")}</span></a>
        <a href="#verdict-5"><span>5. Beneficial-owner update</span><span>{chip("To decide")}</span></a>
        <a href="#verdict-6"><span>6. Annual VAT return</span><span>{chip("You confirmed", "done")}</span></a></nav>
      <div class="stack">
      {compact(1, "Monthly financial report U1.1", "Applies. The fund is subject to Part II.", "FACT-01")}
      {compact(2, "Subscription tax return and payment", "Applies. The fund is established in Luxembourg.", "FACT-02")}
      {compact(3, "Audited annual report", "Applies. The fund is subject to Part II.", "FACT-01")}
      {unsure}
      <details class="rule-card gate" id="verdict-5"><summary><div><div class="n">Rule 5 of 6 · Sent to the Luxembourg Business Registers</div><h2>Beneficial-owner information update</h2></div>
        <div class="tags">{chip("AI: applies", "agent")}<span class="more">Review</span></div></summary></details>
      {compact(6, "Annual VAT return", "Doesn't apply. The fund is not registered for VAT in Luxembourg, so no filings are added.", "FACT-05", "doesn't apply", "")}
      <section class="card pad"><h2 class="sq you">2 answers left to confirm</h2>
        <p style="margin:10px 0 16px;max-width:64ch">Once you've confirmed them all, the dates are calculated by code. No AI works out a date.</p>
        <form method="post" action="publish.html"><button class="btn" type="submit">Finish and calculate dates</button></form></section>
      </div>
    </div>"""


def publish():
    return run_head("Check the calendar and publish", "These 22 dates were calculated from the rules you approved. Check them, read what was left out, then publish for the GP.", 3) + f"""
    <p class="note" style="margin-top:16px">Before anyone relies on these dates: the way deadlines are counted (for example, the day “six months after year end” falls on) has not yet been checked against the legal texts.</p>
    <div class="kpis" aria-label="Summary">
      {kpi("Filings", "22", "From the 5 rules that apply to the fund", "cal", "dark")}
      {kpi("Moved off a weekend", "6", "4 to the Monday after, 2 to the Friday before", "move")}
      {kpi("May not be required", "4", "Statistical report A01 (Spain)", "care", "you")}
      {kpi("Left out", "1 rule", "Plus 7 paragraphs that no rule uses", "doc", text=True)}
    </div>
    <section class="section" aria-labelledby="year-h">
      <div class="sec-h"><h2 class="sq agent" id="year-h">What the GP will see</h2></div>
      <div class="card scroll">{yeargrid(True)}</div>
    </section>
    <section class="section">
      <div class="card"><div class="card-h"><div><h2 class="sq you">What's not in this calendar</h2><p>Read both lists before you publish.</p></div></div>
        <table><thead><tr><th scope="col">Rule you rejected</th><th scope="col">Your reason</th></tr></thead>
          <tbody><tr><td><b>Quarterly IT security attestation</b><span class="m">SRC-CSSF15627-P3</span></td><td>The quote describes how to send a report. It sets no deadline and no duty.</td></tr></tbody></table>
        <table><thead><tr><th scope="col">Paragraph no rule uses</th><th scope="col">What it says</th></tr></thead>
          <tbody>
            <tr><td><span class="id">SRC-CSSF15627-P1</span></td><td>Who the circular covers</td></tr>
            <tr><td><span class="id">SRC-CSSF15627-P3</span></td><td>How to send the report and who may send it</td></tr>
            <tr><td><span class="id">SRC-UCILAW-P1</span></td><td>Defines “financial year-end”</td></tr>
            <tr><td><span class="id">SRC-CNMV-P2</span></td><td>Who may submit report A01</td></tr>
            <tr><td><span class="id">SRC-PRACT-P1 to P3</span></td><td>The practitioner guide (three summaries)</td></tr>
          </tbody></table>
      </div>
    </section>
    <section class="section"><div class="rule-card gate">
      <!-- A9 reversed (operator decision, 2026-11-14): answer first, then only that answer's fields.
           "Close without publishing" goes to Filing rules (the review closes), via formaction. -->
      <form class="decision" method="post" action="calendar.html" style="border-top:0">
        <fieldset><legend>Is this calendar ready for the GP?</legend>
          <div class="opts"><label class="opt big"><input type="radio" name="pub" value="yes">Yes, publish it</label>
          <label class="opt big"><input type="radio" name="pub" value="no">No, don't publish</label></div></fieldset>
        <div class="if yes">
          <p class="lead">The GP will see these 22 dates in place of the calendar published on Fri 13 Nov 2026.</p>
          <label class="ack"><input type="checkbox" name="ack"><span>I've read the rejected rule and the unused paragraphs above.</span></label>
          <div><button class="btn" type="submit">Publish calendar</button></div></div>
        <div class="if no">
          <p class="lead">Nothing changes for the GP. They keep the calendar published on Fri 13 Nov 2026, and this review closes.</p>
          <div class="field"><label for="dec">What needs to change before it can be published?</label><textarea id="dec" name="reason"></textarea>
          <span class="hint">Saved in the audit log with your name and the time.</span></div>
          <div><button class="btn" type="submit" formaction="frameworks.html">Close without publishing</button></div></div>
      </form></div>
    </section>"""


def run_status(done=False):
    def unit(t, m, state):
        if done and state != "done":
            state, m = "done", "The quote is in the source." + (" Another source gives a different deadline." if "Beneficial" in t else " No other source disagrees.")
        if state == "done":
            return f'<div class="unit"><div><div class="t">{t}</div><div class="small muted">{m}</div></div><span></span>{chip("Done", "done")}</div>'
        if state == "run":
            return f'<div class="unit now"><div><div class="t">{t}</div><div class="small muted">{m}</div></div><span></span>{chip("Checking now", "agent")}</div>'
        return f'<div class="unit"><div><div class="t">{t}</div></div><span></span>{chip("Up next")}</div>'

    docs = [("CSSF Circular 15/627", "3 paragraphs read, 1 rule drafted"), ("Law of 17 December 2010", "3 paragraphs read, 2 rules drafted"),
            ("CNMV statistical reporting", "2 paragraphs read, 1 rule drafted"), ("Law on the Register of Beneficial Owners", "1 paragraph read, 1 rule drafted"),
            ("Luxembourg VAT law", "1 paragraph read, 1 rule drafted")]
    checks = [("Monthly financial report U1.1", "The quote is in the source. No other source disagrees.", "done"), ("Subscription tax return and payment", "The quote is in the source. No other source disagrees.", "done"),
              ("Audited annual report", "The quote is in the source. Another source gives a different deadline.", "done"), ("Statistical report A01 (Spain)", "Being compared with the other sources", "run"),
              ("Beneficial-owner information update", "", "wait"), ("Annual VAT return", "", "wait"), ("Quarterly IT security attestation", "", "wait")]
    if done:
        head = run_head("The rules are ready for you to check", "AI drafted 7 rules and checked each one against the sources. Nothing reaches the calendar until you approve it.", 1)
        banner = """<section class="cta" aria-labelledby="cta-h">
      <div><div class="k">Your turn</div><h2 id="cta-h">7 rules to check</h2>
      <p>For 2 of them, the sources disagree about the deadline. You decide which stands.</p></div>
      <a class="btn" href="review-rules.html">Check the rules</a>
    </section>"""
    else:
        head = run_head("Nothing for you to do yet", "AI is drafting the rules and checking each one against the sources. You check the rules when it finishes.", 0)
        banner = """<section class="cta wait" aria-labelledby="cta-h">
      <div><div class="k">AI is working</div><h2 id="cta-h">3 of 7 rules checked</h2>
      <p>Started at 14:02. This usually takes under 5 minutes. A “Check the rules” button appears here as soon as it finishes.</p>
      <p class="small" style="margin-top:10px">This page updates by itself every few seconds. <a href="run-status.html?refresh=off">Stop updating</a></p></div>
    </section>
    <p class="proto">Prototype shortcut, not part of the product: <a href="run-status-done.html">show this page after the AI finishes</a></p>"""
    tally = chip("7 of 7 checked", "done") if done else chip("3 of 7 checked", "agent")
    return head + banner + f"""
    <section class="section" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start">
        <div class="card"><div class="card-h"><div><h2 class="sq agent">Drafting the rules</h2><p>The first AI reads each source and writes a rule, quoting the exact words it relied on.</p></div>{chip("5 of 5 sources read", "done")}</div>
          <div class="units">{"".join(unit(t, m, "done") for t, m in docs)}</div></div>
        <div class="card"><div class="card-h"><div><h2 class="sq agent">Checking the drafts</h2><p>A second, separate AI compares every draft with all the sources and tells you where they disagree. It never changes a rule.</p></div>{tally}</div>
          <div class="units">{"".join(unit(t, m, s) for t, m, s in checks)}</div></div>
    </section>"""


def frameworks():
    runs = [("Review 4", "Fri 13 Nov 2026, 14:02", chip("Your turn: 5 rules to check", "you"), "review-rules.html", "Continue"),
            ("Review 3", "Fri 13 Nov 2026, 10:15", chip("Published", "done"), "calendar.html", "See the calendar"),
            ("Review 2", "Thu 12 Nov 2026, 16:40", chip("You abandoned it"), "run-status.html", "See what happened"),
            ("Review 1", "Thu 12 Nov 2026, 11:05", chip("Failed while drafting", "no"), "run-status.html", "See what happened")]
    rows = "".join(f'<tr><td><b>{n}</b></td><td class="num">{d}</td><td>{st}</td><td><a class="more" href="{h}">{a}</a></td></tr>' for n, d, st, h, a in runs)
    srcs = [("SRC-CSSF15627", "CSSF Circular 15/627", "Primary", 3), ("SRC-UCILAW", "Law of 17 December 2010", "Primary", 3), ("SRC-CNMV", "CNMV statistical reporting for foreign UCIs", "Primary", 2),
            ("SRC-RBELAW", "Law of 13 January 2019 on the Register of Beneficial Owners", "Primary", 1), ("SRC-VATLAW", "Luxembourg VAT law", "Primary", 1),
            ("SRC-PRACT", "Practitioner guide to Luxembourg fund filings", "Secondary. AI checks against it but never drafts rules from it.", 3)]
    srows = "".join(f'<tr><td><span class="id">{i}</span></td><td><b>{t}</b></td><td>{k}</td><td class="num">{p}</td></tr>' for i, t, k, p in srcs)
    # A7 (operator decision, 2026-11-14): "Start a new review" stays visible while review 4 is open.
    # Clicking it is refused by the SERVER (RUN_ACTIVE): the reason appears beside the button and the
    # attempt is audited. Wording from ux.md §5 RUN_ACTIVE, with "run" → "review" (U2) and "gate" → "step" (U4).
    # Mock-up only: the form reloads this page at #start-refused, and app.css shows .caught:target.
    start_review = f"""<div class="foot-note"><b>Has a regulation changed?</b> Start a new review to check the rules again.
          <form method="get" action="#start-refused" style="margin-top:10px"><button class="btn sm" type="submit">Start a new review</button></form>
          <div class="caught" id="start-refused" role="alert" style="margin-top:12px"><b>Review 4 is still in progress, so a new review can't start.</b>
            Finish it, or abandon it at its step, first. <a href="review-rules.html">Open review 4</a>
            <div class="log">{ICON["check"]}<i>Recorded in the audit trail.</i></div></div></div>"""
    return f"""
    <header class="head">
      <div><div class="sub" style="margin:0 0 6px">Regulatory framework</div><h1>Luxembourg UCI Part II</h1>
      <p>Every filing date on the fund's calendar comes from the 5 rules you approved here. When a regulation changes, start a review and check the rules again.</p></div>
    </header>
    <!-- ux.md:216: a RUN_ACTIVE refusal shows at the top AND next to the button. Hidden until #start-refused:target. -->
    <div class="refline">{chip("1 action was refused", "you")}<span>A new review can't start while review 4 is in progress.</span><a href="#start-refused">Go to “Start a new review”</a></div>
    <section class="cta" aria-labelledby="cta-h">
      <div><div class="k">Waiting for you</div><h2 id="cta-h">Review 4: 5 rules left to check</h2>
      <p>AI drafted 7 rules from the sources. You've approved 2. The calendar stays as it is until you finish.</p></div>
      <a class="btn" href="review-rules.html">Continue checking</a>
    </section>
    <div class="kpis" aria-label="Summary" style="grid-template-columns:repeat(3,minmax(0,1fr))">
      {kpi("Sources", "6", "13 paragraphs of regulation", "doc")}
      {kpi("Rules in the published calendar", "5", "Approved on Fri 13 Nov 2026", "check")}
      {kpi("Sources that disagree", "2", "On the annual report and the beneficial-owner update", "flag", "you")}
    </div>
    <section class="section"><div class="card"><div class="card-h"><div><h2 class="sq">Reviews</h2><p>Open a review to carry on where you left off, or to see what you decided before.</p></div></div>
        <table><thead><tr><th scope="col">Review</th><th scope="col">Started</th><th scope="col">Status</th><th scope="col"><span class="sr">Open</span></th></tr></thead><tbody>{rows}</tbody></table>
        {start_review}</div></section>
    <section class="section"><div class="card"><div class="card-h"><div><h2 class="sq">Sources</h2><p>The rules are drafted from these 5 laws and circulars. The practitioner guide is only used to double-check them.</p></div></div>
      <table><thead><tr><th scope="col">ID</th><th scope="col">Document</th><th scope="col">Type</th><th scope="col">Paragraphs</th></tr></thead><tbody>{srows}</tbody></table></div></section>"""


# ---------------------------------------------------------------- a second fund on the same framework
FUND2 = "Hollowmere Infrastructure Fund SICAV"


def funds():
    return f"""
    <header class="head">
      <div><h1>Funds</h1><p>Each fund has its own calendar. Funds on the same framework share its approved rules, so you check those rules once.</p></div>
      <div class="actions"><a class="ghost" href="add-fund.html">Add a fund</a></div>
    </header>
    <section class="cta" aria-labelledby="cta-h">
      <div><div class="k">Waiting for you</div><h2 id="cta-h">{FUND2}: 4 answers left to confirm</h2>
      <p>Its framework's rules are already approved. You only confirm which of them apply to this fund.</p></div>
      <a class="btn" href="fund-applies.html">Continue</a>
    </section>
    <section class="section"><div class="card">
      <table><thead><tr><th scope="col">Fund</th><th scope="col">Framework</th><th scope="col">Calendar</th><th scope="col">Filings in 2027</th><th scope="col">Due next</th><th scope="col"><span class="sr">Open</span></th></tr></thead>
      <tbody>
        <tr><td><b>{FUND}</b><span class="m">Bramblegate Partners</span></td><td>Luxembourg UCI Part II</td><td>{chip("Published", "done")}</td><td class="num">22</td><td class="num">Mon 11 Jan 2027</td><td><a class="more" href="calendar.html">Open calendar</a></td></tr>
        <tr><td><b>{FUND2}</b><span class="m">Hollowmere Partners</span></td><td>Luxembourg UCI Part II<span class="m">Rules reused</span></td><td>{chip("Your turn: 4 to confirm", "you")}</td><td class="muted">Not calculated yet</td><td class="muted">Not calculated yet</td><td><a class="more" href="fund-applies.html">Continue</a></td></tr>
      </tbody></table></div></section>"""


def add_fund():
    steps = [("done", "", "Step 1", "Choose a framework and enter the fund's facts", "Your turn", True),
             ("done", "", "Skipped", "Check the rules", "Already approved for this framework", False),
             ("", "", "Step 2", "Confirm what applies", "Not started", False), ("", "", "Step 3", "Publish the calendar", "Not started", False)]
    lis = "".join(f'<li class="{"" if cur else cls}{" skipped" if n == "Skipped" else ""}"{" aria-current=\"step\"" if cur else ""}><div class="n">{n}</div><div class="t">{t}</div><div class="s">{w}</div></li>' for cls, _, n, t, w, cur in steps)
    yn = lambda name: opts(name, ["Yes", "No", "Not known"])
    return f"""
    <div class="crumb"><a href="funds.html">Funds</a><span>›</span><span>Add a fund</span></div>
    <header class="head"><div><h1>Add a fund</h1>
      <p>Choose the framework the fund falls under. If its rules are already approved, there is nothing to re-check: you enter a few facts and confirm which rules apply.</p></div></header>
    <ol class="steps" aria-label="Steps to add a fund">{lis}</ol>
    <section class="section two">
      <div class="rule-card gate"><form class="decision" method="post" action="fund-applies.html" style="border-top:0">
        <fieldset><legend>Which framework does the fund fall under?</legend>
          <div class="picks">
            <label class="pick"><input type="radio" name="fw" value="yes"><span><b>Luxembourg UCI Part II</b><span class="small muted">6 approved rules · used by 1 fund</span>{chip("Rules already approved", "done")}</span></label>
            <label class="pick"><input type="radio" name="fw" value="no"><span><b>A different framework</b><span class="small muted">For example a Luxembourg RAIF</span>{chip("Needs a review first")}</span></label>
          </div></fieldset>
        <div class="if yes" style="max-width:none">
          <p class="lead">These are the facts the framework's 6 rules depend on. AI uses them to work out which rules apply.</p>
          <div class="formgrid">
            <div class="field"><label for="fn">Fund name</label><input type="text" id="fn" name="name" value="{FUND2}"></div>
            <div class="field"><label for="gp">GP</label><input type="text" id="gp" name="gp" value="Hollowmere Partners"></div>
            <div class="field"><label for="ye">Financial year end</label><select id="ye" name="ye"><option>30 June</option><option>31 December</option><option>31 March</option><option>30 September</option></select></div>
          </div>
          <fieldset><legend>Where is it marketed?</legend><div class="opts">{"".join(f'<label class="opt"><input type="checkbox" name="mk"{" checked" if c in ("Luxembourg", "Germany") else ""}>{c}</label>' for c in ["Luxembourg", "Germany", "Spain", "France", "Italy"])}</div></fieldset>
          <fieldset><legend>Is it registered for VAT in Luxembourg?</legend>{yn("vat")}</fieldset>
          <fieldset><legend>Is it registered with the Luxembourg Business Registers?</legend>{yn("rbe")}</fieldset>
          <div><button class="btn" type="submit">Check which rules apply</button></div></div>
        <div class="if no">
          <p class="lead">A framework's rules have to be approved once before any fund can use it. Start a review: AI drafts the rules from the regulation and you check them. Every later fund on that framework skips that step.</p>
          <div><a class="btn" href="frameworks.html">Go to filing rules</a></div></div>
      </form></div>
      <div class="card pad"><h3>What reusing the framework saves</h3>
        {bars("First fund on Luxembourg UCI Part II: rules to check", "7", 100, "This fund: rules to check", "0", 0)}
        {bars("First fund: steps", "4", 100, "This fund: steps", "2", 50)}
        <p class="small" style="margin-top:14px">The 6 approved rules, their source quotes and your decisions carry over. What stays per fund is which rules apply and the dates, because those depend on the fund's own facts.</p></div>
    </section>"""


def fund_applies():
    rows = [("Monthly financial report U1.1", "Applies", "agent", "Subject to Part II: yes", True),
            ("Subscription tax return and payment", "Applies", "agent", "Established in Luxembourg: yes", True),
            ("Audited annual report", "Applies", "agent", "Subject to Part II: yes · year end 30 June", False),
            ("Statistical report A01 (Spain)", "Doesn't apply", "", "Marketed in: Luxembourg, Germany. Not Spain.", False),
            ("Beneficial-owner information update", "Applies", "agent", "Registered entity: yes. A date is added when owners change.", False),
            ("Annual VAT return", "Applies", "agent", "Registered for VAT: yes", False)]
    trs = ""
    for n, (name, ans, kind, fact, done) in enumerate(rows, 1):
        act = (chip("You confirmed", "done") if done else
               f'<form method="post" action="#r{n}" style="display:flex;gap:10px;align-items:center"><button class="btn sm" type="submit">Confirm</button><a class="more" href="applicability.html">Overrule</a></form>')
        trs += f'<tr id="r{n}"><td><b>{name}</b></td><td>{chip("AI: " + ans.lower(), kind)}</td><td>{fact}</td><td>{act}</td></tr>'
    steps = [("done", "Step 1", "Framework and fund facts", "Done"), ("done skipped", "Skipped", "Check the rules", "Already approved for this framework"),
             ("cur", "Step 2", "Confirm what applies", "Your turn"), ("", "Step 3", "Publish the calendar", "Not started")]
    lis = "".join(f'<li class="{c if c != "cur" else ""}"{" aria-current=\"step\"" if c == "cur" else ""}><div class="n">{n}</div><div class="t">{t}</div><div class="s">{w}</div></li>' for c, n, t, w in steps)
    return f"""
    <div class="crumb"><a href="funds.html">Funds</a><span>›</span><span>{FUND2}</span></div>
    <header class="head"><div><h1>Confirm what applies</h1>
      <p>AI matched the framework's 6 approved rules to this fund's facts. Each answer shows the fact it rests on. Confirm it, or overrule it.</p></div></header>
    <ol class="steps" aria-label="Steps to add a fund">{lis}</ol>
    <div class="kpis" aria-label="Summary" style="grid-template-columns:repeat(3,minmax(0,1fr))">
      <div class="kpi dark"><div class="ring-row" style="color:#cfcfcf">{ring(2, 6)}<div><b style="color:#fff">4 of 6 left</b>You've confirmed 2</div></div></div>
      {kpi("Rules reused", "6", "Approved for Bramblegate Credit Opportunities SICAV. Nothing to re-check.", "check")}
      {kpi("Answers AI couldn't settle", "0", "Every answer rests on a fact you entered", "care")}
    </div>
    <section class="section"><div class="card">
      <table><thead><tr><th scope="col">Rule</th><th scope="col">AI's answer</th><th scope="col">The fact it rests on</th><th scope="col">Your decision</th></tr></thead><tbody>{trs}</tbody></table></div></section>
    <section class="section"><div class="card pad"><h2 class="sq you">4 answers left to confirm</h2>
      <p style="margin:10px 0 16px;max-width:64ch">Once you've confirmed them all, the dates are calculated by code and you publish this fund's calendar.</p>
      <form method="post" action="funds.html"><button class="btn" type="submit">Finish and calculate dates</button></form></div></section>"""


SIGNIN = f"""<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in · ACME Compliance calendar (demo)</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lexend:wght@300;400;500&family=Inter:wght@400;500;600&family=DM+Mono&display=swap">
<link rel="stylesheet" href="app.css?v=__V__"></head>
<body><div class="signin">
  <section class="stage" aria-label="About">
    <a class="brand" href="index.html" style="padding:0"><b>acme</b><i></i></a>
    <div class="cluster" aria-hidden="true">
      <div class="dcard c-cal"><div class="dh"><div class="dt">2027 filing calendar</div><span>Fictional fund · 22 deadlines</span></div>{dotchart("public")}</div>
      <div class="dcard c-flag"><div class="tags">{chip("Sources disagree", "you")}</div>{bars("The law", "6 mo", 100, "A practitioner guide", "4 mo", 66.6)}</div>
      <div class="dcard c-ring"><div class="ring-row">{ring(6, 7)}<div><b>6 of 7</b>rules approved by a person. One was rejected.</div></div></div>
    </div>
    <h1 style="max-width:17ch">AI drafts. People approve.</h1>
    <p style="max-width:52ch">I designed this tool to read fund regulations and draft a compliance calendar: who must file what, and by when. A wrong date has real consequences, so I started from one question: where can I trust AI, and where can't I?</p><p style="max-width:52ch;margin-top:12px">My approach is: decide what must never go wrong, make code and people responsible for that, and let AI speed up everything else. Then scope ruthlessly to what can actually ship.</p>
  </section>
  <main class="enter"><div class="inner">
    <h2>Sign in</h2>
    <p style="margin-top:8px">Choose a role to explore the demo with mock data. You don't need a password.</p>
    <form method="post" action="frameworks.html"><button class="role" type="submit" name="role" value="specialist">
      <span class="t">Compliance specialist</span><span class="d">Check the rules AI drafts, then publish the calendar.</span></button></form>
    <form method="post" action="gp-calendar.html"><button class="role" type="submit" name="role" value="gp">
      <span class="t">General Partner / Fund Manager</span><span class="d">See what your fund must file and when. View only.</span></button></form>
    <p class="hint" style="margin-top:20px">The fund and the firm are fictional.</p>
  </div></main>
</div></body></html>
"""

INDEX_ROWS = [("sign-in.html", "Sign in", "Choose the compliance specialist or the GP"),
              ("frameworks.html", "Filing rules", "The fund's filing rules, and the reviews of them"),
              ("run-status.html", "Step 1 · AI is drafting the rules", "Nothing for the specialist to do yet"),
              ("run-status-done.html", "Step 1 · AI has finished", "The specialist can start checking"),
              ("review-rules.html", "Step 2 · Check the rules", "The specialist approves or rejects each rule"),
              ("applicability.html", "Step 3 · Confirm what applies", "The specialist confirms which rules apply to the fund"),
              ("publish.html", "Step 4 · Publish the calendar", "The specialist checks the dates and publishes them"),
              ("calendar.html", "Compliance calendar (specialist)", "The published calendar, as the specialist sees it"),
              ("gp-calendar.html", "Compliance calendar (GP)", "The same calendar, view only"),
              ("gp-calendar-empty.html", "Compliance calendar (GP, nothing published)", "Before the first calendar is published"),
              ("funds.html", "Funds", "Every fund and where its calendar stands"),
              ("add-fund.html", "Add a fund", "A second fund reuses the approved rules"),
              ("fund-applies.html", "Add a fund · Confirm what applies", "The only checking a second fund needs")]

if __name__ == "__main__":
    pages = {
        "calendar.html": page("Compliance calendar", calendar_page(True), "calendar"),
        "gp-calendar.html": page("Compliance calendar", calendar_page(False), "calendar", role="gp"),
        "gp-calendar-empty.html": page("Compliance calendar", gp_empty(), "calendar", role="gp"),
        "frameworks.html": page("Frameworks", frameworks(), "frameworks"),
        "run-status.html": page("Review 4", run_status(), "frameworks", waiting=False),
        "run-status-done.html": page("Review 4", run_status(done=True), "frameworks", waiting=False),
        "review-rules.html": page("Check the rules", review_rules(), "frameworks", waiting=False),
        "applicability.html": page("Confirm what applies", applicability(), "frameworks", waiting=False),
        "publish.html": page("Publish the calendar", publish(), "frameworks", waiting=False),
        "sign-in.html": SIGNIN,
        "funds.html": page("Funds", funds(), "funds"),
        "add-fund.html": page("Add a fund", add_fund(), "funds", fund="New fund", fund_note="Not set up yet"),
        "fund-applies.html": page("Confirm what applies", fund_applies(), "funds", fund=FUND2, fund_note="Luxembourg UCI Part II · year end 30 Jun"),
    }
    rows = "".join(f'<tr><td><a href="{h}"><b>{t}</b></a></td><td>{d}</td></tr>' for h, t, d in INDEX_ROWS)
    pages["index.html"] = page("All mock-ups", f'<header class="head"><div><h1>Mock-ups</h1><p>All the screens, in the order they are used.</p></div></header>'
                               f'<section class="section"><div class="card"><table><thead><tr><th scope="col">Screen</th><th scope="col">What it shows</th></tr></thead><tbody>{rows}</tbody></table></div></section>', active="", waiting=False)
    # Dates that mean "today" and "yesterday" are filled in when the pages are built, so the
    # mock-ups never show a stale publication date. (In the real app the server supplies them.)
    from datetime import timedelta
    today, yesterday = fmt(date.today()), fmt(date.today() - timedelta(days=1))
    for name, html in pages.items():
        html = html.replace("__V__", str(int((OUT / "app.css").stat().st_mtime)))  # so the browser never shows an old stylesheet
        html = html.replace("Fri 13 Nov 2026", today).replace("Thu 12 Nov 2026", yesterday)
        (OUT / name).write_text(html, encoding="utf-8")
    print("wrote", len(pages), "pages to", OUT)
