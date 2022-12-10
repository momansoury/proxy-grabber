#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests as req
import argparse, logging, yaml, threading, queue
from time import perf_counter,sleep

def config_loader():
    with open("config.yml") as ymlfile:
        return(yaml.load(ymlfile,Loader=yaml.FullLoader))

# def is_alive(proxy):  
#     try:
#         start = perf_counter()
#         req.head(args.url, 
#                 proxies = proxy, 
#                 timeout = args.timeout
#                 )
#         logging.info(f"\t\t+{proxy}")
#     except Exception as e:
#         logging.info(f"-{proxy}")
#         return False
#     return ((perf_counter() - start) * 1000).__round__()

def rem_duplicate(ilist: list):
    res=[]
    for x in ilist:
        if x not in res:
            res.append(x)
    return res
    
def checker(q,PROXIESLISTS):
    while not q.empty():
        url=q.get()
        logging.debug(f"#Request@{url}")
        sleep(0.25)
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
    logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
#     PROXIES={
#     'http': 'socks5h://{}',
#     'https': 'socks5h://{}'
# }
    parser = argparse.ArgumentParser(description="Simple proxy grabber")
    parser.add_argument("-u", "--url", help="test connect domain", default='https://www.google.com')
    parser.add_argument('-T', '--threads', help="threads number, default is 10", default=10, type=int)
    parser.add_argument("-t", "--timeout", help="timeout in seconds, default is 4sec.", default=4 , type=int)
    parser.add_argument("-l", "--lport", help="start local port", default=None, type=int)
    parser.add_argument('-v', "--verbose", help="increase output verbosity", action="store_true", default=False)
    parser.add_argument('-d', '--debug', help="debug log", action='store_true', default=False)
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
        threading.Thread(target=checker,args=(myqueue,PROXIES_LISTS),daemon=True).start()
        logging.debug(f"Thread {x} started!")
    checker(myqueue,PROXIES_LISTS)
    logging.info(f"\n[~]Grabbed Proxies: {len(PROXIES_LISTS)}")
    logging.debug("[...]removing duplicates")
    final=rem_duplicate(PROXIES_LISTS)
    logging.debug(f"[{len(PROXIES_LISTS)-len(final)}]removed!")
    with open(args.output, "w") as op:
        for _ in final:
            op.write(f"{_}\n")
    print("\n[+]Done!")
