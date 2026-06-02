import pyphen

dic = pyphen.Pyphen(lang='en_US')
result = dic.inserted('hyphenation')
print('pyphen test output: {}'.format(result))
assert result == 'hy-phen-ation', repr(result)
