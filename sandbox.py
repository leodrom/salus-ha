from salus import Salus

s = Salus()

s.do_login(
        'dmitry.kosaryev@gmail.com',
        'supermarker')

s.parse_token()

print (f"Security Token: {s.token}")

s.do_login(
        'dmitry.kosaryev@gmail.com',
        'supermarker')

s.parse_token()

print (f"Security Token: {s.token}")