"""
BSD 3-Clause License

Copyright (c) 2008-2011, AQR Capital Management, LLC, Lambda Foundry, Inc. and PyData Development Team
All rights reserved.

Copyright (c) 2011-2020, Open source contributors.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import pandas as pd
import pandas.core.common as com

G = [-0.30570, 0.6368, -0.72287, 0.24160528, -1.0439]
B = list(range(2)) + list(range(2)) + list(range(1))
A = list(range(5))
df = pd.DataFrame(
    {
        "A": A,
        "B": B,
        "C": A,
        "D": B,
        "E": A,
        "F": B,
        "G": A,
        "H": B,
        "values": G,
    }
)

lg = df.groupby(["A", "B", "C", "D", "E", "F", "G", "H"])
rg = df.groupby(["H", "G", "F", "E", "D", "C", "B", "A"])

left = lg.sum()["values"]
right = rg.sum()["values"]

exp_index, _ = left.index.sortlevel()
exp_index, _ = right.index.sortlevel(0)

tups = list(map(tuple, df[["A", "B", "C", "D", "E", "F", "G", "H"]].values))
tups = com.asarray_tuplesafe(tups)

expected = df.groupby(tups).sum()["values"]

for k, v in expected.items():
    assert left[k] == right[k[::-1]]
    assert left[k] == v
assert len(left) == len(right)
