(function () {
  const container = document.getElementById("summarizepaper-output");
  if (!container) return;

  // This script runs every time the Labs toggle is clicked, also when it is
  // turned off: a container that already has content is emptied instead.
  if (container.innerHTML.trim().length > 0) {
    container.innerHTML = "";
    container.setAttribute("style", "display:none");
    return;
  }
  container.setAttribute("style", "display:block");

  // The arXiv identifier from the URL, e.g. "2103.17249v2" or "astro-ph/9212001"
  const arxivId = window.location.pathname.replace(/^\/abs\//, "");
  const api = "https://www.summarizepaper.com/api/arxiv-labs/" + arxivId;
  const fallbackUrl = "https://www.summarizepaper.com/abs/" + arxivId;

  container.innerHTML = "<p>Loading SummarizePaper…</p>";

  // A slow answer must not leave the card waiting: past 6 seconds, the plain link
  const controller = window.AbortController ? new AbortController() : null;
  const timer = controller ? setTimeout(function () { controller.abort(); }, 6000) : null;

  fetch(api, controller ? { signal: controller.signal } : {})
    .then(function (response) {
      clearTimeout(timer);
      if (!response.ok) throw new Error("Not OK response");
      return response.json();
    })
    .then(render)
    .catch(function () {
      render({ available: false, url: fallbackUrl });
    });

  function escape(text) {
    const div = document.createElement("div");
    div.textContent = text == null ? "" : String(text);
    return div.innerHTML;
  }

  // A few inline styles, as other Labs cards do: arXiv's stylesheet has no rules for them
  const STYLE = {
    card: "border:1px solid #d9d9e3;border-radius:8px;overflow:hidden;margin:1rem 0;background:#fff;max-width:52rem",
    bar: "height:4px;background:linear-gradient(90deg,#f97316,#ec4899 35%,#6366f1 65%,#10b981)",
    body: "padding:.9rem 1.1rem 1rem",
    header: "display:flex;flex-wrap:wrap;align-items:center;gap:.5rem;margin-bottom:.6rem",
    name: "font-size:1.05rem;font-weight:600;margin:0",
    badge: "font-size:.72rem;color:#4338ca;background:#eef0ff;border-radius:999px;padding:.1rem .55rem",
    lead: "font-size:.95rem;line-height:1.45;margin:0 0 .4rem",
    label: "font-size:.7rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:#5b5b6b;margin:.9rem 0 .3rem",
    text: "margin:0;line-height:1.45",
    list: "list-style:none;margin:0;padding:0",
    item: "margin:.4rem 0;font-size:.85rem;line-height:1.5",
    result: "font-size:.68rem;font-weight:600;color:#166534;background:#e8f7ee;border-radius:4px;padding:.05rem .4rem;margin-right:.4rem",
    interpretation: "font-size:.68rem;font-weight:600;color:#92400e;background:#fdf3e4;border-radius:4px;padding:.05rem .4rem;margin-right:.4rem",
    point: "color:#6366f1;margin-right:.4rem",
    muted: "margin:0;color:#5b5b6b;line-height:1.45",
    footer: "display:flex;flex-wrap:wrap;align-items:center;gap:.6rem 1rem;margin-top:1rem;padding-top:.8rem;border-top:1px solid #ececf3",
    button: "display:inline-block;background:#4f46e5;color:#fff;border-radius:6px;padding:.4rem .8rem;font-size:.85rem;text-decoration:none",
    note: "font-size:.75rem;color:#5b5b6b",
  };

  function link(url, text) {
    return `<a href="${escape(url)}" target="_blank" rel="noopener" style="${STYLE.button}">${escape(text)}</a>`;
  }

  function section(title, content) {
    return `<p style="${STYLE.label}">${title}</p>${content}`;
  }

  function list(items) {
    return items.length ? `<ul style="${STYLE.list}">${items.join("")}</ul>` : "";
  }

  function item(tag, tagStyle, text) {
    return `<li style="${STYLE.item}"><span style="${tagStyle}">${tag}</span>${escape(text)}</li>`;
  }

  // The version the card is about: the reader may be looking at another one
  function version(data) {
    return data.version ? ` \u00b7 v${Number(data.version)}` : "";
  }

  function card(badge, body, footer) {
    return `
      <div style="${STYLE.card}">
        <div style="${STYLE.bar}"></div>
        <div style="${STYLE.body}">
          <div style="${STYLE.header}">
            <h2 style="${STYLE.name}">SummarizePaper</h2>
            ${badge ? `<span style="${STYLE.badge}">${badge}</span>` : ""}
          </div>
          ${body}
          <div style="${STYLE.footer}">${footer}</div>
        </div>
      </div>`;
  }

  function render(data) {
    const note = `<span style="${STYLE.note}">AI-generated; it may contain errors. Check against the paper.</span>`;
    const more = link(data.url, "Full summary and Q&A →");
    let html;
    if (data.available && data.kind === "reading") {
      const findings = (data.findings || []).map(function (finding) {
        return finding.kind === "interpretation"
          ? item("Interpretation", STYLE.interpretation, finding.text)
          : item("Result", STYLE.result, finding.text);
      });
      const limitation = (data.limitations || [])[0];
      html = card(
        `AI reading of the ${data.scope === "abstract" ? "abstract" : "full text"}${version(data)}`,
        `<p style="${STYLE.lead}">${escape(data.tldr)}</p>
         ${data.question ? section("Question", `<p style="${STYLE.text}">${escape(data.question)}</p>`) : ""}
         ${section("Main findings", list(findings))}
         ${limitation ? section("Limitation", `<p style="${STYLE.muted}">${escape(limitation)}</p>`) : ""}`,
        more + note,
      );
    } else if (data.available) {
      const points = (data.key_points || []).map(function (point) {
        return item("•", STYLE.point, point);
      });
      html = card(
        `AI summary${version(data)}`,
        `<p style="${STYLE.lead}">${escape(data.summary)}</p>
         ${points.length ? section("Key points", list(points)) : ""}`,
        more + note,
      );
    } else {
      html = card(
        "",
        `<p style="${STYLE.text}">No summary of this paper yet. SummarizePaper writes AI summaries of arXiv papers
         (key findings, plain-language version) and answers questions about them, citing the passages it relies on.</p>`,
        link(data.url, "Summarize this paper →"),
      );
    }
    container.innerHTML = window.DOMPurify.sanitize(html, { ADD_ATTR: ["target"] });
  }
})();
