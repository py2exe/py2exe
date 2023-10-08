import requests

r = requests.get('http://www.appveyor.com')
print(r.url)
print(r.status_code)

assert r.url == 'https://www.appveyor.com/'
assert r.status_code == 200
