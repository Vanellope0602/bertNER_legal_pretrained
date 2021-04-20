import urllib 
import requests
print("downloading with requests")
url = "http://panobject.iflytek.com:10001/anyshare_bucket/dbeb61d7-d26c-4297-bdb1-59206eb8af1b/0715D61A935640FF8AF7A41C25D2657F/3E62B6A3B1B040E2AD524B0ED452DC2D?response-content-disposition=attachment%3b%20filename%3d%22electra%255f180g%255flarge.zip%22%3b%20filename*%3dutf%2d8%27%27electra%255f180g%255flarge.zip&AWSAccessKeyId=ayshare&Expires=1618906242&Signature=ofQMZy21z1AVBfnDnlJHe3WQ49U%3d"
r = requests.get(url)
with open("legal_electra_base.zip", "wb") as code:
	code.write(r.content)
