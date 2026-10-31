import os, sqlite3, urllib.parse, urllib.request
from pathlib import Path
from flask import Blueprint, request, redirect, url_for, flash, render_template_string, session
from functools import wraps
from datetime import datetime

extras = Blueprint("extras", __name__)
DB = Path(__file__).resolve().parent / "studio.db"

DEFAULT_PROJECTS = [
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
 c.execute("DELETE FROM projects WHERE lower(title) LIKE '%one k coffee%' OR lower(url) LIKE '%one-kcoffee%'")
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
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@600;700;800&display=swap');
:root{--bg:#1b100a;--panel:#2b1a10;--gold:#d7a13d;--gold2:#f0c66d;--cream:#f7efe1;--muted:#b9a894;--line:#63472d}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--cream);font:15px 'DM Sans',Arial,sans-serif}
nav{position:sticky;top:0;z-index:1000;padding:17px 5%;background:rgba(27,16,10,.97);backdrop-filter:blur(15px);border-bottom:1px solid #ffffff18;display:flex;gap:24px;align-items:center;flex-wrap:wrap}
nav a{color:#e7d9c7;text-decoration:none;font-weight:700}nav a:hover{color:var(--gold2)}.extra-brand{font-size:19px;color:var(--cream)!important;white-space:nowrap}.extra-links{display:flex;align-items:center;gap:22px;margin-left:auto}.extra-toggle{display:none;background:transparent;border:1px solid #80613d;color:var(--cream);width:44px;height:42px;border-radius:10px;font-size:24px}
.wrap{max-width:1000px;margin:35px auto;padding:0 18px 60px}h1{font:800 clamp(36px,6vw,54px) 'Playfair Display',serif;color:var(--cream)}h2,h3{color:var(--cream)}
.card{background:linear-gradient(145deg,#302014,#24150d);border:1px solid #60452b;border-radius:22px;padding:24px;margin:16px 0;box-shadow:0 12px 35px #0003}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:15px}
.field{display:block;margin:15px 0;font-weight:700;color:#eadcc9}.field input,.field textarea,.field select{display:block;width:100%;padding:14px;margin-top:8px;border:1px solid #684a2e;border-radius:12px;box-sizing:border-box;background:#1d120c;color:#fff8ec;font:inherit}.field input:focus,.field textarea:focus{outline:0;border-color:var(--gold);box-shadow:0 0 0 3px #d7a13d22}
.btn{background:linear-gradient(110deg,var(--gold),var(--gold2));color:#251509!important;padding:13px 20px;border:0;border-radius:30px;cursor:pointer;text-decoration:none;display:inline-block;font-weight:800}
.muted{color:var(--muted)}.msg{padding:12px;background:#48271b;color:#ffcfad;border-radius:9px}
table{width:100%;border-collapse:collapse}td,th{text-align:left;padding:10px;border-bottom:1px solid #5b4029;overflow-wrap:anywhere}th{color:var(--gold2)}
a{color:var(--gold2)}footer{text-align:center;color:#a9957e;padding:25px;border-top:1px solid #60452b;background:#170d08}
@media(max-width:760px){nav{gap:12px;padding:13px 5%;justify-content:space-between}.extra-toggle{display:block}.extra-links{display:none;position:absolute;top:100%;left:0;right:0;margin:0;background:#1b100a;border-bottom:1px solid #684a2e;padding:20px 7% 28px;flex-direction:column;align-items:stretch;gap:0}.extra-links.open{display:flex}.extra-links a{padding:14px 0;border-bottom:1px solid #ffffff12;font-size:17px}.wrap{margin:24px auto;padding:0 14px 45px}.card{padding:19px}table{font-size:12px}td,th{padding:8px}}
</style></head><body><nav><a class="extra-brand" href="/">✦ Amir Ali Projects</a><button class="extra-toggle" type="button" aria-label="Open menu" onclick="document.getElementById('extra-links').classList.toggle('open')">☰</button><div class="extra-links" id="extra-links"><a href="/">Home</a><a href="/chat">AI Chat</a><a href="/contact">Contact</a><a href="/about">About & Projects</a>{% if session.get('uid') %}<a href="/studio">AI Drawing Studio</a>{% endif %}{% if session.get('role')=='admin' %}<a href="/admin">Admin</a><a href="/admin/messages">Messages</a><a href="/admin/projects">Manage Projects</a>{% endif %}</div></nav><main class="wrap">{% with ms=get_flashed_messages() %}{% for m in ms %}<p class="msg">{{m}}</p>{% endfor %}{% endwith %}{{ body|safe }}</main><footer>AI Drawing Studio · Amir Ali Projects</footer></body></html>
"""
def render(title, body, **context):
 return render_template_string(SHELL, title=title, body=render_template_string(body, **context))

@extras.route("/about")
def about():
 with db() as c: projects=c.execute("SELECT * FROM projects WHERE lower(title) NOT LIKE '%one k coffee%' AND lower(url) NOT LIKE '%one-kcoffee%' ORDER BY id DESC").fetchall()
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
   # Optional instant Telegram notification. Configure these two values in Render Environment.
   bot_token=os.getenv("TELEGRAM_BOT_TOKEN","").strip()
   chat_id=os.getenv("TELEGRAM_CHAT_ID","").strip()
   if bot_token and chat_id:
    text_msg="New website contact message\\nName: "+name+"\\nEmail: "+email+"\\nPhone: "+phone+"\\nMessage: "+message
    try:
     payload=urllib.parse.urlencode({"chat_id":chat_id,"text":text_msg}).encode()
     req=urllib.request.Request("https://api.telegram.org/bot"+bot_token+"/sendMessage",data=payload)
     urllib.request.urlopen(req,timeout=8).read()
    except Exception:
     app.logger.exception("Telegram contact notification failed")
   flash("Ergaan kee galmaa'eera. Yoo Telegram notification qindeessite, achittis siif ergama.")
   return redirect("/contact")
 body="""<h1>Contact Me</h1><section class="card"><p>Gaaffii, yaada ykn hojii waliin hojjechuu yoo barbaadde ergaa naaf ergi.</p><form method="post"><label class="field">Full name<input name="name" required maxlength="100"></label><label class="field">Email<input name="email" type="email"></label><label class="field">Phone number<input name="phone" type="tel"></label><label class="field">Your message<textarea name="message" rows="6" required maxlength="3000"></textarea></label><button class="btn">Send message</button></form></section><section class="card"><b>Phone:</b> <a href="tel:0967757546">0967757546</a><br><b>Telegram:</b> <a href="https://t.me/zayya_an" target="_blank">@zayya_an</a><br><b>TikTok:</b> <a href="https://www.tiktok.com/@zayya_an" target="_blank">@zayya_an</a><br><b>Instagram:</b> <a href="https://www.instagram.com/zayya_an2" target="_blank">@zayya_an2</a></section>"""
 return render("Contact",body)

@extras.route("/chat", methods=["GET","POST"])
def chat():
 if request.method=="POST":
  data=request.get_json(silent=True) or request.form
  question=str(data.get("message","")).strip()
  history=data.get("history",[])
  if not question:
   return ({"error":"Please type a message."},400) if request.is_json else redirect("/chat")
  try:
   from google import genai
   key=os.getenv("GEMINI_API_KEY")
   if not key: raise RuntimeError("AI chatbot is not configured yet.")
   client=genai.Client(api_key=key)
   contents=[]
   for item in history[-16:]:
    role=item.get("role")
    text=item.get("text","")
    if role in ("user","model") and text:
     contents.append({"role":role,"parts":[{"text":str(text)[:4000]}]})
   contents.append({"role":"user","parts":[{"text":question[:4000]}]})
   res=client.models.generate_content(
    model=os.getenv("GEMINI_MODEL","gemini-3.8-flash"),
    contents=contents,
    config={"system_instruction":"You are the helpful AI assistant for Amir Ali Projects and AI Drawing Studio. Answer naturally, clearly and helpfully. Support Afaan Oromoo, Amharic and English; reply in the language the visitor uses. Help with drawing lessons, accounts, the website and projects. Never invent facts. Use readable paragraphs and lists when useful."}
   )
   answer=res.text or "Sorry, I could not create a response. Please try again."
   if request.is_json:
    from flask import jsonify
    return jsonify({"reply":answer})
   return render("AI Chat","<h1>AI Chat</h1><p>{{answer}}</p>",answer=answer)
  except Exception as e:
   message="I could not connect to the AI right now. Please try again in a moment."
   app.logger.exception("AI chat request failed")
   if request.is_json:
    from flask import jsonify
    return jsonify({"error":message}),503
   return render("AI Chat","<h1>AI Chat</h1><p>{{answer}}</p>",answer=message)

 body="""<style>
.chat-shell{height:min(72vh,760px);min-height:520px;display:flex;flex-direction:column;background:#24150d;border:1px solid #60452b;border-radius:20px;overflow:hidden;box-shadow:0 12px 40px #0005}
.chat-top{padding:15px 18px;border-bottom:1px solid #60452b;display:flex;align-items:center;justify-content:space-between;gap:10px}
.chat-brand{font-weight:700;color:#f7efe1}.chat-sub{font-size:12px;color:#b9a894;margin-top:3px}
.chat-clear{border:1px solid #684a2e;background:#1b100a;border-radius:9px;padding:8px 11px;color:#f0c66d;cursor:pointer}
.chat-scroll{flex:1;overflow-y:auto;padding:22px 16px;display:flex;flex-direction:column;gap:22px}
.chat-welcome{margin:auto;text-align:center;max-width:500px;padding:20px 10px}.chat-welcome h2{font-size:27px;color:#273328;margin:0 0 9px}.chat-welcome p{color:#b9a894;line-height:1.6}
.chat-suggestions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px;margin-top:22px}
.chat-suggestions button{background:#352214;border:1px solid #684a2e;border-radius:12px;padding:12px;text-align:left;color:#f0c66d;cursor:pointer}
.chat-row{display:flex;gap:10px;align-items:flex-start;max-width:88%}.chat-row.user{align-self:flex-end;flex-direction:row-reverse}
.chat-avatar{width:30px;height:30px;flex:0 0 30px;border-radius:50%;display:grid;place-items:center;background:#526b4d;color:white;font-size:13px;font-weight:bold}
.chat-row.user .chat-avatar{background:#d7a13d;color:#28170d}
.chat-bubble{padding:12px 15px;border-radius:16px;background:#3a291b;color:#fff4e2;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}
.chat-row.user .chat-bubble{background:#d7a13d;color:#251509;border-bottom-right-radius:5px}
.chat-row.assistant .chat-bubble{border-bottom-left-radius:5px}
.chat-compose{border-top:1px solid #60452b;padding:13px 14px 15px;background:#24150d}
.chat-form{display:flex;align-items:flex-end;gap:9px;border:1px solid #684a2e;border-radius:17px;padding:8px 9px 8px 14px;box-shadow:0 3px 12px #0003;background:#1b100a}
.chat-form textarea{flex:1;resize:none;border:0;outline:0;font:15px Arial;line-height:1.5;max-height:130px;min-height:28px;padding:6px 0;color:#fff4e2;background:transparent}
.chat-send{width:42px;height:42px;border:0;border-radius:12px;background:linear-gradient(110deg,#d7a13d,#f0c66d);color:#251509;font-size:20px;cursor:pointer}
.chat-send:disabled{opacity:.5;cursor:default}.chat-hint{text-align:center;color:#a9957e;font-size:11px;margin:8px 0 0}
.chat-typing{color:#777;font-size:13px;padding:4px 0}
@media(max-width:600px){.chat-shell{height:calc(100dvh - 250px);min-height:440px;border-radius:14px}.chat-scroll{padding:16px 11px}.chat-row{max-width:96%}.chat-suggestions{grid-template-columns:1fr}.chat-compose{padding:10px}}
</style>
<h1 style="margin-bottom:8px">AI Chat</h1>
<p style="color:#777;margin-top:0;margin-bottom:18px">Chat with your AI assistant. Afaan Oromoo, Amharic and English are supported.</p>
<section class="chat-shell">
 <div class="chat-top"><div><div class="chat-brand">✦ Amir AI</div><div class="chat-sub">AI assistant · Ready to help</div></div><button class="chat-clear" id="chat-clear" type="button">New chat</button></div>
 <div class="chat-scroll" id="chat-scroll" aria-live="polite">
  <div class="chat-welcome" id="chat-welcome"><h2>What can I help you with?</h2><p>Ask a question, get help with drawing, or explore Amir Ali's projects.</p>
   <div class="chat-suggestions"><button type="button">Teach me how to draw a face</button><button type="button">Help me with my AI Drawing Studio account</button><button type="button">What projects has Amir Ali built?</button><button type="button">Akkamitti suuraa kaasuu baradha?</button></div>
  </div>
 </div>
 <div class="chat-compose"><form class="chat-form" id="chat-form"><textarea id="chat-input" rows="1" maxlength="2000" placeholder="Message Amir AI..." aria-label="Your message" required></textarea><button class="chat-send" id="chat-send" type="submit" aria-label="Send message">↑</button></form><div class="chat-hint">AI can make mistakes. Check important information.</div></div>
</section>
<script>
(()=>{
 const form=document.getElementById('chat-form'),input=document.getElementById('chat-input'),scroll=document.getElementById('chat-scroll'),send=document.getElementById('chat-send'),welcome=document.getElementById('chat-welcome'),clear=document.getElementById('chat-clear');
 let history=[];
 const add=(role,text)=>{
  if(welcome) welcome.remove();
  const row=document.createElement('div');row.className='chat-row '+(role==='user'?'user':'assistant');
  const avatar=document.createElement('div');avatar.className='chat-avatar';avatar.textContent=role==='user'?'Y':'✦';
  const bubble=document.createElement('div');bubble.className='chat-bubble';bubble.textContent=text;
  row.append(avatar,bubble);scroll.append(row);scroll.scrollTop=scroll.scrollHeight;return row;
 };
 const resize=()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,130)+'px'};
 input.addEventListener('input',resize);
 input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();form.requestSubmit()}});
 document.querySelectorAll('.chat-suggestions button').forEach(b=>b.addEventListener('click',()=>{input.value=b.textContent;form.requestSubmit()}));
 form.addEventListener('submit',async e=>{
  e.preventDefault();const message=input.value.trim();if(!message||send.disabled)return;
  add('user',message);history.push({role:'user',text:message});input.value='';resize();send.disabled=true;
  const typing=add('assistant','Thinking…');
  try{
   const response=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,history:history.slice(0,-1)})});
   const data=await response.json();typing.remove();
   if(!response.ok)throw new Error(data.error||'Request failed');
   add('assistant',data.reply);history.push({role:'model',text:data.reply});
  }catch(err){typing.remove();add('assistant',err.message||'Connection error. Please try again.');history.pop();}
  finally{send.disabled=false;input.focus()}
 });
 clear.addEventListener('click',()=>{history=[];scroll.innerHTML='<div class="chat-welcome" id="chat-welcome"><h2>What can I help you with?</h2><p>Ask a question, get help with drawing, or explore Amir Ali\'s projects.</p><div class="chat-suggestions"><button type="button">Teach me how to draw a face</button><button type="button">Help me with my AI Drawing Studio account</button><button type="button">What projects has Amir Ali built?</button><button type="button">Akkamitti suuraa kaasuu baradha?</button></div></div>';scroll.querySelectorAll('.chat-suggestions button').forEach(b=>b.addEventListener('click',()=>{input.value=b.textContent;form.requestSubmit()}));input.focus()});
 input.focus();
})();
</script>"""
 return render("AI Chat",body)

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
