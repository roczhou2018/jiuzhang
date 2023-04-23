# _url = "http://www.guoxuedashi.net/a201/"
_url = "http://www.guoxuedashi.net/a/2tbfg/111116y.html"

import requests
from pyquery import PyQuery as pq
import asyncio

async def parse_url(url=_url):    
    response = requests.get(url)
    doc = pq(response.text)
    
    ps = []
    for it in doc('div.info_tree').items():
        p = it.text().strip()
        ps.append(p)
        # l = it.find('a').attr('href')
    pathseq = ps[0].replace('\n', ' ').split(' > ')
    print(pathseq)
    
    # ls = doc('div.info_cate').items()
    # for l in ls: print(l.text())

asyncio.run(parse_url())

