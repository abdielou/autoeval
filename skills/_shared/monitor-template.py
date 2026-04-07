#!/usr/bin/env python3
"""autoeval progress dashboard -- monitors an autonomous optimization loop.

Usage:
    python monitor.py              # serves dashboard on http://localhost:8080
    python monitor.py --port 9090  # custom port

Reads progress.jsonl for iteration data. Falls back to parsing git log
if progress.jsonl doesn't exist yet. No dependencies beyond Python stdlib.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
try:
    from http.server import ThreadingHTTPServer
except ImportError:
    ThreadingHTTPServer = HTTPServer  # fallback for older Python
from datetime import datetime

REFRESH_INTERVAL = 30  # seconds

# Resolve paths relative to the script location, not cwd
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_progress_jsonl():
    """Read progress.jsonl and return list of iteration dicts."""
    path = os.path.join(SCRIPT_DIR, "progress.jsonl")
    if not os.path.exists(path):
        return []
    iterations = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                iterations.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return iterations


def parse_git_log():
    """Fallback: parse git log commit messages for scores."""
    try:
        result = subprocess.run(
            ["git", "log", "--reverse", "--format=%H|%aI|%s"],
            capture_output=True, text=True, check=True, cwd=SCRIPT_DIR
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    iterations = []
    score_re = re.compile(r"score\s+([\d.]+)", re.IGNORECASE)
    hyp_re = re.compile(r"hypothesis:\s*(.+?)\s*--\s*change:", re.IGNORECASE)

    for i, line in enumerate(result.stdout.strip().split("\n")):
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        commit_hash, timestamp, message = parts

        score_match = score_re.search(message)
        if not score_match:
            continue

        hyp_match = hyp_re.search(message)
        hypothesis = hyp_match.group(1) if hyp_match else message

        iterations.append({
            "iteration": len(iterations) + 1,
            "timestamp": timestamp,
            "score": float(score_match.group(1)),
            "components": {},
            "hypothesis": hypothesis,
            "kept": True,
            "commit": commit_hash[:8],
        })

    return iterations


def get_data():
    """Get iteration data from best available source.

    Uses whichever source has more entries — progress.jsonl may be
    incomplete if the loop didn't write to it consistently.
    """
    jsonl_data = parse_progress_jsonl()
    git_data = parse_git_log()
    data = jsonl_data if len(jsonl_data) >= len(git_data) else git_data

    if not data:
        return {
            "iterations": [],
            "components": [],
            "best_score": 0,
            "baseline_score": 0,
            "total_iterations": 0,
            "kept_iterations": 0,
            "elapsed": "0s",
            "delta": 0,
        }

    # Extract component names from first iteration that has them
    component_names = []
    for d in data:
        if d.get("components"):
            component_names = sorted(d["components"].keys())
            break

    best_score = max(d["score"] for d in data)
    baseline_score = data[0]["score"] if data else 0
    kept = [d for d in data if d.get("kept", True)]

    # Calculate elapsed time
    try:
        t0 = datetime.fromisoformat(data[0]["timestamp"].replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(data[-1]["timestamp"].replace("Z", "+00:00"))
        elapsed_seconds = (t1 - t0).total_seconds()
        if elapsed_seconds < 60:
            elapsed = f"{int(elapsed_seconds)}s"
        elif elapsed_seconds < 3600:
            elapsed = f"{int(elapsed_seconds // 60)}m {int(elapsed_seconds % 60)}s"
        else:
            hours = int(elapsed_seconds // 3600)
            mins = int((elapsed_seconds % 3600) // 60)
            elapsed = f"{hours}h {mins}m"
    except (ValueError, KeyError):
        elapsed = "unknown"

    return {
        "iterations": data,
        "components": component_names,
        "best_score": best_score,
        "baseline_score": baseline_score,
        "total_iterations": len(data),
        "kept_iterations": len(kept),
        "elapsed": elapsed,
        "delta": round(best_score - baseline_score, 4),
    }


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>autoeval progress</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: #0d1117; color: #c9d1d9; padding: 24px; }
  h1 { font-size: 20px; font-weight: 600; margin-bottom: 16px; color: #f0f6fc; }
  .stats { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px 20px; min-width: 140px; }
  .stat-label { font-size: 12px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
  .stat-value { font-size: 24px; font-weight: 600; color: #f0f6fc; }
  .stat-value.positive { color: #3fb950; }
  .stat-value.negative { color: #f85149; }
  .stat-value.neutral { color: #8b949e; }
  .chart-container { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
  canvas { max-height: 400px; }
  .failures-section { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 24px; }
  .failures-section h2 { font-size: 16px; font-weight: 600; margin-bottom: 12px; color: #f0f6fc; }
  .failures-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .failures-table th { text-align: left; color: #8b949e; padding: 8px; border-bottom: 1px solid #30363d; font-weight: 500; }
  .failures-table td { padding: 8px; border-bottom: 1px solid #21262d; color: #c9d1d9; }
  .failures-table tr:hover td { background: #1c2128; }
  .failure-score { color: #f85149; font-weight: 600; }
  .failure-reason { color: #d29922; }
  .footer { font-size: 12px; color: #484f58; text-align: center; margin-top: 24px; }
  .no-data { text-align: center; padding: 80px 20px; color: #8b949e; font-size: 16px; }
  .refresh-indicator { font-size: 12px; color: #484f58; float: right; margin-top: -32px; }
</style>
</head>
<body>
<h1>autoeval progress</h1>
<div class="refresh-indicator">auto-refresh: <span id="countdown">REFRESH_INTERVAL_VALUE</span>s</div>

<div id="stats" class="stats"></div>
<div class="chart-container">
  <canvas id="chart"></canvas>
</div>
<div id="no-data" class="no-data" style="display:none;">
  Waiting for first iteration... dashboard will auto-refresh.
</div>
<div id="failures-section" class="failures-section" style="display:none;">
  <h2>Failed Experiments (learnings)</h2>
  <table class="failures-table">
    <thead>
      <tr><th>#</th><th>Score</th><th>Hypothesis</th><th>Why it failed</th></tr>
    </thead>
    <tbody id="failures-body"></tbody>
  </table>
</div>
<div class="footer">autoeval monitoring dashboard &mdash; refreshes every REFRESH_INTERVAL_VALUE seconds</div>

<script>
const REFRESH_INTERVAL = REFRESH_INTERVAL_VALUE;
let chart = null;
let countdown = REFRESH_INTERVAL;

const COLORS = [
  '#58a6ff', '#3fb950', '#d29922', '#f85149', '#bc8cff',
  '#39d2c0', '#f778ba', '#79c0ff', '#7ee787', '#e3b341'
];

function deltaClass(val) {
  if (val > 0) return 'positive';
  if (val < 0) return 'negative';
  return 'neutral';
}

function renderStats(data) {
  const el = document.getElementById('stats');
  el.innerHTML = `
    <div class="stat">
      <div class="stat-label">Best Score</div>
      <div class="stat-value">${data.best_score.toFixed(4)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Baseline</div>
      <div class="stat-value">${data.baseline_score.toFixed(4)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Delta</div>
      <div class="stat-value ${deltaClass(data.delta)}">${data.delta >= 0 ? '+' : ''}${data.delta.toFixed(4)}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Iterations</div>
      <div class="stat-value">${data.total_iterations}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Kept</div>
      <div class="stat-value positive">${data.kept_iterations}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Reverted</div>
      <div class="stat-value negative">${data.total_iterations - data.kept_iterations}</div>
    </div>
    <div class="stat">
      <div class="stat-label">Elapsed</div>
      <div class="stat-value">${data.elapsed}</div>
    </div>
  `;
}

function renderChart(data) {
  const ctx = document.getElementById('chart').getContext('2d');

  if (data.iterations.length === 0) {
    document.getElementById('no-data').style.display = 'block';
    document.querySelector('.chart-container').style.display = 'none';
    return;
  }
  document.getElementById('no-data').style.display = 'none';
  document.querySelector('.chart-container').style.display = 'block';

  const labels = data.iterations.map(d => d.iteration || labels.length + 1);

  // Split iterations into kept and reverted for separate rendering
  const keptScores = data.iterations.map(d => d.kept !== false ? d.score : null);
  const revertedScores = data.iterations.map(d => d.kept === false ? d.score : null);

  // Composite score dataset (kept only — connected line)
  const datasets = [{
    label: 'Kept',
    data: keptScores,
    borderColor: COLORS[0],
    backgroundColor: COLORS[0] + '20',
    borderWidth: 2,
    pointRadius: 4,
    pointHoverRadius: 7,
    fill: false,
    tension: 0.1,
    spanGaps: true,
  }];

  // Reverted experiments — red scatter dots, no connecting line
  if (revertedScores.some(s => s !== null)) {
    datasets.push({
      label: 'Reverted',
      data: revertedScores,
      borderColor: '#f85149',
      backgroundColor: '#f8514940',
      borderWidth: 1,
      pointRadius: 5,
      pointHoverRadius: 8,
      pointStyle: 'crossRot',
      showLine: false,
    });
  }

  // Component datasets
  if (data.components.length > 0) {
    data.components.forEach((name, i) => {
      datasets.push({
        label: name,
        data: data.iterations.map(d => (d.components || {})[name] ?? null),
        borderColor: COLORS[(i + 1) % COLORS.length],
        borderWidth: 1.5,
        pointRadius: 2,
        borderDash: [4, 2],
        fill: false,
        tension: 0.1,
        hidden: true,  // toggled on by clicking legend
      });
    });
  }

  // Best score annotation line
  const bestLine = {
    label: 'Best',
    data: data.iterations.map(() => data.best_score),
    borderColor: '#3fb950',
    borderWidth: 1,
    borderDash: [8, 4],
    pointRadius: 0,
    fill: false,
  };
  datasets.push(bestLine);

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        tooltip: {
          callbacks: {
            afterBody: function(context) {
              const idx = context[0].dataIndex;
              const iter = data.iterations[idx];
              if (!iter) return '';
              const lines = [];
              if (iter.hypothesis) lines.push('Hypothesis: ' + iter.hypothesis);
              if (iter.kept === false) {
                lines.push('[REVERTED]');
                if (iter.failure_reason) lines.push('Reason: ' + iter.failure_reason);
              }
              return lines.join('\\n');
            }
          }
        },
        legend: {
          labels: { color: '#8b949e', usePointStyle: true, pointStyle: 'circle' }
        }
      },
      scales: {
        x: {
          title: { display: true, text: 'Iteration', color: '#8b949e' },
          ticks: { color: '#484f58' },
          grid: { color: '#21262d' },
        },
        y: {
          title: { display: true, text: 'Score', color: '#8b949e' },
          ticks: { color: '#484f58' },
          grid: { color: '#21262d' },
          min: 0,
          max: 1,
        }
      }
    }
  });
}

function renderFailures(data) {
  const failures = data.iterations.filter(d => d.kept === false);
  const section = document.getElementById('failures-section');
  const tbody = document.getElementById('failures-body');

  if (failures.length === 0) {
    section.style.display = 'none';
    return;
  }
  section.style.display = 'block';

  // Show most recent failures first, limit to 20
  const recent = failures.slice(-20).reverse();
  tbody.innerHTML = recent.map(f => `
    <tr>
      <td>${f.iteration || '?'}</td>
      <td class="failure-score">${(f.score != null) ? f.score.toFixed(4) : '?'}</td>
      <td>${f.hypothesis || '—'}</td>
      <td class="failure-reason">${f.failure_reason || '—'}</td>
    </tr>
  `).join('');
}

async function refresh() {
  try {
    const resp = await fetch('/data');
    const data = await resp.json();
    renderStats(data);
    renderChart(data);
    renderFailures(data);
  } catch (e) {
    console.error('Refresh failed:', e);
  }
  countdown = REFRESH_INTERVAL;
}

// Countdown timer
setInterval(() => {
  countdown--;
  document.getElementById('countdown').textContent = countdown;
  if (countdown <= 0) {
    refresh();
  }
}, 1000);

// Initial load
refresh();
</script>
</body>
</html>""".replace('REFRESH_INTERVAL_VALUE', str(REFRESH_INTERVAL))


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            data = get_data()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        elif self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress request logs


def main():
    parser = argparse.ArgumentParser(description="autoeval progress dashboard")
    parser.add_argument("--port", type=int, default=8080, help="port to serve on (default: 8080)")
    parser.add_argument("--no-open", action="store_true", help="don't open browser automatically")
    args = parser.parse_args()

    port = args.port
    server = None
    for attempt in range(10):
        # Connect-based check: on Windows, HTTPServer can bind to a port
        # already in use without error, so we probe first
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            if s.connect_ex(("localhost", port)) == 0:
                # Port is in use — something is listening
                if attempt == 0:
                    print(f"Port {port} in use, finding a free port...")
                port += 1
                continue
        try:
            server = ThreadingHTTPServer(("localhost", port), DashboardHandler)
            break
        except OSError:
            port += 1
    if server is None:
        print(f"Could not find a free port in range {args.port}-{port}.")
        sys.exit(1)

    url = f"http://localhost:{port}"
    print(f"autoeval dashboard running at {url}")
    print(f"auto-refreshes every {REFRESH_INTERVAL}s -- press Ctrl+C to stop")

    if not args.no_open:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\ndashboard stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
