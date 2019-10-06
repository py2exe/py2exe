import os
import sqlite3

print('sqlite3 version: {}'.format(sqlite3.version))

conn = sqlite3.connect('test.db')
c = conn.cursor()
c.execute('''CREATE TABLE stocks
             (date text, trans text, symbol text, qty real, price real)''')
c.execute("INSERT INTO stocks VALUES ('2006-01-05','BUY','RHAT',100,35.14)")
conn.commit()

for row in c.execute('SELECT * FROM stocks ORDER BY price'):
        out = row

print('sqlite3 test output: {}'.format(out))
assert str(out) == "('2006-01-05', 'BUY', 'RHAT', 100.0, 35.14)"
        
conn.close()
os.remove('test.db')