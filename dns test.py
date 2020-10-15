from dns import resolver
import threading
from datetime import datetime
import csv
from os import path
import time

def queryDomain(domain,results):
    startTime = datetime.now()
    try:
        result = resolver.resolve(domain, 'A')
    except(resolver.NXDOMAIN):
        msg = 'NXDomain'
    except(resolver.Timeout):
        msg = 'Timeout'
    except(resolver.NoAnswer):
        msg = 'NoAnswer'
    else:
        msg = 'Success'
        #for ipval in result: #Getting IP address
        #    msg = ipval.to_text()

    endTime = datetime.now()

    info =[domain,msg,timeToString(startTime),timeToString(endTime),timeDifference(startTime,endTime)]
    results.append(info)
    
    
def timeToString(t):
    return t.strftime('%H:%M:%S.%f')

def timeDifference(start,end):
    dif = (end-start)
    return dif.seconds + dif.microseconds/1000000

def recordInfo(key,info,infoDict):
    print(key + ': ' + str(info))
    infoDict[key] = info

def groupLatency(latency,numbers):
    numbers[0] += 1
    if (latency <=0.1):
        numbers[1] += 1
    elif (latency > 0.1 and latency <= 1):
        numbers[2] += 1
    elif (latency > 1):
        numbers[3] += 1

def recordGroup(numbers,category,infoDict):
    infoDict['Total '+category] = numbers[0]
    infoDict[category+' 0-0.1'] = numbers[1]
    infoDict[category+' 0.1-1'] = numbers[2]
    infoDict[category+' 1-5'] = numbers[3]

if __name__ == '__main__':
    
    print('Choose the kind of domain:\n(1:local domain,2:nonexistent domains,3:top 500 domains)')
    kind = input()
    print('Query interval(second)?(0:no interval,1:0.1,2:0.01,3:0.001,4:0.0001)')
    interval = input()
    if (interval == '1'):
        interval = 0.1
    elif (interval == '2'):
        interval = 0.01
    elif (interval == '3'):
        interval = 0.001
    elif (interval == '4'):
        interval = 0.0001
    print('Output filename?')
    outputName = input()
    results = []
    threads = []
    infoDict = {'Test Name':outputName,'Domain Kind':kind,'Query Interval':interval,'Start Time':'','End Time':'','Query Duration':0,
                'Total Success':0,'Total NXDomain':0,'Total Timeout':0,'Total NoAnswer':0,
                'Success 0-0.1':0,'Success 0.1-1':0,'Success 1-5':0,
                'NXDomain 0-0.1':0,'NXDomain 0.1-1':0,'NXDomain 1-5':0,
                'NoAnswer 0-0.1':0,'NoAnswer 0.1-1':0,'NoAnswer 1-5':0,
                'Timeout 0-0.1':0,'Timeout 0.1-1':0,'Timeout 1-5':0
                }
    fields = infoDict.keys()
    resolver.nameservers = ['192.168.0.130']
    localDomain = 'win.tcdtrr.ie'
    statisticFilename = 'statistic.csv'
    num = 500
    
    with open('top500Domains.csv',newline='') as rf:
        rows = list(csv.DictReader(rf))
        startTime = datetime.now()
        recordInfo('Start Time',timeToString(startTime),infoDict)
        
        for i in range(num):
            if (kind=='1'):
                domain = localDomain
            elif (kind=='2'):
                domain = localDomain + str(i)
            elif (kind=='3'):
                domain = rows[i]['Root Domain']
            t = threading.Thread(target=queryDomain,args=(domain,results,))
            threads.append(t)
            t.start()
            if (interval != '0'):
                time.sleep(interval)

        endTime = datetime.now()
        recordInfo('End Time',timeToString(endTime),infoDict)
        recordInfo('Query Duration',timeDifference(startTime,endTime),infoDict)

    for thread in threads:
        thread.join()

    successList = [0,0,0,0] #total,0~0.1 second,0.1~1 second,1~5 second
    timeoutList = [0,0,0,0]
    noAnswerList = [0,0,0,0]
    nxDomainList = [0,0,0,0]
    
    
    wf = open(outputName+'.csv','w',newline='')
    
    with wf:
        writer = csv.writer(wf)
        for result in results:
            writer.writerow(result)
            msg = result[1]
            latency = result[4]
            if (msg == 'NXDomain'):
                groupLatency(latency,nxDomainList)
            elif (msg == 'Timeout'):
                groupLatency(latency,timeoutList)
            elif (msg == 'NoAnswer'):
                groupLatency(latency,noAnswerList)
            elif (msg == 'Success'):
                groupLatency(latency,successList)
    
    recordGroup(successList,'Success',infoDict)
    recordGroup(timeoutList,'Timeout',infoDict)
    recordGroup(noAnswerList,'NoAnswer',infoDict)
    recordGroup(nxDomainList,'NXDomain',infoDict)
    
    if not (path.exists(statisticFilename)):
        f = open(statisticFilename,'w')
        f.write(','.join(fields)+'\n');
        f.close()

    with open(statisticFilename,'a',newline='') as sta:
        writer = csv.DictWriter(sta,delimiter=',',fieldnames=fields)
        writer.writerow(infoDict)

    print('The statistic has been generated.')
