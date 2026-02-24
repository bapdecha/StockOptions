#! /usr/bin/python3

import matplotlib.pyplot as plt

def plot(opt_type, values):
    payoff = [values[i][opt_type] for i in range(len(values))]
    S0 = [values[i]['prix'] for i in range(len(values))]
    plt.figure(figsize=(20,10))
    plt.plot(S0, payoff, label='Payoff')
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

generate_values()