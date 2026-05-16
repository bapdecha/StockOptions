from flask import Flask, render_template, request
from math import floor, exp, log, sqrt, pi
import time
from pymongo import MongoClient
import os

app = Flask(__name__)

def get_database():
	client = MongoClient(os.environ["MONGO_URI"])
	return client[os.environ["MONGO_DB"]]

@app.get("/")
def form():
	return render_template("index.html")

@app.get("/simu")
def simu():
	return render_template("simu.html")

def parse(L):
	dst = time.mktime((int(L[0]), int(L[1]), int(L[2]), 23, 59, 59, 0, 1, -1))
	now = time.time()
	diff = dst - now
	if diff < 0:
		return 1
	return diff / 86400

def norm(x):
	return 1/sqrt(2*pi)*exp(-(x**2)/2)

def inte(fn, a, b):
	dx = 0.001
	i = a
	sum = 0
	while i < b:
		sum += fn(i+dx/2) * dx
		i = float(format(i+dx, '.3f'))
	return sum

def calc_prime(S, K, fn, r, t, sigma):
	dx = 0.01
	d1 = (log(S/K) + (r + sigma*sigma/2)*t) / (sigma*sqrt(t))
	d2 = d1 - sigma*sqrt(t)
	return S*fn(norm, -100, d1) - K*exp(-r*t)*fn(norm, -100, d2), -S*fn(norm, -100, -d1) + K*exp(-r*t)*fn(norm, -100, -d2)

def calc_greeks(S, K, fn, r, t, sigma):
	d1 = (log(S/K) + (r + sigma*sigma/2)*t) / (sigma*sqrt(t))
	d2 = d1 - sigma*sqrt(t)
	delta_call = fn(norm, -100, d1)
	delta_put = fn(norm, -100, d1) - 1
	gamma = norm(d1) / (S*sigma*sqrt(t))
	theta_call = -S * norm(d1) * sigma / (2*sqrt(t)) - r*K*exp(-r*t)*fn(norm, -100, d2)
	theta_put = -S * norm(d1) * sigma / (2*sqrt(t)) + r*K*exp(-r*t)*fn(norm, -100, -d2)
	rho_call = K*t*exp(-r*t)*fn(norm, -100, d2)
	rho_put = -K*t*exp(-r*t)*fn(norm, -100, -d2)
	vega = S*norm(d1)*sqrt(t)
	return { 'delta_call': delta_call, 'delta_put': delta_put, 'gamma': gamma, 'theta_call': theta_call, 'theta_put': theta_put, 'rho_call': rho_call, 'rho_put': rho_put, 'vega': vega }

@app.post("/simu")
def ans():
	action = float(request.form["action"])
	exercice = float(request.form["exercice"])
	taille = int(request.form["taille"])
	nb = int(request.form["nb"])
	inf = int(request.form["inf"])
	sup = int(request.form["sup"])
	taux = float(request.form["taux"]) / 100
	vol = float(request.form["vol"]) / 100
	name_db = str(request.form["name"])
	date = parse(request.form["terme"].split("-")) / 365
	prime = calc_prime(action, exercice, inte, taux, date, vol)
	values = [{ 'prix': 0, 'call': 0, 'pfc': 0, 'pfp': 0, 'put': 0 } for i in range(sup-inf+1)]
	greeks = calc_greeks(action, exercice, inte, taux, date, vol)
	f = open("static/csv.csv", "w")
	for i in range(sup-inf+1):
		values[i]['prix'] = inf+i #cours de l'action
		values[i]['call'] = nb * (taille * (max(0, (inf+i) - exercice) - prime[0])) // 1
		values[i]['pfc'] = (inf+i) * taille * nb + values[i]['call']
		values[i]['put'] = nb * (taille * (max(0, exercice - (inf+i)) - prime[1])) // 1
		values[i]['pfp'] = (inf+i) * taille * nb + values[i]['put']
		s = str(values[i]['prix']) + ";" + str(values[i]['call']) + ";"
		s += str(values[i]['pfc']) + ";" + str(values[i]['put']) + ";"
		s += str(values[i]['pfp']) + "\n"
		if f:
			f.write(s)
	f.close()
	os.system("python3 plot.py")
	message = ""
	try:
		if name_db != "":
			db = get_database()
			if "names" not in db.list_collection_names():
				db["names"].insert_one({
					"name": name_db
				})
			if name_db in db.list_collection_names():
				raise Exception("Collection already exists")
			collection = db[name_db]
			collection.insert_many([{
				"prix": values[i]['prix'],
				"call": values[i]['call'],
				"pfc": values[i]['pfc'],
				"put": values[i]['put'],
				"pfp": values[i]['pfp']} for i in range(sup-inf+1)])
	except Exception as e:
		message = "Erreur : la collection " + name_db + " existe déjà"
	return render_template("simu.html", values=values, exercice=exercice, action=action, prime=prime, message=message, greeks=greeks)

@app.get("/opt")
def opt():
	return render_template("opt.html")

@app.get("/obli")
def obli():
	return render_template("obli.html")

def calc_cc(c, p):
	pm = int(p[1])
	pj = int(p[2])
	cm = int(c[1])
	cj = int(c[2])
	jc = (cm - 1) * 30 + min(30, cj)
	jp = (pm - 1) * 30 + min(30, pj)
	if jc < jp:
		return jc - jp
	elif jc >= jp:
		return 360 - (jc - jp)

@app.post("/obli")
def calc_obli():
	cours = float(request.form['obli'])
	ech = request.form['echeance'].split('-')
	coupon = float(request.form['coupon'])
	nominal = float(request.form['nom']) * int(request.form['nb'])
	c_verse = coupon * nominal / 100
	date_c = request.form['date'].split('-')
	pres = request.form['present'].split('-')
	cc = calc_cc(date_c, pres) / 360 * c_verse
	cce = (int(ech[0]) - int(date_c[0]) + 1) * c_verse + (100 - cours) * nominal / 100 + nominal
	roi = (cce / (cours * nominal / 100) - 1) * 100
	return render_template("obli.html", cours=cours, coupon=c_verse, cc=cc, cce=cce, roi=roi)

@app.get("/db")
def get_db():
	db = get_database()
	names = db["names"].find()
	li = [name["name"] for name in names]
	return render_template("db.html", names=li)

@app.post("/db")
def post_db():
	db = get_database()
	collection = db[request.form['elt']]
	values = collection.find()
	li = [value for value in values]
	return render_template("db.html", values=li)

@app.get("/strat")
def get_strat():
	return render_template("strat.html")

def choose_prime(S, K, fn, r, t, sigma, strat, K2=0, K3=0, K4=0):
	if strat == "call" or strat == "put" or strat == "straddle":
		return calc_prime(S, K, fn, r, t, sigma)
	elif strat == "strangle":
		return calc_prime(S, K, fn, r, t, sigma)[1], calc_prime(S, K2, fn, r, t, sigma)[0]
	elif strat == "butterfly":
		return calc_prime(S, K, fn, r, t, sigma)[0], calc_prime(S, K2, fn, r, t, sigma)[0], calc_prime(S, K3, fn, r, t, sigma)[0]
	else:
		return calc_prime(S, K, fn, r, t, sigma)[1], calc_prime(S, K2, fn, r, t, sigma)[1], calc_prime(S, K3, fn, r, t, sigma)[0], calc_prime(S, K4, fn, r, t, sigma)[0]

def curve_prime(K, fn, r, t, sigma, inf, sup):
	values = [{ "sj": 0, "prime": 0 } for i in range(100*(sup-inf+1))]
	for i in range(sup-inf+1):
		values[i]["sj"] = inf+i
		values[i]["prime"] = calc_prime(inf+i, K, fn, r, t, sigma)[0]
	return values

@app.post("/strat")
def post_strat():
	sj = int(request.form["sous-jacent"])
	taille = int(request.form["taille"])
	nb = int(request.form["nb"])
	inf = int(request.form["inf"])
	sup = int(request.form["sup"])
	taux = float(request.form["taux"]) / 100
	vol = float(request.form["vol"]) / 100
	date = parse(request.form["terme"].split("-")) / 365
	strat = str(request.form["type"])
	sens = str(request.form["sens"])
	strike1 = int(request.form["exercice"])
	try:
		strike2 = int(request.form["exercice2"])
	except:
		strike2 = None
	try:
		strike3 = int(request.form["exercice3"])
	except:
		strike3 = None
	try:
		strike4 = int(request.form["exercice4"])
	except:
		strike4 = None
	if strike4:
		prime = choose_prime(sj, strike1, inte, taux, date, vol, strat, K2=strike2, K3=strike3, K4=strike4)
	elif strike3:
		prime = choose_prime(sj, strike1, inte, taux, date, vol, strat, K2=strike2, K3=strike3)
	elif strike2:
		prime = choose_prime(sj, strike1, inte, taux, date, vol, strat, K2=strike2)
	else:
		prime = choose_prime(sj, strike1, inte, taux, date, vol, strat)
		primes = curve_prime(strike1, inte, taux, date, vol, inf, sup)
	values = [{'sj': 0, 'vi': 0} for i in range(sup - inf + 1)]
	f = open("static/strat/csv.csv", "w")
	g = open("static/strat/primes.csv", "w")
	for i in range(len(primes)):
		s = str(primes[i]["sj"]) + ";" + str(primes[i]["prime"]) + "\n"
		g.write(s)
	g.close()
	for i in range(sup - inf + 1):
		values[i]['sj'] = inf + i
		if strat == "call":
			values[i]['vi'] = nb * taille * (max(0, inf+i - strike1) - prime[0]) // 1
		elif strat == "put":
			values[i]['vi'] = nb * taille * (max(0, strike1 - (inf+i)) - prime[1]) // 1
		elif strat == "straddle":
			values[i]['vi'] = nb * taille * ((max(0, inf+i - strike1) - prime[0]) + (max(0, strike1 - (inf+i)) - prime[1])) // 1
		elif strat == "strangle":
			values[i]['vi'] = nb * taille * ((max(0, inf+i - strike2) - prime[0]) + (max(0, strike1 - (inf+i)) - prime[1])) // 1
		elif strat == "butterfly":
			values[i]['vi'] = nb * taille * ((max(0, inf+i - strike1) - prime[0]) + (max(0, inf+i - strike3) - prime[2]) - 2 * (max(0, inf+i - strike2) - prime[1])) // 1
		else:
			values[i]['vi'] = nb * taille * ((max(0, strike1 - (inf+i)) - prime[0]) + (max(0, inf+i - strike4) - prime[3]) - (max(0, strike2 - (inf+i)) - prime[1]) - (max(0, inf+i - strike3) - prime[2])) // 1
		if sens == "vente":
			values[i]['vi'] = -values[i]['vi']
		s = str(values[i]['sj']) + ";" + str(values[i]['vi']) + "\n"
		if f:
			f.write(s)
	f.close()
	os.system("../.venv/bin/python3 plot.py strat "+strat+" "+sens)
	return render_template("strat.html", prime=prime)

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8000)