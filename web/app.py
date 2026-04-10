"""FastAPI web app for the Wikipedia path finder."""

import asyncio
import time
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from wiki_path.api_client import WikiApiClient
from wiki_path.bfs import find_path
from wiki_path.path_utils import normalize_title

app = FastAPI(title="WikiPath Finder", version="1.0.0")


class PathRequest(BaseModel):
    source: str
    target: str
    max_depth: int = 6


class PathResponse(BaseModel):
    path: Optional[list[str]] = None
    hops: Optional[int] = None
    elapsed_ms: float = 0.0
    error: Optional[str] = None


@app.post("/find-path", response_model=PathResponse)
async def find_wiki_path(req: PathRequest) -> PathResponse:
    source = normalize_title(req.source)
    target = normalize_title(req.target)
    start = time.perf_counter()

    async with WikiApiClient() as client:
        src_title, src_exists, _ = await client.resolve_title(source)
        tgt_title, tgt_exists, _ = await client.resolve_title(target)

        if not src_exists:
            return PathResponse(error=f"Article not found: {source}")
        if not tgt_exists:
            return PathResponse(error=f"Article not found: {target}")

        try:
            path = await asyncio.wait_for(
                find_path(src_title, tgt_title, client, req.max_depth),
                timeout=60.0,
            )
        except asyncio.TimeoutError:
            elapsed = (time.perf_counter() - start) * 1000
            return PathResponse(
                elapsed_ms=round(elapsed, 1),
                error="Search timed out after 60 seconds.",
            )

    elapsed = (time.perf_counter() - start) * 1000

    if path is None:
        return PathResponse(
            elapsed_ms=round(elapsed, 1),
            error=f"No path found within {req.max_depth} hops.",
        )

    return PathResponse(
        path=path,
        hops=len(path) - 1,
        elapsed_ms=round(elapsed, 1),
    )


@app.get("/", response_class=HTMLResponse)
async def index() -> str:
    return _HTML_PAGE


_HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>WikiPath Finder</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #f8f9fa;
      color: #212529;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }

    header {
      text-align: center;
      margin-bottom: 2rem;
    }
    header h1 { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
    header p  { color: #6c757d; margin-top: 0.4rem; }

    .card {
      background: #fff;
      border-radius: 12px;
      box-shadow: 0 2px 12px rgba(0,0,0,.08);
      padding: 2rem;
      width: 100%;
      max-width: 560px;
    }

    label { display: block; font-size: .85rem; font-weight: 600; margin-bottom: .3rem; color: #495057; }

    input[type="text"] {
      width: 100%;
      padding: .6rem .8rem;
      border: 1.5px solid #ced4da;
      border-radius: 8px;
      font-size: 1rem;
      outline: none;
      transition: border-color .15s;
    }
    input[type="text"]:focus { border-color: #4361ee; }

    .row { display: flex; gap: 1rem; margin-bottom: 1rem; }
    .row .field { flex: 1; }

    .options { display: flex; align-items: center; gap: .6rem; margin-bottom: 1.2rem; font-size: .9rem; color: #495057; }
    .options input[type="number"] {
      width: 60px; padding: .4rem .5rem;
      border: 1.5px solid #ced4da; border-radius: 6px; font-size: .9rem;
    }

    button {
      width: 100%; padding: .75rem;
      background: #4361ee; color: #fff;
      border: none; border-radius: 8px;
      font-size: 1rem; font-weight: 600;
      cursor: pointer; transition: background .15s;
    }
    button:hover:not(:disabled) { background: #3451d1; }
    button:disabled { background: #adb5bd; cursor: not-allowed; }

    #result { margin-top: 1.5rem; }

    .spinner {
      display: flex; align-items: center; gap: .6rem;
      color: #6c757d; font-size: .95rem;
    }
    .spinner svg { animation: spin 1s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }

    .path-box {
      background: #f1f3f5; border-radius: 10px;
      padding: 1.2rem 1.4rem;
    }
    .path-box .meta {
      font-size: .8rem; color: #6c757d; margin-bottom: .8rem;
    }
    .path-steps { list-style: none; }
    .path-steps li {
      display: flex; align-items: center; gap: .5rem;
      padding: .35rem 0; font-size: .95rem;
    }
    .path-steps li:not(:last-child)::after {
      content: "↓"; color: #adb5bd;
      display: block; margin-left: .2rem;
    }
    .path-steps a {
      color: #4361ee; text-decoration: none; font-weight: 500;
    }
    .path-steps a:hover { text-decoration: underline; }
    .step-num {
      background: #4361ee; color: #fff;
      border-radius: 50%; width: 22px; height: 22px;
      display: inline-flex; align-items: center; justify-content: center;
      font-size: .72rem; font-weight: 700; flex-shrink: 0;
    }

    .error-box {
      background: #fff3cd; border: 1px solid #ffc107;
      border-radius: 8px; padding: 1rem 1.2rem;
      color: #856404; font-size: .95rem;
    }
  </style>
</head>
<body>
  <header>
    <h1>WikiPath Finder</h1>
    <p>Find the shortest hyperlink path between two Wikipedia articles.</p>
  </header>

  <div class="card">
    <div class="row">
      <div class="field">
        <label for="source">Source article</label>
        <input type="text" id="source" placeholder="e.g. Jeffrey Epstein" />
      </div>
      <div class="field">
        <label for="target">Target article</label>
        <input type="text" id="target" placeholder="e.g. Albert Einstein" />
      </div>
    </div>

    <div class="options">
      <label for="depth" style="margin:0">Max hops:</label>
      <input type="number" id="depth" value="6" min="1" max="10" />
    </div>

    <button id="search-btn" onclick="search()">Find Path</button>

    <div id="result"></div>
  </div>

  <script>
    async function search() {
      const source = document.getElementById('source').value.trim();
      const target = document.getElementById('target').value.trim();
      const maxDepth = parseInt(document.getElementById('depth').value, 10);
      const resultEl = document.getElementById('result');
      const btn = document.getElementById('search-btn');

      if (!source || !target) {
        resultEl.innerHTML = '<div class="error-box">Please enter both article titles.</div>';
        return;
      }

      btn.disabled = true;
      resultEl.innerHTML = `
        <div class="spinner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#4361ee" stroke-width="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          Searching... (this may take up to a minute)
        </div>`;

      try {
        const resp = await fetch('/find-path', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ source, target, max_depth: maxDepth }),
        });
        const data = await resp.json();

        if (data.error) {
          resultEl.innerHTML = `<div class="error-box">${escHtml(data.error)}</div>`;
        } else {
          const elapsed = (data.elapsed_ms / 1000).toFixed(2);
          const hopWord = data.hops === 1 ? 'hop' : 'hops';
          const steps = data.path.map((title, i) => {
            const url = 'https://en.wikipedia.org/wiki/' + encodeURIComponent(title.replace(/ /g, '_'));
            return `<li>
              <span class="step-num">${i + 1}</span>
              <a href="${url}" target="_blank" rel="noopener">${escHtml(title)}</a>
            </li>`;
          }).join('');

          resultEl.innerHTML = `
            <div class="path-box">
              <div class="meta">${data.hops} ${hopWord} &nbsp;·&nbsp; ${elapsed}s</div>
              <ul class="path-steps">${steps}</ul>
            </div>`;
        }
      } catch (err) {
        resultEl.innerHTML = `<div class="error-box">Request failed: ${escHtml(String(err))}</div>`;
      } finally {
        btn.disabled = false;
      }
    }

    function escHtml(str) {
      return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    ['source', 'target'].forEach(id => {
      document.getElementById(id).addEventListener('keydown', e => {
        if (e.key === 'Enter') search();
      });
    });
  </script>
</body>
</html>
"""
