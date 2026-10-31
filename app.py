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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600;700&family=Playfair+Display:wght@600;700&display=swap');
:root{--g:#526b4d;--ink:#242920;--muted:#777d72;--gold:#d8b86a;--line:#e8e7df}*{box-sizing:border-box}body{margin:0;background:#faf9f5;color:var(--ink);font:15px 'DM Sans',sans-serif}.nav{padding:20px 6%;display:flex;justify-content:space-between;background:white;border-bottom:1px solid var(--line);align-items:center}.brand{font-weight:700;color:var(--g);text-decoration:none;font-size:19px}.nav a{color:var(--g);text-decoration:none;margin-left:17px}.wrap{max-width:1080px;margin:auto;padding:38px 22px 70px}.hero{display:grid;grid-template-columns:1fr 1fr;gap:45px;align-items:center;min-height:520px}.eyebrow{color:var(--g);font-size:11px;letter-spacing:2px;font-weight:bold}.hero h1{font:700 clamp(40px,5vw,62px)/1.08 'Playfair Display';margin:20px 0}.hero h1 em{color:var(--g)}p{color:var(--muted);line-height:1.8}.btn{background:var(--g);color:white!important;border:0;padding:14px 22px;border-radius:30px;text-decoration:none;display:inline-block;font-weight:700;cursor:pointer}.card{background:white;border:1px solid var(--line);border-radius:20px;padding:28px;box-shadow:0 8px 25px #20251f08}.mock{height:390px;border-radius:45% 45% 18px 18px;background:#e9e8dd;display:grid;place-items:center}.paper{background:#fff;width:240px;border:8px solid #262b24;border-radius:28px;padding:22px}.face{height:210px;background:#f5f3e9;border-radius:10px;display:grid;place-items:center;font-size:90px;color:#999}.features{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;padding:35px 0}.auth{max-width:440px;margin:30px auto}.auth h1,.head h1{font:700 40px 'Playfair Display'}.field{display:block;margin:16px 0;font-weight:600;font-size:13px}.field input{display:block;width:100%;padding:14px;border:1px solid var(--line);border-radius:10px;margin-top:8px}.full{width:100%}.head{margin:15px 0 28px}.drop{padding:30px;border:1px dashed #9aa995;border-radius:14px;background:#f8f9f5;text-align:center}.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:15px}.stepno{color:var(--g);font-size:11px;font-weight:bold;letter-spacing:2px}.tip{padding:12px;background:#f7f6ef;border-radius:10px;color:#71694f}.flash{background:#fff0ec;color:#9a3c2b;padding:12px;border-radius:10px;margin-bottom:15px}.stat{font-size:32px;font-weight:bold;color:var(--g)}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:12px;border-bottom:1px solid var(--line)}footer{text-align:center;padding:25px;color:var(--muted);font-size:12px;border-top:1px solid var(--line)}@media(max-width:720px){.hero{grid-template-columns:1fr}.features,.grid{grid-template-columns:1fr}.nav{flex-wrap:wrap;gap:12px}.wrap{padding:25px 16px}}
</style>"""
from extras import extras
app.register_blueprint(extras)

def page(body,title="AI Drawing Studio"):
 return render_template_string("""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{title}}</title>"""+STYLE+"""</head><body><nav class="nav"><a class="brand" href="/">✦ AI Drawing Studio</a><div><a href="/chat">AI Chat</a><a href="/contact">Contact</a><a href="/about">About</a>{% if session.get('uid') %}<a href="/studio">Create</a><a href="/drawings">My drawings</a>{% if session.get('role')=='admin' %}<a href="/admin">Admin</a>{% endif %}<a href="/logout">Log out</a>{% else %}<a href="/login">Log in</a><a href="/register">Sign up</a>{% endif %}</div></nav><main class="wrap">{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}{% endwith %}"""+body+"""</main><footer>AI Drawing Studio · Learn to draw, one step at a time</footer></body></html>""",title=title)

@app.route("/")
def home():
 return page("""<section class="hero"><div><div class="eyebrow">✦ YOUR PERSONAL DRAWING COACH</div><h1>Turn any portrait into a <em>step-by-step</em> drawing lesson.</h1><p>Upload a portrait and receive a beginner-friendly nine-step guide, from the first shapes to the finishing details. Save your lessons and practice at your own pace.</p><a class="btn" href="/register">Start creating ↗</a> &nbsp; <a href="/login" style="color:var(--g)">I have an account</a><p>✧ AI-assisted guidance · Private saved lessons</p></div><div class="mock"><div class="paper"><small>DRAWING TUTORIAL　2 / 9</small><div class="face">✎</div><b>STEP 2 · CONSTRUCTION</b><p style="font-size:11px">Building your portrait guide…</p></div></div></section><section class="features"><div><b>01 · Upload</b><p>Choose a portrait from your device.</p></div><div><b>02 · Analyze</b><p>AI studies the reference image.</p></div><div><b>03 · Learn</b><p>Follow and save your nine-step lesson.</p></div></section>""")

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
 return page(f'<div class="head"><div class="eyebrow">CONTROL CENTER</div><h1>Admin dashboard</h1></div><div class="grid"><div class="card"><div class="stat">{count}</div>Registered users</div><div class="card"><div class="stat">{dc}</div>Saved lessons</div></div><section class="card"><h2>Users</h2><table><tr><th>Name</th><th>Email</th><th>Role</th></tr>{rows}</table></section><section class="card"><h2>Drawing activity</h2><table><tr><th>Lesson</th><th>User</th><th>Date</th></tr>{lessons}</table></section>')
if __name__=="__main__":app.run(host="0.0.0.0",port=int(os.getenv("PORT","5000")))
