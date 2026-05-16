#! /usr/bin/python3

import matplotlib.pyplot as plt
import sys

def plot(opt_type, values, st_type="", st_sens="", primes=[]):
    payoff = [values[i][opt_type] for i in range(len(values))]
    S0 = [values[i]['prix'] for i in range(len(values))]
    px = [primes[i]['prix'] for i in range(len(primes))]
    py = [primes[i]['prime'] for i in range(len(primes))]
    plt.figure(figsize=(20,10))
    plt.plot(px, py, label='Prime')
    plt.plot(S0, payoff, label='Payoff')
    if opt_type == "put" or (st_sens == "achat" and st_type in ["put", "straddle", "stangle"]) or (st_sens == "vente" and st_type not in ["put", "straddle", "strangle"]):
        plt.gca().invert_yaxis()
    plt.xlabel("Sous-jacent")
    plt.ylabel("Payoff")
    plt.title("Payoff de l'option")
    plt.legend()
    plt.grid(True)
    plt.savefig("static/"+opt_type+".png")

def generate_values():
    f = open("static/csv.csv", 'r')
    lines = f.readlines()
    values = [{ 'prix': 0, 'call': 0, 'put': 0 } for i in range(len(lines))]
    for i in range(len(lines)):
        L = lines[i].split("\n")[0].split(";")
        values[i]['prix'] = L[0]
        values[i]['call'] = L[1]
        values[i]['put'] = L[3]
    plot('call', values)
    plot('put', values)

def generate_values_strat(st_type, st_sens):
    f = open("static/strat/csv.csv", 'r')
    lines = f.readlines()
    n = len(lines)
    values = [{ 'prix': 0, 'vi': 0 } for i in range(n)]
    for i in range(n):
        L = lines[i].split("\n")[0].split(";")
        values[i]['prix'] = L[0]
        values[i]['vi'] = L[1]
    f.close()
    g = open("static/strat/primes.csv")
    lines = g.readlines()
    n = len(lines)
    primes = [{ 'prix': 0, 'prime': 0} for i in range(n)]
    for i in range(n):
        L = lines[i].split("\n")[0].split(";")
        primes[i]['prix'] = L[0]
        primes[i]['prime'] = L[1]
    g.close()
    plot('vi', values, st_type, st_sens, primes=primes)

if len(sys.argv) == 4 and sys.argv[1] == "strat":
    generate_values_strat(sys.argv[2], sys.argv[3])
else:
    generate_values()