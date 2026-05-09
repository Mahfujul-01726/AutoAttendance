from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from database import AttendanceDatabase


app = FastAPI(title="Advanced Attendance API")
db = AttendanceDatabase()


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>Attendance Dashboard</title>
      <style>
        :root {
          color-scheme: light;
          --ink: #18201d;
          --muted: #66736d;
          --line: #d8dfda;
          --bg: #f5f7f2;
          --panel: #ffffff;
          --accent: #0f766e;
          --warn: #b45309;
        }
        * { box-sizing: border-box; }
        body {
          margin: 0;
          background: linear-gradient(135deg, #f5f7f2 0%, #e8f0ea 48%, #f8faf7 100%);
          color: var(--ink);
          font-family: "Segoe UI", Tahoma, sans-serif;
        }
        header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 22px 28px;
          border-bottom: 1px solid var(--line);
          background: rgba(255,255,255,0.78);
          backdrop-filter: blur(10px);
        }
        h1 { margin: 0; font-size: 24px; font-weight: 700; }
        main { max-width: 1180px; margin: 0 auto; padding: 24px; }
        .stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; margin-bottom: 18px; }
        .stat, section {
          background: var(--panel);
          border: 1px solid var(--line);
          border-radius: 8px;
          box-shadow: 0 10px 30px rgba(20, 35, 29, 0.06);
        }
        .stat { padding: 18px; }
        .label { color: var(--muted); font-size: 13px; }
        .value { font-size: 30px; font-weight: 800; margin-top: 6px; }
        section { overflow: hidden; }
        .section-head { display: flex; justify-content: space-between; padding: 16px 18px; border-bottom: 1px solid var(--line); }
        h2 { margin: 0; font-size: 17px; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px 18px; text-align: left; border-bottom: 1px solid var(--line); font-size: 14px; }
        th { color: var(--muted); font-weight: 700; background: #fafbf9; }
        .status { color: var(--accent); font-weight: 700; }
        .empty { padding: 22px 18px; color: var(--muted); }
        button {
          border: 1px solid var(--line);
          background: #fff;
          color: var(--ink);
          border-radius: 6px;
          min-height: 36px;
          padding: 0 12px;
          cursor: pointer;
        }
        @media (max-width: 720px) {
          header { align-items: flex-start; flex-direction: column; gap: 10px; }
          main { padding: 14px; }
          .stats { grid-template-columns: 1fr; }
          th, td { padding: 10px; }
        }
      </style>
    </head>
    <body>
      <header>
        <h1>Attendance Dashboard</h1>
        <button onclick="loadData()">Refresh</button>
      </header>
      <main>
        <div class="stats">
          <div class="stat"><div class="label">Students</div><div class="value" id="studentsCount">0</div></div>
          <div class="stat"><div class="label">Face Embeddings</div><div class="value" id="embeddingCount">0</div></div>
          <div class="stat"><div class="label">Present Today</div><div class="value" id="presentCount">0</div></div>
        </div>
        <section>
          <div class="section-head"><h2>Recent Attendance</h2><span class="label" id="today"></span></div>
          <table>
            <thead><tr><th>Name</th><th>Date</th><th>Time</th><th>Distance</th><th>Status</th></tr></thead>
            <tbody id="attendanceRows"></tbody>
          </table>
          <div class="empty" id="emptyState">No attendance records yet.</div>
        </section>
      </main>
      <script>
        async function loadData() {
          const summary = await fetch('/api/summary').then(r => r.json());
          const attendance = await fetch('/api/attendance').then(r => r.json());
          document.getElementById('studentsCount').textContent = summary.students;
          document.getElementById('embeddingCount').textContent = summary.embeddings;
          document.getElementById('presentCount').textContent = summary.present_today;
          document.getElementById('today').textContent = summary.today;
          const rows = document.getElementById('attendanceRows');
          rows.innerHTML = '';
          document.getElementById('emptyState').style.display = attendance.length ? 'none' : 'block';
          for (const item of attendance) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td>${item.student_name}</td><td>${item.date}</td><td>${item.time}</td><td>${Number(item.confidence).toFixed(3)}</td><td class="status">${item.status}</td>`;
            rows.appendChild(tr);
          }
        }
        loadData();
      </script>
    </body>
    </html>
    """


@app.get("/api/summary")
def summary():
    today = datetime.now().strftime("%Y-%m-%d")
    students = db.list_students()
    attendance = db.list_attendance(date=today, limit=500)
    return {
        "today": today,
        "students": len(students),
        "embeddings": sum(item["embedding_count"] for item in students),
        "present_today": len(attendance),
    }


@app.get("/api/students")
def students():
    return db.list_students()


@app.get("/api/attendance")
def attendance(date: str | None = None, limit: int = 200):
    return db.list_attendance(date=date, limit=limit)


@app.get("/api/alerts")
def alerts(limit: int = 100):
    return db.list_alerts(limit=limit)
