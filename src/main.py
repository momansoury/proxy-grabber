#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests as req
import argparse, logging, yaml, threading, queue
from time import perf_counter,sleep

def config_loader():
    with open("config.yml") as ymlfile:
        return(yaml.load(ymlfile,Loader=yaml.FullLoader))

def is_alive(proxy)->bool:  
    try:
        # start = perf_counter()
        req.head(args.url, 
                proxies = proxy, 
                timeout = args.timeout
                )
        return True
    except Exception as e:
        return False
    # return ((perf_counter() - start) * 1000).__round__()

def scanner(q):
    PROXIES={
    'http': 'http://{}',
    'https': 'https://{}'
    }
    while not q.empty():
        p=q.get()
        PROXIES["http"]=PROXIES["http"].format(p)
        PROXIES["https"]=PROXIES["https"].format(p)
        if is_alive(PROXIES):
            logging.debug(f"\t\t+{p}")
            with open(scanned_fname, "w") as op:
                op.write(f"{p}\n")
        else:
            logging.debug(f"-{p}")
        q.task_done()

def rmdup(ilist: list):
    res=[]
    for x in ilist:
        if x not in res:
            res.append(x)
    return res
    
def grabber(q,PROXIESLISTS):
    while not q.empty():
        url=q.get()
        logging.debug(f"#Request@{url}")
        sleep(0.2)
        try:
            src=req.get(url,timeout=args.timeout)
            if src.status_code==200:
                new_proxy=src.text.replace(" ","").strip("\n").split("\n")
                PROXIESLISTS += new_proxy
                logging.info(f"URLs: {q.qsize()}/{len(cfg['URLS'])}")
                logging.debug(f"[{len(new_proxy)}]New proxies loaded...")
            else:
                logging.warning(f"[{url}]>> {src.status_code}")
        except:
            logging.error(f"!{url}",exc_info=False)
        q.task_done()
    return PROXIESLISTS

if __name__ == '__main__':
    logging.basicConfig(level=logging.ERROR, format='%(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Simple proxy grabber")
    parser.add_argument("-u", "--url", help="test connect domain", default='https://www.google.com')
    parser.add_argument('-T', '--threads', help="threads number, default is 10", default=10, type=int)
    parser.add_argument("-t", "--timeout", help="timeout in seconds, default is 4sec.", default=4 , type=int)
    parser.add_argument('-v', "--verbose", help="increase output verbosity", action="store_true", default=False)
    parser.add_argument('-d', '--debug', help="debug log", action='store_true', default=False)
    parser.add_argument('-s', '--scan', help="Scan the grabbed proxies", action='store_true', default=False)
    parser.add_argument('-o', '--output', help="output file", default='grabbed.txt')
    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    cfg=config_loader()
    logging.debug(f"#URLs Loaded: {len(cfg['URLS'])}")
    N = min(args.threads, len(cfg['URLS']))-1
    PROXIES_LISTS=[]
    myqueue=queue.Queue()

    for u in cfg["URLS"]:
        myqueue.put(u)
        logging.debug(f"Url Loaded>> {u}")

    for x in range(N):
        threading.Thread(target=grabber,args=(myqueue,PROXIES_LISTS),daemon=True).start()
        logging.debug(f"Thread {x} started!")
    logging.debug(f"Main Thread starting...")
    grabber(myqueue,PROXIES_LISTS)

    print("="*30)
    logging.info(f"[~]Grabbed Proxies: {len(PROXIES_LISTS)}")
    logging.info("[...]removing duplicates")
    final=rmdup(PROXIES_LISTS)
    logging.debug(f"[{len(PROXIES_LISTS)-len(final)}]removed!>> {len(final)}")
    logging.debug(f"saving@{args.output}...")
    with open(args.output, "w") as op:
        for _ in final:
            op.write(f"{_}")
            
    if args.scan:
        print("[~]Scanning the proxies...")
        PROXIES_LISTS=[]
        myqueue=queue.Queue()
        logging.debug("importing proxies to queue...")
        start = perf_counter()
        for u in final:
            myqueue.put(u)
        logging.debug(f"imported@{((perf_counter()-start)*1000).__round__()} ms.")
        scanned_fname=f"scanned-{args.output}"
        logging.debug(f"starting {N} Threads...")
        for x in range(N):
            threading.Thread(target=scanner,args=(myqueue,),daemon=True).start()
            logging.debug(f"Thread {x} started!")
        logging.debug(f"Main Thread starting...")
        scanner(myqueue)
        print(f"[+]Scan completed@{scanned_fname}")

    print("\n[+]Done!")
