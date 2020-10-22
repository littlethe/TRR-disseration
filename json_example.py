from urllib.request import *
import json
import ssl

domain = "www.google.com"
#domain = "win.tcdtrr.ie"
sType = "A"

#dns = "vm.tcdtrr.ie"
dns = "cloudflare-dns.com"
#dns = "mozilla.cloudflare-dns.com"

header = "application/dns-json"
#header = "application/dns-message"

ssl._create_default_https_context = ssl._create_unverified_context

try:
    req = Request('https://'+dns+'/dns-query?ct='+header+"&name="+domain+"&type="+sType)
    res = urlopen(req).read()
    reply = json.loads(res)

    if "Answer" in reply:
        answers = reply["Answer"]
        data = [answer["data"] for answer in answers]
        print("success")
    else:
        data = []
        print("fail")

    print(data)
        
except Exception as ex:
    print("Exception occurred: '%s'" % ex)
    
