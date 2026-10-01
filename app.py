import os,json
from flask import Flask,render_template,request,redirect,session,jsonify
from urllib.request import Request,urlopen
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from werkzeug.security import check_password_hash
app=Flask(__name__); app.secret_key=os.environ["SECRET_KEY"]
@app.after_request
def no_cache(resp):
 resp.headers["Cache-Control"]="no-store, no-cache, must-revalidate, max-age=0"
 resp.headers["Pragma"]="no-cache"
 resp.headers["Expires"]="0"
 return resp
URL=os.getenv("SDA9_SYNC_URL","https://xynpbdtgamwhayrfkeod.supabase.co/functions/v1/sda9-sync"); TOKEN=os.environ["SDA9_SYNC_TOKEN"]
TZ=ZoneInfo("America/Sao_Paulo")
def brl(v):
 try:
  n=float(v or 0)
  return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
 except (TypeError,ValueError): return "0,00"
app.jinja_env.filters["brl"]=brl
def api(p):
 r=Request(URL,data=json.dumps(p).encode(),headers={"content-type":"application/json","x-sda9-token":TOKEN}); return json.loads(urlopen(r,timeout=20).read())
def bounds(periodo="atual"):
 h=datetime.now(TZ).date()
 ini=h.replace(day=1 if h.day<=15 else 16)
 fim=h.replace(day=15) if h.day<=15 else (h.replace(day=28)+timedelta(days=4)).replace(day=1)-timedelta(days=1)
 if periodo=="anterior":
  if h.day<=15:
   ant=h.replace(day=1)-timedelta(days=1)
   ini=ant.replace(day=16); fim=ant
  else:
   ini=h.replace(day=1); fim=h.replace(day=15)
 return h,ini,fim
@app.route("/",methods=["GET","POST"])
def login():
 if request.method=="POST":
  try:
   d=api({"action":"login","usuario":request.form["usuario"].strip()}); u=d.get("user")
   if u and check_password_hash(u["senha_hash"],request.form["senha"]): session["mid"]=u["motorista_id"];session["nome"]=u["motoristas"]["nome"];return redirect("/portal")
  except Exception: pass
  return render_template("login.html",erro="Usuário ou senha inválidos.")
 return render_template("login.html")
@app.route("/sair")
def sair(): session.clear();return redirect("/")
@app.route("/portal")
def portal():
 if not session.get("mid"):return redirect("/")
 periodo=request.args.get("periodo","atual")
 if periodo not in ("atual","anterior"): periodo="atual"
 h,i,f=bounds(periodo)
 d=api({"action":"resumo","motorista_id":session["mid"],"inicio":i.isoformat(),"fim":f.isoformat()})
 return render_template("portal.html",d=d,hoje=h.isoformat(),nome=session["nome"],periodo=periodo,inicio=i.isoformat(),fim=f.isoformat())
@app.post("/divergencia")
def div():
 if not session.get("mid"):return jsonify(ok=False),403
 b=request.get_json(); return jsonify(api({"action":"divergencia","motorista_id":session["mid"],"data":b["data"],"operacao":b.get("operacao","TOTAL"),"mensagem":b["mensagem"],"snapshot":b.get("snapshot",{})}))
