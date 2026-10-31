import os, sqlite3
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, flash, render_template_string, session
from functools import wraps
from datetime import datetime

extras = Blueprint("extras", __name__)
DB = Path(__file__).resolve().parent / "studio.db"

DEFAULT_PROJECTS = [
 ("One K Coffee","https://one-kcoffee.et"),
 ("Haile Kirar","https://hailekirar.base44.app"),
 ("Black Barber Shop","https://black-barber-shop.youware.app"),
 ("Bashasha Secondary School","https://bashashascodaryschool.base44.app"),
 ("Ethio AI","https://ethioai.base44.app"),
 ("Unity Park","https://unitypark.base44.app"),
]
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
with db() as c:
 c.execute("""CREATE TABLE IF NOT EXISTS contact_messages(
 id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT,phone TEXT,message TEXT NOT NULL,created TEXT,status TEXT DEFAULT 'New')""")
 c.execute("""CREATE TABLE IF NOT EXISTS projects(
 id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT NOT NULL,url TEXT NOT NULL,created TEXT)""")
 if c.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
  c.executemany("INSERT INTO projects(title,url,created) VALUES(?,?,?)",
    [(n,u,datetime.utcnow().isoformat()) for n,u in DEFAULT_PROJECTS])

def admin_required(fn):
 @wraps(fn)
 def wrapped(*a,**k):
  if not session.get("uid") or session.get("role") != "admin":
   return redirect("/login")
  return fn(*a,**k)
 return wrapped

SHELL = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title }}</title>
<style>
body{margin:0;background:#faf9f5;color:#242920;font:15px Arial,sans-serif}nav{padding:18px 6%;background:white;border-bottom:1px solid #e8e7df;display:flex;gap:18px;flex-wrap:wrap}nav a{color:#526b4d;text-decoration:none;font-weight:bold}.wrap{max-width:1000px;margin:35px auto;padding:0 18px 60px}h1{font-size:38px;color:#526b4d}.card{background:white;border:1px solid #e8e7df;border-radius:16px;padding:22px;margin:16px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:15px}.field{display:block;margin:13px 0;font-weight:bold}.field input,.field textarea{display:block;width:100%;padding:12px;margin-top:7px;border:1px solid #ddd;border-radius:9px;box-sizing:border-box}.btn{background:#526b4d;color:white;padding:12px 18px;border:0;border-radius:9px;cursor:pointer;text-decoration:none;display:inline-block}.muted{color:#777}.msg{padding:12px;background:#fff0ec;border-radius:9px}table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #eee;overflow-wrap:anywhere}a{color:#526b4d}footer{text-align:center;color:#777;padding:20px}@media(max-width:600px){h1{font-size:30px}}
</style></head><body><nav><a href="/">AI Drawing Studio</a><a href="/chat">AI Chat</a><a href="/contact">Contact</a><a href="/about">About & Projects</a>{% if session.get('role')=='admin' %}<a href="/admin">Admin</a><a href="/admin/projects">Manage Projects</a><a href="/admin/messages">Messages</a>{% endif %}</nav><main class="wrap">{% with ms=get_flashed_messages() %}{% for m in ms %}<p class="msg">{{m}}</p>{% endfor %}{% endwith %}{{ body|safe }}</main><footer>AI Drawing Studio · Amir Ali Projects</footer></body></html>
"""
def render(title, body, **context):
 return render_template_string(SHELL, title=title, body=render_template_string(body, **context))

@extras.route("/about")
def about():
 with db() as c: projects=c.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
 body = """<h1>About Amir Ali</h1><section class="card"><p>Welcome! I am Amir Ali, a developer and creator building useful digital projects, websites and AI-powered tools.</p><p>Explore my projects below. Select any project to open its website.</p><p><b>Phone:</b> <a href="tel:0967757546">0967757546</a> &nbsp; <b>Telegram:</b> <a href="https://t.me/zayya_an" target="_blank" rel="noopener">@zayya_an</a></p><p><b>TikTok:</b> <a href="https://www.tiktok.com/@zayya_an" target="_blank" rel="noopener">@zayya_an</a> &nbsp; <b>Instagram:</b> <a href="https://www.instagram.com/zayya_an2" target="_blank" rel="noopener">@zayya_an2</a></p></section><h2>My Projects</h2><div class="grid">{% for p in projects %}<article class="card"><h3>{{p.title}}</h3><a class="btn" href="{{p.url}}" target="_blank" rel="noopener">Open project ↗</a><p class="muted">{{p.url}}</p></article>{% endfor %}</div>"""
 return render("About Amir Ali",body,projects=projects)

@extras.route("/contact", methods=["GET","POST"])
def contact():
 if request.method=="POST":
  name=request.form.get("name","").strip(); email=request.form.get("email","").strip(); phone=request.form.get("phone","").strip(); message=request.form.get("message","").strip()
  if not name or not message:
   flash("Maqaa fi ergaa guuti.")
  else:
   with db() as c:c.execute("INSERT INTO contact_messages(name,email,phone,message,created) VALUES(?,?,?,?,?)",(name,email,phone,message,datetime.utcnow().isoformat()))
   flash("Ergaan kee nu gaheera. Galatoomi!")
   return redirect("/contact")
 body="""<h1>Contact Me</h1><section class="card"><p>Gaaffii, yaada ykn hojii waliin hojjechuu yoo barbaadde ergaa naaf ergi.</p><form method="post"><label class="field">Full name<input name="name" required maxlength="100"></label><label class="field">Email<input name="email" type="email"></label><label class="field">Phone number<input name="phone" type="tel"></label><label class="field">Your message<textarea name="message" rows="6" required maxlength="3000"></textarea></label><button class="btn">Send message</button></form></section><section class="card"><b>Phone:</b> <a href="tel:0967757546">0967757546</a><br><b>Telegram:</b> <a href="https://t.me/zayya_an" target="_blank">@zayya_an</a><br><b>TikTok:</b> <a href="https://www.tiktok.com/@zayya_an" target="_blank">@zayya_an</a><br><b>Instagram:</b> <a href="https://www.instagram.com/zayya_an2" target="_blank">@zayya_an2</a></section>"""
 return render("Contact",body)

@extras.route("/chat", methods=["GET","POST"])
def chat():
 answer=None
 if request.method=="POST":
  question=request.form.get("message","").strip()
  if question:
   try:
    from google import genai
    key=os.getenv("GEMINI_API_KEY")
    if not key: raise RuntimeError("AI chatbot is not configured yet.")
    client=genai.Client(api_key=key)
    res=client.models.generate_content(model=os.getenv("GEMINI_MODEL","gemini-3.8-flash"),contents="You are the helpful AI Drawing Studio website assistant. Answer clearly and safely. Help visitors with drawing lessons, accounts, projects and contact information. If you do not know, say so.\nVisitor: "+question)
    answer=res.text
   except Exception as e: answer="Chatbot error: "+str(e)
 body="""<h1>AI Chat Assistant</h1><section class="card"><p>Gaaffii kee barreessi; chatbot website kanaa si gargaara.</p><form method="post"><label class="field">Your message<textarea name="message" rows="4" maxlength="2000" required></textarea></label><button class="btn">Send to AI</button></form>{% if answer %}<hr><h3>AI Assistant</h3><p style="white-space:pre-wrap">{{answer}}</p>{% endif %}</section>"""
 return render("AI Chat",body,answer=answer)

@extras.route("/admin/projects", methods=["GET","POST"])
@admin_required
def manage_projects():
 if request.method=="POST":
  title=request.form.get("title","").strip(); url=request.form.get("url","").strip()
  if title and url.startswith(("https://","http://")):
   with db() as c:c.execute("INSERT INTO projects(title,url,created) VALUES(?,?,?)",(title,url,datetime.utcnow().isoformat()))
   flash("Project added.")
  else: flash("Maqaa fi linkii sirrii (https://) galchi.")
  return redirect("/admin/projects")
 with db() as c: projects=c.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
 body="""<h1>Manage Projects</h1><section class="card"><h3>Add a new project</h3><form method="post"><label class="field">Project name<input name="title" required></label><label class="field">Project URL<input name="url" type="url" placeholder="https://" required></label><button class="btn">Add project</button></form></section><section class="card"><h3>Current projects</h3><table><tr><th>Project</th><th>Link</th><th>Action</th></tr>{% for p in projects %}<tr><td>{{p.title}}</td><td><a href="{{p.url}}" target="_blank" rel="noopener">{{p.url}}</a></td><td><form method="post" action="/admin/projects/delete/{{p.id}}" onsubmit="return confirm('Delete this project?')"><button class="btn">Delete</button></form></td></tr>{% endfor %}</table></section>"""
 return render("Manage Projects",body,projects=projects)

@extras.route("/admin/projects/delete/<int:pid>",methods=["POST"])
@admin_required
def delete_project(pid):
 with db() as c:c.execute("DELETE FROM projects WHERE id=?",(pid,))
 flash("Project deleted."); return redirect("/admin/projects")

@extras.route("/admin/messages")
@admin_required
def messages():
 with db() as c: rows=c.execute("SELECT * FROM contact_messages ORDER BY id DESC").fetchall()
 body="""<h1>Contact Messages</h1><section class="card"><table><tr><th>Name</th><th>Contact</th><th>Message</th><th>Date</th></tr>{% for m in rows %}<tr><td>{{m.name}}</td><td>{{m.email}}<br>{{m.phone}}</td><td>{{m.message}}</td><td>{{m.created[:16]}}</td></tr>{% else %}<tr><td colspan="4">No messages yet.</td></tr>{% endfor %}</table></section>"""
 return render("Contact Messages",body,rows=rows)
