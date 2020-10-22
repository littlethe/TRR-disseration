from urllib.request import *
import json
import ssl
import requests
import base64
from dnslib import *

domain = "www.google.com"
#domain = "win.tcdtrr.ie"

dns = "vm.tcdtrr.ie"
#dns = "cloudflare-dns.com"
#dns = "mozilla.cloudflare-dns.com"

ssl._create_default_https_context = ssl._create_unverified_context

try:

    d = DNSRecord(q=DNSQuestion(domain,QTYPE.A))
    d = base64.b64encode(d.pack())
    st = d.decode('ascii').strip('=')

    req = Request('https://'+dns+'/dns-query?dns='+st)
    res = urlopen(req).read()
    content = DNSRecord.parse(res)

    print(content)


except Exception as ex:
    print("Exception occurred: '%s'" % ex)
    
