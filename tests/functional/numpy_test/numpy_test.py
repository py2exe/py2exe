import numpy as np

l = str(np.linspace(0, 100, 5))
control = '[  0.  25.  50.  75. 100.]'

print(l)
assert(l == control)
