const form = document.getElementById("search-form");
const input = document.getElementById("q");
const go = document.getElementById("go");
const statusEl = document.getElementById("status");
const list = document.getElementById("results");

const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

// Highlight the searcher's own words. Text is escaped first, so this is safe.
function highlight(text, query) {
  const words = [...new Set(query.toLowerCase().split(/\s+/).filter((w) => w.length > 2))]
    .map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const safe = esc(text);
  if (!words.length) return safe;
  return safe.replace(new RegExp(`\\b(${words.join("|")})`, "gi"), "<mark>$1</mark>");
}

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.classList.toggle("error", isError);
}

function showLoading() {
  list.innerHTML = '<li class="skeleton"></li>'.repeat(3);
}

function render(query, papers) {
  list.innerHTML = "";
  if (!papers.length) {
    setStatus("No papers found. Try fewer words or a broader topic.");
    return;
  }
  setStatus(`${papers.length} papers for "${query}"`);
  papers.forEach((p, i) => {
    const abstract = p.abstract.length
      ? p.abstract.map((s) => `<p>${s.label ? `<strong>${esc(s.label)}.</strong> ` : ""}${esc(s.text)}</p>`).join("")
      : "<p>No abstract is available for this paper.</p>";
    const li = document.createElement("li");
    li.className = "paper";
    li.innerHTML = `
      <h2>${highlight(p.title, query)}</h2>
      <p class="meta">${esc(p.journal)}, ${esc(p.date)}${p.authors ? "<br>" + esc(p.authors) : ""}</p>
      <p class="summary">${highlight(p.summary, query)}</p>
      <button class="toggle" type="button" aria-expanded="false" aria-controls="d${i}">Read abstract</button>
      <div class="detail" id="d${i}"><div>
        <div class="abstract">${abstract}<a class="source" href="${esc(p.url)}" target="_blank" rel="noopener">Open on PubMed</a></div>
      </div></div>`;
    li.querySelector(".toggle").addEventListener("click", (e) => {
      const open = li.classList.toggle("open");
      e.currentTarget.setAttribute("aria-expanded", open);
      e.currentTarget.textContent = open ? "Hide abstract" : "Read abstract";
    });
    list.appendChild(li);
  });
}

async function search(query) {
  query = query.trim();
  if (query.length < 3) return setStatus("Type at least 3 characters to search.", true);
  input.value = query;
  go.disabled = true;
  setStatus("Searching PubMed...");
  showLoading();
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong. Search again.");
    render(data.query, data.results);
  } catch (err) {
    list.innerHTML = "";
    setStatus(err.message, true);
  } finally {
    go.disabled = false;
  }
}

form.addEventListener("submit", (e) => { e.preventDefault(); search(input.value); });
document.querySelectorAll(".chip").forEach((c) => c.addEventListener("click", () => search(c.dataset.q)));
