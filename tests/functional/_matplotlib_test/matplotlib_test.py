import os

import matplotlib as mpl

mpl.use("Agg")

import matplotlib.pyplot as plt

if __name__ == "__main__":
    fig, ax = plt.subplots()
    ax.plot(range(10))
    fig.savefig("test.png", format="png")

assert os.path.exists("test.png")
