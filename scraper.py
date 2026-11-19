"""Polite, bounded public-page crawler for DarGlobal and Wasalt. Run: python scraper.py"""
import os, re, time, sqlite3, urllib.parse, urllib.robotparser, json
from collections import deque
import httpx
from bs4 import BeautifulSoup
from app import DB_PATH, db

SITES = {
 'DarGlobal': ['https://darglobal.co.uk/'],
 'Wasalt': ['https://wasalt.sa/en']
}
ALLOWED = {'darglobal.co.uk':'DarGlobal','wasalt.sa':'Wasalt','www.wasalt.sa':'Wasalt'}
MAX_PAGES = int(os.getenv('SCRAPE_MAX_PAGES','80'))
DELAY = float(os.getenv('SCRAPE_DELAY','1.0'))
HEADERS={'User-Agent':'EstateIntelResearchBot/1.0 (+public-page indexing; contact: admin@example.com)'}

def clean(s):
    return re.sub(r'\s+',' ',s or '').strip()

def get_robots(client, base):
    rp=urllib.robotparser.RobotFileParser(); rp.set_url(urllib.parse.urljoin(base,'/robots.txt'))
    try:
        r=client.get(rp.url,headers=HEADERS); rp.parse(r.text.splitlines() if r.status_code==200 else [])
    except Exception: rp.parse([])
    return rp

def main():
    conn=db(); seen=set(); saved=0
    # Seed with factual homepage material retrieved during initial research; live crawl supplements it.
    seed_path=os.path.join(os.path.dirname(__file__),'data','seed.json')
    if os.path.exists(seed_path):
      for item in json.load(open(seed_path,encoding='utf-8')):
        conn.execute('DELETE FROM documents WHERE url=? AND title=?',(item['url'],item['title']))
        conn.execute('INSERT INTO documents(source,url,title,content) VALUES(?,?,?,?)',(item['source'],item['url'],item['title'],item['content']))
      conn.commit(); saved=conn.execute('SELECT count(*) FROM documents').fetchone()[0]
      print(f'Loaded {saved} researched seed documents')
    with httpx.Client(timeout=25,follow_redirects=True,headers=HEADERS) as client:
      for brand, starts in SITES.items():
        queue=deque(starts); robots=get_robots(client,starts[0])
        while queue and saved<MAX_PAGES:
          url=queue.popleft().split('#')[0]
          if url in seen: continue
          seen.add(url); p=urllib.parse.urlparse(url)
          if p.scheme!='https' or p.netloc not in ALLOWED or ALLOWED[p.netloc]!=brand: continue
          if not robots.can_fetch(HEADERS['User-Agent'],url):
              print('robots disallow:',url); continue
          try:
            r=client.get(url)
            if r.status_code!=200 or 'text/html' not in r.headers.get('content-type',''): continue
            soup=BeautifulSoup(r.text,'html.parser')
            for tag in soup(['script','style','noscript','svg','nav','footer','header']): tag.decompose()
            title=clean(soup.title.get_text(' ',strip=True) if soup.title else p.path)
            body=clean(soup.get_text(' ',strip=True))
            if len(body)>180:
              conn.execute('DELETE FROM documents WHERE url=?',(url,))
              conn.execute('INSERT INTO documents(source,url,title,content) VALUES(?,?,?,?)',(brand,url,title,body[:30000])); conn.commit(); saved+=1
              print(f'[{saved}] {brand}: {title[:90]}')
            for a in soup.find_all('a',href=True):
              nxt=urllib.parse.urljoin(url,a['href']).split('#')[0]
              np=urllib.parse.urlparse(nxt)
              if np.scheme=='https' and np.netloc in ALLOWED and ALLOWED[np.netloc]==brand and nxt not in seen:
                if not any(x in np.path.lower() for x in ['/login','/account','/checkout','/privacy','/terms']): queue.append(nxt)
          except Exception as e: print('skip',url,str(e)[:120])
          time.sleep(DELAY)
    conn.close(); print(f'Finished. Indexed {saved} pages into {DB_PATH}')
if __name__=='__main__': main()
