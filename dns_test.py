from dns import resolver
import threading
from datetime import datetime
import csv
from os import path
import time
import sys
from urllib.request import *
import urllib
import json
import ssl
import requests
import base64
from dnslib import *

localWebsite = 'win.tcdtrr.ie'

ssl._create_default_https_context = ssl._create_unverified_context

intervalDict = {'0':0,'1':0.1,'2':0.01,'3':0.001}
queryTypeDict = {'1':'A','2':'AAAA','3':'CNAME','4':'MX'}
domainKindDict = {'1':'Local','2':'Fake','3':'Ireland','4':'World'}
queryMethodDict = {'1':'Wireformat','2':'JSON','3':'Tradition'}
dnsProviderDict = {'1':{'short':'Local',        'ip':'192.168.0.130',   'full':'vm.tcdtrr.ie'},
                   '2':{'short':'Cloudflare',   'ip':'1.1.1.1',         'full':'cloudflare-dns.com'},
                   '3':{'short':'Google',       'ip':'8.8.8.8',         'full':'dns.google'}}

filenameDict = {'statistic':'statistic.csv',
                'World':'top500Domains.csv',
                'Ireland':'top50Ireland.csv'}

infoDict = {'Filename':'','Note':'','Domain Kind':'','Query Interval':0,'Query Type':'','Query Method':'',
    'DNS Provider':'','Query Number':0,'Start Time':'','End Time':'','Query Duration':0,
    'Total Success':0,'Total NXDomain':0,'Total NoAnswer':0,'Total Timeout':0,                
    'Success 0-0.1':0,'Success 0.1-1':0,'Success 1-5':0,'Success >5':0,
    'NXDomain 0-0.1':0,'NXDomain 0.1-1':0,'NXDomain 1-5':0,'NXDomain >5':0,
    'NoAnswer 0-0.1':0,'NoAnswer 0.1-1':0,'NoAnswer 1-5':0, 'NoAnswer >5':0,
    'Timeout 0-0.1':0,'Timeout 0.1-1':0,'Timeout 1-5':0, 'Timeout >5':0,
    'Average Success Duration':0,'Average NXDomain Duration':0,'Average NoAnswer Duration':0,'Average Timeout Duration':0,
    'Fastest Success Duration':0,'Fastest Success Domain':'',
    'Fastest NXDomain Duration':0,'Fastest NXDomain Domain':'',
    'Fastest NoAnswer Duration':0,'Fastest NoAnswer Domain':'',
    'Fastest Timeout Duration':0,'Fastest Timeout Domain':'',
    'Latest Success Duration':0,'Latest Success Domain':'',
    'Latest NXDomain Duration':0,'Latest NXDomain Domain':'',
    'Latest NoAnswer Duration':0,'Latest NoAnswer Domain':'',
    'Latest Timeout Duration':0,'Latest Timeout Domain':''
}

class QueryObject:
    def __init__(self,domain,responses,queryType,queryMethod,dnsFull,dohCode):
        self.domain = domain
        self.responses = responses
        self.queryType = queryType
        self.queryMethod = queryMethod
        self.dnsFull = dnsFull
        self.dohCode = dohCode

class ResponseObject:
    def __init__(self,domain,result,startTime,endTime,duration,message):
        self.domain = domain
        self.result = result
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration
        self.message = message

class DistributionObject:
    def __init__(self):
        self.total = 0
        self.in01 = 0   #0-0.1 second
        self.in1 = 0    #0.1-1 second
        self.in5 = 0    #1-5 seconds
        self.over5 = 0  # >5 seconds
        self.average = 0
        self.latest = 0
        self.fastest = 0
        self.latestDomain = ''
        self.fastestDomain = ''

def queryDomain(query):
    
    startTime = datetime.now()
    msg = ''
    if(queryMethod=='Tradition'):
        try:
            resp = resolver.resolve(query.domain, query.queryType)
        except(resolver.NXDOMAIN):
            res = 'NXDomain'
        except(resolver.Timeout):
            res = 'Timeout'
        except(resolver.NoAnswer):
            res = 'NoAnswer'
        else:
            res = 'Success'
            #for ipval in result: #Getting IP address
            #    msg = ipval.to_text()
    else:
        try:
            if(queryMethod=='Wireformat'):
                req = Request('https://'+query.dnsFull+'/dns-query?dns='+query.dohCode)
                resp = urlopen(req).read()
                content = DNSRecord.parse(resp)
                if(len(content.rr)==0):
                    res = 'NXDomain'
                else:
                    res = 'Success'
                    
            elif(queryMethod=='JSON'):
                req = Request('https://'+query.dnsFull+'/dns-query?ct=application/dns-json&name='+query.domain+'&type='+query.queryType)
                resp = urlopen(req).read()
                reply = json.loads(resp)

                if "Answer" in reply:
                    res = 'Success'
                else:
                    res = 'NXDomain'
                
        except urllib.error.HTTPError as err:
            res = 'NoAnswer'
            msg = str(err.code)
        except Exception as err:
            res = 'Timeout'
            msg = str(err)

    endTime = datetime.now()
    response = ResponseObject(query.domain,res,timeToString(startTime),timeToString(endTime),timeDifference(startTime,endTime),msg)
    query.responses.append(response)

def timeToString(t):
    return t.strftime('%Y-%m-%d %H:%M:%S.%f')

def timeDifference(start,end):
    dif = (end-start)
    return dif.seconds + dif.microseconds/1000000

def recordInfo(key,info,infoDict):
    print(key + ': ' + str(info))
    infoDict[key] = info

def inputPara(hint,default):
    print(hint)
    s = input()
    if(s == ''):
        s = default
        print(s)
    return s

def setDnsFull(queryMethod,ip,name):
    if(queryMethod=='Tradition'):
        dnsFull = ip
    else:
        dnsFull = name
    return dnsFull

def detectFile(filename):
    if not (path.exists(filename)):
        print('Please put the csv file "'+filename+'" in the same dirctory.')
        sys.exit(1)

if __name__ == '__main__':

    fields = infoDict.keys()
    statFn = filenameDict['statistic']
    if not (path.exists(statFn)):
        f = open(statFn,'w')
        f.write(','.join(fields)+'\n');
        f.close()
    try:
        statFile = open(statFn,'a',newline='')
    except:
        print('Error,the file "'+statFn+'" is opening, please close it.')
        sys.exit(1)

    detectFile(filenameDict['Ireland'])
    detectFile(filenameDict['World'])
    
    domainKind = domainKindDict[inputPara('Choose the kind of domain:\n1:local domain\n2:fake domains\n3:top 50 Ireland domains(default)\n4:top 500 world domains','3')]
    interval = intervalDict[inputPara('Query interval(second)?(0:no interval(default),1:0.1,2:0.01,3:0.001,4:0.0001)','0')]
    queryType = queryTypeDict[inputPara('Query type?(1:A(default),2:AAAA,3:CNAME,4:MX)','1')]
    queryMethod = queryMethodDict[inputPara('Query Method?(1:DOH Wireformat(default),2:DOH JSON,3:Tradition)','1')]
    dns = dnsProviderDict[inputPara('DNS Server?(1:local(default),2.cloudflare,3.google)','1')]
    queryNumber = int(inputPara('Query number?(default:50)',50))
    note = inputPara('Note?(optional, default is no blank)','')

    infoDict['Domain Kind'] = domainKind
    infoDict['Note'] = note
    infoDict['Query Interval'] = interval
    infoDict['Query Type'] = queryType
    infoDict['Query Method'] = queryMethod
    infoDict['DNS Provider'] = dns['short']
    infoDict['Query Number'] = queryNumber
    
    responses = []
    threads = []
    resolver.nameservers = [dns['ip']]

    if(domainKind=='World' or domainKind=='Ireland'):
        with open(filenameDict[domainKind],newline='') as rf:
            rows = list(csv.DictReader(rf))
            rowCount = len(rows)

    queryObjects = []
    for i in range(queryNumber):
        if (domainKind=='Local'):
            domain = localWebsite
        elif (domainKind=='Fake'):
            domain = localWebsite + str(i)
        elif (domainKind=='World' or domainKind=='Ireland'):
            domain = rows[i%rowCount]['Root Domain']

        dohCode = ''
        if (queryMethod == 'Wireformat'):
            if(queryType == 'A'):
                qt = QTYPE.A
            elif(queryType == 'AAAA'):
                qt = QTYPE.AAAA
            elif(queryType == 'CNAME'):
                qt = QTYPE.CNAME
            elif(queryType == 'MX'):
                qt = QTYPE.MX
            d = DNSRecord(q=DNSQuestion(domain,qt))
            d = base64.b64encode(d.pack())
            dohCode = d.decode('ascii').strip('=')

        queryObjects.append(QueryObject(domain,responses,queryType,queryMethod,dns['full'],dohCode))

    
    startTime = datetime.now()
    recordInfo('Start Time',timeToString(startTime),infoDict)
    
    for query in queryObjects:
        t = threading.Thread(target=queryDomain,args=(query,))
        threads.append(t)
        t.start()
        
        if (interval != 0):
            time.sleep(interval)

    endTime = datetime.now()
    recordInfo('End Time',timeToString(endTime),infoDict)
    recordInfo('Query Duration',timeDifference(startTime,endTime),infoDict)

    for thread in threads:
        thread.join()

    distributions = {'Success':DistributionObject(),'Timeout':DistributionObject(),'NoAnswer':DistributionObject(),'NXDomain':DistributionObject()}
    outputFn = domainKind+'_'+note+'_'+queryType+'_'+queryMethod+'_'+dns['short']+'_'+str(queryNumber)+'_'+str(interval).replace('.','')+'_'+endTime.strftime('%Y-%m-%d-%H-%M-%S')+'.csv'
    infoDict['Filename'] = outputFn
    
    wf = open(outputFn,'w',newline='')
    with wf:
        writer = csv.DictWriter(wf,delimiter=',',fieldnames=responses[0].__dict__.keys())
        writer.writeheader()
        latest = 0
        fastest = 0
        average = 0
        for response in responses:
            writer.writerow(response.__dict__)
            dist = distributions[response.result]
            latency = response.duration
            domain = response.domain
            dist.total += 1
            
            if (latency > dist.latest):
                dist.latest = latency
                dist.latestDomain = domain

            if (latency < dist.fastest or dist.fastest == 0):
                dist.fastest = latency
                dist.fastestDomain = domain

            dist.average += latency
            
            if (latency <=0.1):
                dist.in01 += 1
            elif (latency > 0.1 and latency <= 1):
                dist.in1 += 1
            elif (latency > 1 and latency <= 5):
                dist.in5 += 1
            else:
                dist.over5 +=1

    for category in distributions.keys():
        dist = distributions[category]
        infoDict['Total '+category] = dist.total
        infoDict[category+' 0-0.1'] = dist.in01
        infoDict[category+' 0.1-1'] = dist.in1
        infoDict[category+' 1-5'] = dist.in5
        infoDict[category+' >5'] = dist.over5
        infoDict['Fastest '+category+' Duration'] = dist.fastest
        infoDict['Fastest '+category+' Domain'] = dist.fastestDomain
        infoDict['Latest '+category+' Duration'] = dist.latest
        infoDict['Latest '+category+' Domain'] = dist.latestDomain
        infoDict['Average '+category+' Duration'] = 0 if(dist.total==0) else dist.average/dist.total

    with statFile:
        writer = csv.DictWriter(statFile,delimiter=',',fieldnames=fields)
        writer.writerow(infoDict)
        
    print('The responses of all domain names have been recorded in \n'+ outputFn+'.')
    print('The statistic has been generated in '+statFn+'.')
