import os, sqlite3, json, uuid
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, request, session, redirect, url_for, flash, jsonify, render_template_string, render_template, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE=Path(__file__).resolve().parent
UPLOADS=BASE/"uploads"; UPLOADS.mkdir(exist_ok=True)
DB=BASE/"studio.db"
app=Flask(__name__)
@app.after_request
def disable_page_cache(response):
 response.headers["Cache-Control"]="no-store, no-cache, must-revalidate, max-age=0"
 response.headers["Pragma"]="no-cache"
 response.headers["Expires"]="0"
 return response
app.secret_key=os.getenv("SECRET_KEY","replace-this-before-production")
app.config["MAX_CONTENT_LENGTH"]=8*1024*1024

def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
with conn() as c:
 c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT DEFAULT 'user');
 CREATE TABLE IF NOT EXISTS drawings(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,image TEXT,steps TEXT,created TEXT);""")
 admin=os.getenv("ADMIN_EMAIL","").strip().lower()
 admin_password=os.getenv("ADMIN_PASSWORD","")
 if admin and admin_password:
  password_hash=generate_password_hash(admin_password)
  existing=c.execute("SELECT id FROM users WHERE email=?",(admin,)).fetchone()
  if existing:
   c.execute("UPDATE users SET name=?,password=?,role='admin' WHERE email=?",("Zayya Admin",password_hash,admin))
  else:
   c.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",("Zayya Admin",admin,password_hash,"admin"))
  c.execute("DELETE FROM users WHERE email='admin@aidrawingstudio.local' AND email<>?",(admin,))

def auth(fn):
 @wraps(fn)
 def w(*a,**k):
  if not session.get("uid"): return redirect("/login")
  return fn(*a,**k)
 return w
def isadmin(fn):
 @wraps(fn)
 def w(*a,**k):
  if not session.get("uid") or session.get("role")!="admin": return redirect("/login")
  return fn(*a,**k)
 return w

STYLE="""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');
:root{--espresso:#1b100a;--gold:#d7a13d;--gold2:#f0c66d;--cream:#f7efe1;--muted:#b9a894;--line:#63472d}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--espresso);color:var(--cream);font:15px 'DM Sans',sans-serif}
.nav{position:sticky;top:0;z-index:1000;padding:17px 5%;display:flex;justify-content:space-between;background:rgba(27,16,10,.97);backdrop-filter:blur(16px);border-bottom:1px solid #ffffff18;align-items:center;gap:18px}
.brand{font-weight:800;color:var(--cream);text-decoration:none;font-size:21px;white-space:nowrap}.brand:before{content:'✦';color:var(--gold);margin-right:9px}
.nav-links{display:flex;align-items:center;gap:22px}.nav a{color:#e7d9c7;text-decoration:none;font-weight:600}.nav-links a:hover{color:var(--gold2)}
.menu-toggle{display:none;background:transparent;border:1px solid #80613d;color:var(--cream);width:46px;height:42px;border-radius:10px;font-size:25px;cursor:pointer}
.wrap{max-width:1080px;margin:auto;padding:38px 22px 70px}.eyebrow{color:var(--gold2);font-size:11px;letter-spacing:3px;font-weight:bold;text-transform:uppercase}
h1,h2,h3{color:var(--cream)}p{color:#c5b6a3;line-height:1.8}.hero{display:grid;grid-template-columns:1fr 1fr;gap:45px;align-items:center;min-height:520px}.hero h1{font:700 clamp(40px,5vw,62px)/1.08 'Playfair Display';margin:20px 0}.hero h1 em{color:var(--gold)}
.btn{background:linear-gradient(110deg,var(--gold),var(--gold2));color:#251509!important;border:0;padding:14px 23px;border-radius:30px;text-decoration:none;display:inline-block;font-weight:800;cursor:pointer;box-shadow:0 8px 25px #d7a13d25;transition:.2s}.btn:hover{transform:translateY(-2px)}
.card{background:linear-gradient(145deg,#302014,#24150d);border:1px solid #60452b;border-radius:22px;padding:28px;box-shadow:0 12px 35px #0003;color:var(--cream)}
.features{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:35px 0}.auth{max-width:500px;margin:35px auto;padding:clamp(25px,6vw,48px)}.auth h1,.head h1{font:700 clamp(38px,6vw,54px) 'Playfair Display';color:var(--cream)}
.field{display:block;margin:17px 0;font-weight:700;font-size:14px;color:#eadcc9}.field input,.field textarea,.field select{display:block;width:100%;padding:15px 16px;border:1px solid #684a2e;border-radius:12px;margin-top:9px;background:#1d120c;color:#fff8ec;font:inherit;outline:none}.field input:focus,.field textarea:focus{border-color:var(--gold);box-shadow:0 0 0 3px #d7a13d22}
.full{width:100%}.head{margin:15px 0 28px}.drop{padding:30px;border:1px dashed #a77c42;border-radius:14px;background:#2a1a10;text-align:center}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:15px}
.stepno{color:var(--gold2);font-size:11px;font-weight:bold;letter-spacing:2px}.tip{padding:12px;background:#3b2919;border-radius:10px;color:#f1ce8d}.flash{background:#48271b;color:#ffcfad;padding:12px;border-radius:10px;margin-bottom:15px}.stat{font-size:32px;font-weight:bold;color:var(--gold2)}
table{width:100%;border-collapse:collapse;color:var(--cream)}td,th{text-align:left;padding:12px;border-bottom:1px solid #5b4029}th{color:var(--gold2)}footer{text-align:center;padding:25px;color:#a9957e;font-size:12px;border-top:1px solid #60452b;background:#170d08}
a{color:var(--gold2)}img{max-width:100%}
@media(max-width:760px){.nav{padding:13px 5%}.menu-toggle{display:block}.nav-links{display:none;position:absolute;top:100%;left:0;right:0;background:#1b100a;border-bottom:1px solid #684a2e;padding:24px 7% 30px;flex-direction:column;align-items:stretch;gap:0;box-shadow:0 18px 25px #0006}.nav-links.open{display:flex}.nav-links a{padding:15px 0;border-bottom:1px solid #ffffff12;font-size:18px}.hero{grid-template-columns:1fr}.features,.grid{grid-template-columns:1fr}.wrap{padding:25px 16px 55px}.card{padding:21px}.auth{margin:15px auto}.nav{flex-wrap:nowrap}}
</style>"""
from extras import extras
app.register_blueprint(extras)

def page(body,title="Zayya Studio"):
 return render_template_string("""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}}</title>"""+STYLE+"""</head><body><nav class="nav"><a class="brand" href="/">✦ Zayya Studio</a><button class="menu-toggle" type="button" aria-label="Open menu" onclick="this.nextElementSibling.classList.toggle('open')">☰</button><div class="nav-links"><a href="/">Home</a><a href="/chat">AI Chat</a><a href="/contact">Contact</a><a href="/about">About &amp; Projects</a>{% if session.get('uid') %}<a href="/studio">Zayya Studio</a>{% if session.get('role')=='admin' %}<a href="/admin">Admin</a><a href="/admin/messages">Messages</a><a href="/admin/projects">Manage Projects</a>{% endif %}<a href="/logout">Log out</a>{% else %}<a href="/login">Log in</a><a href="/register">Create account</a>{% endif %}</div></nav><main class="wrap">{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}"""+body+"""</main><footer>Zayya Studio · Learn to draw, one step at a time</footer></body></html>""",title=title)

@app.route("/")
def home():
 # Render the public homepage as a template so signed-in users keep their session-aware navigation.
 return render_template_string((BASE / "index.html").read_text(encoding="utf-8"))

@app.route("/register",methods=["GET","POST"])
def register():
 if request.method=="POST":
  name=request.form.get("name","").strip(); email=request.form.get("email","").strip().lower(); pw=request.form.get("password","")
  if not name or len(pw)<8: flash("Enter your name and a password of at least 8 characters.")
  else:
   try:
    with conn() as c:c.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,generate_password_hash(pw)))
    return redirect("/login")
   except sqlite3.IntegrityError:flash("That email is already registered.")
 return page("""<section class="auth card"><div class="eyebrow">JOIN THE STUDIO</div><h1>Create account</h1><form method="post"><label class="field">Your name<input name="name" required></label><label class="field">Email<input type="email" name="email" required></label><label class="field">Password<input type="password" name="password" minlength="8" required></label><button class="btn full">Create account</button></form><p>Already registered? <a href="/login">Log in</a></p></section>""")
@app.route("/login",methods=["GET","POST"])
def login():
 if request.method=="POST":
  with conn() as c:u=c.execute("SELECT * FROM users WHERE email=?",(request.form.get("email","").lower(),)).fetchone()
  if u and check_password_hash(u["password"],request.form.get("password","")):
   session.clear();session.update(uid=u["id"],name=u["name"],role=u["role"]);return redirect("/admin" if u["role"]=="admin" else "/studio")
  flash("Email or password is incorrect.")
 return page("""<style>
.auth{position:relative;overflow:hidden;isolation:isolate;animation:authEnter .75s cubic-bezier(.2,.8,.2,1) both;box-shadow:0 25px 80px #0008,0 0 45px #d7a13d16}
.auth:before,.auth:after{content:"";position:absolute;z-index:-1;border-radius:50%;filter:blur(2px);pointer-events:none}
.auth:before{width:220px;height:220px;right:-95px;top:-100px;background:radial-gradient(circle,#f0c66d55,transparent 70%);animation:authFloat 7s ease-in-out infinite}
.auth:after{width:180px;height:180px;left:-90px;bottom:-100px;background:radial-gradient(circle,#d7a13d38,transparent 70%);animation:authFloat 9s ease-in-out infinite reverse}
.auth h1{font:700 clamp(34px,5vw,46px)/1.1 'Playfair Display';margin:12px 0 24px}
.auth .field{position:relative;z-index:1}.auth input{transition:border-color .25s,box-shadow .25s,transform .25s}
.auth input:focus{outline:none;border-color:#f0c66d;box-shadow:0 0 0 4px #d7a13d22;transform:translateY(-1px)}
.auth .btn{transition:transform .25s,box-shadow .25s}.auth .btn:hover{transform:translateY(-3px);box-shadow:0 14px 30px #d7a13d45}
@keyframes authEnter{from{opacity:0;transform:translateY(24px) scale(.98)}to{opacity:1;transform:translateY(0) scale(1)}}
@keyframes authFloat{0%,100%{transform:translate(0,0)}50%{transform:translate(-16px,18px)}}
@media(prefers-reduced-motion:reduce){.auth,.auth:before,.auth:after{animation:none}}
</style><section class="auth card"><div class="eyebrow">✦ WELCOME BACK</div><h1>Welcome <span style="color:#f0c66d">back.</span></h1><p>Sign in to continue to your creative workspace.</p><form method="post" action="/login"><label class="field">Email<input type="email" name="email" autocomplete="username" required></label><label class="field">Password<input type="password" name="password" autocomplete="current-password" required></label><button class="btn full" type="submit">Sign in to dashboard →</button></form><p>New here? <a href="/register">Create an account</a></p><p><a href="/">← Back to Home</a></p></section>""")
@app.route("/logout")
def logout():session.clear();return redirect("/")
@app.route("/studio",methods=["GET"])
@auth
def studio():
 return page("""<div class="head"><div class="eyebrow">YOUR CREATIVE WORKSPACE</div><h1>Make a drawing lesson</h1><p>Upload a clear portrait to generate a nine-step drawing guide.</p></div><section class="card" style="max-width:650px;margin:auto"><form action="/generate" method="post" enctype="multipart/form-data"><label class="field">Lesson title<input name="title" placeholder="Portrait practice"></label><label class="field drop">↑<br>Choose portrait image<input type="file" name="photo" accept="image/png,image/jpeg,image/webp" required></label><button class="btn full">Generate my 9-step lesson ✦</button></form></section>""")
@app.route("/generate",methods=["POST"])
@auth
def generate():
 f=request.files.get("photo"); title=request.form.get("title","Portrait drawing lesson").strip()[:100] or "Portrait drawing lesson"
 if not f or not f.filename:return redirect("/studio")
 ext=f.filename.rsplit(".",1)[-1].lower()
 if ext not in ("png","jpg","jpeg","webp"):flash("Use PNG, JPG or WEBP.");return redirect("/studio")
 fname=uuid.uuid4().hex+"."+ext; f.save(UPLOADS/fname)
 try:
  from google import genai
  from google.genai import types
  key=os.getenv("GEMINI_API_KEY")
  if not key:raise RuntimeError("AI is not enabled yet. Add GEMINI_API_KEY in Render Environment settings.")
  client=genai.Client(api_key=key)
  prompt='Analyze this portrait as a drawing reference. Return ONLY JSON: {"steps":[{"name":"...","instruction":"...","tip":"..."}]}. Create exactly 9 beginner-friendly original drawing stages, from basic head shape and guidelines through facial features, hair, shading and finishing. Do not identify the person.'
  response=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-2.5-flash"),contents=[types.Part.from_bytes(data=(UPLOADS/fname).read_bytes(),mime_type=f.mimetype),prompt],config=types.GenerateContentConfig(response_mime_type="application/json"))
  steps=json.loads(response.text)["steps"]
  if len(steps)!=9:raise ValueError("AI did not return nine steps. Try again.")
  with conn() as c:cur=c.execute("INSERT INTO drawings(user_id,title,image,steps,created) VALUES(?,?,?,?,?)",(session["uid"],title,fname,json.dumps(steps),datetime.utcnow().isoformat()));did=cur.lastrowid
  return redirect("/drawing/"+str(did))
 except Exception as e:
  (UPLOADS/fname).unlink(missing_ok=True);flash("Could not create lesson: "+str(e));return redirect("/studio")
@app.route("/drawings")
@auth
def drawings():
 with conn() as c:rows=c.execute("SELECT * FROM drawings WHERE user_id=? ORDER BY id DESC",(session["uid"],)).fetchall()
 cards="".join(f'<article class="card"><h3>{r["title"]}</h3><p>{r["created"][:10]}</p><a href="/drawing/{r["id"]}">Open lesson →</a></article>' for r in rows)
 return page('<div class="head"><div class="eyebrow">YOUR LIBRARY</div><h1>Saved drawings</h1></div><div class="grid">'+(cards or '<div class="card">No saved lessons yet. <a href="/studio">Create one</a>.</div>')+'</div>')
@app.route("/drawing/<int:did>")
@auth
def drawing(did):
 with conn() as c:r=c.execute("SELECT * FROM drawings WHERE id=? AND user_id=?",(did,session["uid"])).fetchone()
 if not r:return "Not found",404
 steps=json.loads(r["steps"]); cards="".join(f'<article class="card"><div class="stepno">STEP {i}</div><h2>{s.get("name","")}</h2><p>{s.get("instruction","")}</p><div class="tip">✦ Tip: {s.get("tip","")}</div></article>' for i,s in enumerate(steps,1))
 return page(f'<div class="head"><div class="eyebrow">YOUR DRAWING LESSON</div><h1>{r["title"]}</h1></div><img src="/uploads/{r["image"]}" style="max-width:240px;border-radius:14px"><div class="grid">{cards}</div>')
@app.route("/uploads/<path:filename>")
@auth
def uploads(filename):
 with conn() as c:r=c.execute("SELECT user_id FROM drawings WHERE image=?",(filename,)).fetchone()
 if not r or (r["user_id"]!=session["uid"] and session.get("role")!="admin"):return "Not found",404
 return send_from_directory(UPLOADS,filename)
@app.route("/admin")
@isadmin
def admin():
 with conn() as c:
  users=c.execute("SELECT id,name,email,role FROM users ORDER BY id DESC").fetchall()
  drawings=c.execute("SELECT d.title,d.created,u.name FROM drawings d JOIN users u ON u.id=d.user_id ORDER BY d.id DESC").fetchall()
  count=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
  dc=c.execute("SELECT COUNT(*) FROM drawings").fetchone()[0]
  try: mc=c.execute("SELECT COUNT(*) FROM contact_messages").fetchone()[0]
  except sqlite3.OperationalError: mc=0
 rows="".join(f'<tr><td>{u["name"]}</td><td>{u["email"]}</td><td>{u["role"]}</td></tr>' for u in users)
 lessons="".join(f'<tr><td>{d["title"]}</td><td>{d["name"]}</td><td>{d["created"][:10]}</td></tr>' for d in drawings)
 return page(f'''<style>
 .dash-head{{display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:24px}}
 .dash-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin:22px 0}}
 .dash-stat{{font-size:38px;font-weight:800;color:#f0c66d;letter-spacing:-1px}}
 .dash-card{{transition:transform .25s,border-color .25s}}.dash-card:hover{{transform:translateY(-4px);border-color:#d7a13d88}}
 .dash-actions{{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0 28px}}
 .dash-actions a{{margin:0}}.dash-table{{overflow-x:auto}}
 </style>
 <div class="dash-head"><div><div class="eyebrow">SECURE CONTROL CENTER</div><h1>Admin Dashboard</h1><p>Manage your studio, members, drawing activity and incoming messages.</p></div><span class="eyebrow">ADMIN ACCESS</span></div>
 <div class="dash-actions"><a class="btn" href="/admin/messages">Inbox · {mc} messages</a><a class="btn" href="/admin/projects">Manage Projects</a><a class="btn" href="/studio">Open Studio</a></div>
 <div class="dash-grid"><div class="card dash-card"><div class="dash-stat">{count}</div><b>Registered users</b><p>All accounts in your studio</p></div><div class="card dash-card"><div class="dash-stat">{dc}</div><b>Saved drawing lessons</b><p>Lessons created by members</p></div><div class="card dash-card"><div class="dash-stat">{mc}</div><b>Contact messages</b><p>Messages sent from the public website</p></div></div>
 <section class="card"><h2>Recent Members</h2><div class="dash-table"><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>{rows or "<tr><td colspan=3>No members yet.</td></tr>"}</table></div></section>
 <section class="card"><h2>Drawing Activity</h2><div class="dash-table"><table><tr><th>Lesson</th><th>Member</th><th>Date</th></tr>{lessons or "<tr><td colspan=3>No drawings yet.</td></tr>"}</table></div></section>''')
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
