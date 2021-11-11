import numpy as np
from scipy.optimize import curve_fit

def func(x, a, b, c):
    return a * np.exp(-b * x) + c

np.random.seed(32)
xdata = np.linspace(0, 4, 50)
y = func(xdata, 2.5, 1.3, 0.5)
rng = np.random.default_rng()
y_noise = 0.1 * rng.normal(size=xdata.size)
ydata = y + y_noise

popt, pcov = curve_fit(func, xdata, ydata)
print(f'Fit results: {popt}')

assert 2.2 < popt[0] < 2.8
assert 1.0 < popt[1] < 1.7
assert 0.3 < popt[2] < 0.7
