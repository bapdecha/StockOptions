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
	return render_template("simu.html", values=values, exercice=exercice, action=action, prime=prime, message=message)

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

if __name__ == '__main__':
	app.run(host="0.0.0.0", port=8000)