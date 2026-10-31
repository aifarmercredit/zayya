import os, sqlite3, json, uuid
from datetime import datetime
from pathlib import Path
from functools import wraps
from flask import Flask, request, session, redirect, url_for, flash, jsonify, render_template_string, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE=Path(__file__).resolve().parent
UPLOADS=BASE/"uploads"; UPLOADS.mkdir(exist_ok=True)
DB=BASE/"studio.db"
app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","replace-this-before-production")
app.config["MAX_CONTENT_LENGTH"]=8*1024*1024

def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
with conn() as c:
 c.executescript("""CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT DEFAULT 'user');
 CREATE TABLE IF NOT EXISTS drawings(id INTEGER PRIMARY KEY,user_id INTEGER,title TEXT,image TEXT,steps TEXT,created TEXT);""")
 admin=os.getenv("ADMIN_EMAIL","admin@aidrawingstudio.local").lower()
 if not c.execute("SELECT id FROM users WHERE email=?",(admin,)).fetchone():
  c.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",("Studio Admin",admin,generate_password_hash(os.getenv("ADMIN_PASSWORD","ChangeMe123!")),"admin"))

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

def page(body,title="AI Drawing Studio"):
 return render_template_string("""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}}</title>"""+STYLE+"""</head><body><nav class="nav"><a class="brand" href="/">✦ AI Drawing Studio</a><button class="menu-toggle" type="button" aria-label="Open menu" onclick="this.nextElementSibling.classList.toggle('open')">☰</button><div class="nav-links"><a href="/chat">AI Chat</a><a href="/contact">Contact</a><a href="/about">About</a>{% if session.get('uid') %}<a href="/studio">Create</a><a href="/drawings">My drawings</a>{% if session.get('role')=='admin' %}<a href="/admin">Admin</a>{% endif %}<a href="/logout">Log out</a>{% else %}<a href="/login">Log in</a><a href="/register">Sign up</a>{% endif %}</div></nav><main class="wrap">{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}"""+body+"""</main><footer>AI Drawing Studio · Learn to draw, one step at a time</footer></body></html>""",title=title)

@app.route("/")
def home():
 with conn() as c:
  projects=c.execute("SELECT title,url FROM projects ORDER BY id DESC").fetchall() if c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'").fetchone() else []
 project_cards="".join(f'<a class="project-card" href="{p["url"]}" target="_blank" rel="noopener"><span class="project-dot">↗</span><span><b>{p["title"]}</b><small>Explore project</small></span></a>' for p in projects)
 return page("""
 <style>
 body{background:#070b16;color:#f5f7ff}.nav{background:#090f20;border-color:#202a42}.brand,.nav a{color:#e7edff}.wrap{max-width:1200px}.aa-hero{position:relative;overflow:hidden;border:1px solid #27334e;border-radius:30px;padding:clamp(35px,7vw,90px);background:radial-gradient(circle at 80% 15%,#4e39a455,transparent 35%),linear-gradient(135deg,#101b35,#080d1b 70%);min-height:430px;animation:rise .8s ease both}.aa-hero:before,.aa-hero:after{content:"";position:absolute;border:1px solid #8b9bff44;border-radius:50%;width:360px;height:360px;right:-90px;top:-130px;animation:orbit 18s linear infinite}.aa-hero:after{width:250px;height:250px;right:-35px;top:-75px;animation-direction:reverse}.aa-kicker{color:#b7a8ff;letter-spacing:4px;font-size:12px;font-weight:bold}.aa-hero h1{font-size:clamp(48px,8vw,90px);line-height:.98;max-width:720px;margin:22px 0;background:linear-gradient(90deg,#fff,#b6c7ff,#d4a9ff);background-clip:text;color:transparent}.aa-hero p{color:#b6c0d8;max-width:580px;font-size:17px}.aa-btn{display:inline-block;padding:14px 22px;border-radius:30px;background:linear-gradient(100deg,#6d5dfc,#b65cff);color:white;text-decoration:none;font-weight:bold;margin:12px 10px 0 0;box-shadow:0 8px 30px #755bff55;transition:.25s}.aa-btn:hover{transform:translateY(-4px);box-shadow:0 14px 35px #755bff88}.section-title{font-size:34px;color:#f5f7ff;margin:65px 0 10px}.section-sub{color:#9daac5}.project-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(235px,1fr));gap:16px;margin-top:25px}.project-card{display:flex;align-items:center;gap:15px;padding:22px;border-radius:18px;border:1px solid #293653;background:linear-gradient(145deg,#121d35,#0b1223);text-decoration:none;color:#f4f6ff;transition:.25s;animation:rise .7s both}.project-card:hover{transform:translateY(-7px);border-color:#8b78ff;box-shadow:0 15px 35px #0006}.project-dot{width:44px;height:44px;display:grid;place-items:center;border-radius:14px;background:#705cff;color:white;font-size:23px}.project-card small{display:block;color:#9daac5;margin-top:6px}.social-row{display:flex;gap:14px;margin-top:25px}.social-icon{width:52px;height:52px;display:grid;place-items:center;border:1px solid #34415e;border-radius:16px;background:#111b30;color:white;transition:.25s}.social-icon:hover{transform:translateY(-5px) scale(1.05);background:#6d5dfc}.social-icon svg{width:25px;height:25px;fill:currentColor}.aa-footer{margin-top:70px;padding:30px;text-align:center;border-top:1px solid #27334e;color:#8794b0}@keyframes rise{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:translateY(0)}}@keyframes orbit{to{transform:rotate(360deg)}}@media(max-width:650px){.aa-hero{padding:32px 24px}.aa-hero h1{font-size:50px}.section-title{font-size:28px}}.nav{background:rgba(27,16,10,.97);border-color:#60452b}.brand,.nav a{color:#f7efe1}.aa-hero{border:1px solid #76552f;background:radial-gradient(circle at 80% 15%,#d7a13d35,transparent 38%),linear-gradient(135deg,#3a2415,#1b100a 72%);border-radius:28px;box-shadow:0 25px 65px #0006}.aa-hero:before,.aa-hero:after{border-color:#d7a13d55}.aa-kicker{color:#e6bd6c}.aa-hero h1{background:linear-gradient(90deg,#fff8ec,#e9bd68,#fff0d1);background-clip:text;color:transparent}.aa-hero p{color:#d4c3ae}.aa-btn{background:linear-gradient(110deg,#d49a32,#f0c66d);color:#241508;box-shadow:0 8px 30px #d7a13d33}.aa-btn:hover{box-shadow:0 14px 35px #d7a13d66}.section-title{color:#f7efe1}.section-sub{color:#b9a894}.project-card{border:1px solid #60452b;background:linear-gradient(145deg,#352214,#21130b);color:#fff5e5}.project-card:hover{border-color:#d7a13d;box-shadow:0 15px 35px #0007}.project-dot{background:linear-gradient(130deg,#c88c2d,#f0c66d);color:#28170d}.project-card small{color:#b9a894}.social-icon{border-color:#684a2e;background:#2b1a10;color:#f2d18b}.social-icon:hover{background:#bd842d}.aa-footer{border-color:#60452b;color:#a9957e}
 </style>
 <section class="aa-hero"><div class="aa-kicker">INDEPENDENT DEVELOPER · DIGITAL CREATOR</div><h1>Amir Ali<br>Projects.</h1><p>Building useful websites, creative digital experiences and AI-powered tools. Explore my work and connect with me.</p><a class="aa-btn" href="#projects">Explore projects ↘</a><a class="aa-btn" href="/contact" style="background:transparent;border:1px solid #65739a;box-shadow:none">Contact me</a>
 <div class="social-row">
 <a class="social-icon" href="https://www.tiktok.com/@zayya_an" target="_blank" rel="noopener" aria-label="TikTok"><svg viewBox="0 0 24 24"><path d="M19.6 7.2a6.8 6.8 0 0 1-4.2-1.5v8.1a6.1 6.1 0 1 1-5.3-6.05v3.3a2.9 2.9 0 1 0 2 2.75V2.5h3.3c.2 2.1 1.8 3.8 4.2 4.1z"/></svg></a>
 <a class="social-icon" href="https://www.instagram.com/zayya_an2" target="_blank" rel="noopener" aria-label="Instagram"><svg viewBox="0 0 24 24"><path d="M7 2h10a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5H7a5 5 0 0 1-5-5V7a5 5 0 0 1 5-5zm0 2.2A2.8 2.8 0 0 0 4.2 7v10A2.8 2.8 0 0 0 7 19.8h10a2.8 2.8 0 0 0 2.8-2.8V7A2.8 2.8 0 0 0 17 4.2zm5 3a4.8 4.8 0 1 1 0 9.6 4.8 4.8 0 0 1 0-9.6zm0 2.2a2.6 2.6 0 1 0 0 5.2 2.6 2.6 0 0 0 0-5.2zm5.1-3.2a1.1 1.1 0 1 1 0 2.2 1.1 1.1 0 0 1 0-2.2z"/></svg></a>
 <a class="social-icon" href="https://t.me/zayya_an" target="_blank" rel="noopener" aria-label="Telegram"><svg viewBox="0 0 24 24"><path d="M21.8 4.2 18.5 20c-.25 1.12-.9 1.4-1.83.87l-5.05-3.72-2.44 2.35c-.27.27-.5.5-1.02.5l.36-5.14 9.36-8.45c.4-.36-.09-.56-.62-.2L5.69 13.52.72 11.97c-1.08-.34-1.1-1.08.23-1.6L20.4 2.8c.9-.33 1.7.22 1.4 1.4z"/></svg></a>
 </div></section>
 <section id="projects"><h2 class="section-title">Selected Projects</h2><p class="section-sub">A collection of websites and tools I have created.</p><div class="project-grid">"""+project_cards+"""</div></section>
 <section><h2 class="section-title">Let’s build something useful.</h2><p class="section-sub">Have an idea, question or project? Send me a message.</p><a class="aa-btn" href="/contact">Send a message ↗</a><a class="aa-btn" href="tel:0967757546" style="background:#17243c;box-shadow:none">Call me</a></section>
 <div class="aa-footer">© 2026 Amir Ali Projects · All rights reserved</div>
 ""","Amir Ali Projects")

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
 return page("""<section class="auth card"><div class="eyebrow">WELCOME BACK</div><h1>Log in</h1><form method="post"><label class="field">Email<input type="email" name="email" required></label><label class="field">Password<input type="password" name="password" required></label><button class="btn full">Log in</button></form><p>New here? <a href="/register">Create an account</a></p></section>""")
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
  users=c.execute("SELECT id,name,email,role FROM users ORDER BY id DESC").fetchall(); drawings=c.execute("SELECT d.title,d.created,u.name FROM drawings d JOIN users u ON u.id=d.user_id ORDER BY d.id DESC").fetchall()
  count=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]; dc=c.execute("SELECT COUNT(*) FROM drawings").fetchone()[0]
 rows="".join(f'<tr><td>{u["name"]}</td><td>{u["email"]}</td><td>{u["role"]}</td></tr>' for u in users)
 lessons="".join(f'<tr><td>{d["title"]}</td><td>{d["name"]}</td><td>{d["created"][:10]}</td></tr>' for d in drawings)
 return page(f'<div class="head"><div class="eyebrow">CONTROL CENTER</div><h1>Admin dashboard</h1><p><a class="btn" href="/admin/messages">View Contact Messages</a> <a class="btn" href="/admin/projects">Manage Projects</a></p></div><div class="grid"><div class="card"><div class="stat">{count}</div>Registered users</div><div class="card"><div class="stat">{dc}</div>Saved lessons</div></div><section class="card"><h2>Users</h2><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>{rows}</table></section><section class="card"><h2>Drawing activity</h2><table><tr><th>Lesson</th><th>User</th><th>Date</th></tr>{lessons}</table></section>')
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
