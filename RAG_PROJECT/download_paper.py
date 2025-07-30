# download_papers.py
# Python 3.12
# 批量下载近5年 NLP/AI/ML 领域2000+篇会议/期刊论文 PDF
# 集成 ArXiv、Crossref+多源OA（Unpaywall, EuropePMC, CORE, OpenAlex）

import os
import asyncio
import aiohttp
import hashlib
from typing import List, Dict
import requests
import feedparser
from tqdm.asyncio import tqdm
from urllib.parse import urlencode
import time
import random
import ssl
import certifi

# =====================================
# 配置区
# =====================================
KEYWORDS = [
    'machine learning', 'deep learning', 'neural network', 'artificial intelligence',
    'natural language processing', 'nlp', 'computer vision', 'transformer', 'bert', 'gpt',
    'llama', 'mistral', 'retrieval', 'rag', 'reinforcement learning', 'graph neural network'
]
DATE_RANGE = 'submittedDate:[2018-01-01 TO 2025-12-31]'
ARXIV_API = 'https://export.arxiv.org/api/query'
CROSSREF_API = 'https://api.crossref.org/works'
UNPAYWALL_API = 'https://api.unpaywall.org/v2/'     # append DOI + ?email=
EUROPEPMC_API = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
CORE_API = 'https://core.ac.uk:443/api-v2/articles/search/ids'
OPENALEX_API = 'https://api.openalex.org/works'
EMAIL = 'q1293132751@163.com'  # Unpaywall & OpenAlex required
CORE_API_KEY = ''
MAX_PAPERS = 2000
BATCH_SIZE = 100
SAVE_DIR = 'papers'
CONCURRENCY = 20  # 提高并发下载数
TIMEOUT = 60
USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/115.0 Safari/537.36'
)
SEEN_IDS_FILE = os.path.join(SAVE_DIR, 'downloaded_ids.txt')

# 全局请求头
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'application/pdf,application/octet-stream,*/*;q=0.9'
}
# SSL context
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

# =====================================
# 工具函数
# =====================================
def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def load_seen_ids() -> set[str]:
    if not os.path.exists(SEEN_IDS_FILE): return set()
    with open(SEEN_IDS_FILE) as f: return set(line.strip() for line in f)

def save_seen_id(pid: str) -> None:
    with open(SEEN_IDS_FILE, 'a') as f: f.write(pid + '\n')

def md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# =====================================
# 来源1：arXiv
# 使用 requests 无代理环境避免 ProxyError
SESSION_NON_PROXY = requests.Session()
SESSION_NON_PROXY.trust_env = False

def fetch_arxiv() -> List[Dict]:
    print("[arXiv] 开始检索...")
    papers = {}
    per_kw = MAX_PAPERS // len(KEYWORDS) + 1
    for kw in KEYWORDS:
        if len(papers) >= MAX_PAPERS: break
        print(f"[arXiv] 关键词={kw}, 已收集={len(papers)}")
        for start in range(0, per_kw, BATCH_SIZE):
            if len(papers) >= MAX_PAPERS: break
            params = {
                'search_query': f'all:"{kw}" AND {DATE_RANGE}',
                'start': start,
                'max_results': BATCH_SIZE,
                'sortBy': 'submittedDate',
                'sortOrder': 'descending'
            }
            resp = SESSION_NON_PROXY.get(ARXIV_API, params=params, headers=HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            feed = feedparser.parse(resp.text)
            if not feed.entries: break
            for e in feed.entries:
                pid = e.id.split('/')[-1]
                if pid in papers: continue
                url = next((l.href for l in e.links if l.type=='application/pdf'), f'https://arxiv.org/pdf/{pid}.pdf')
                papers[pid] = {'id': pid, 'doi': None, 'pdf_url': url}
                if len(papers) >= MAX_PAPERS: break
    print(f"[arXiv] 完成检索, 收集={len(papers)} 篇")
    return list(papers.values())

# =====================================
# 多源OA检索函数
# =====================================
def fetch_oa_pdf(doi: str) -> str:
    """
    多源获取 OA PDF 链接：依次尝试 Unpaywall, Europe PMC, CORE, OpenAlex
    返回 PDF 直链或 None
    """
    # Unpaywall
    try:
        url = f"{UNPAYWALL_API}{doi}?email={EMAIL}"
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            oa = data.get('best_oa_location') or {}
            pdf = oa.get('url_for_pdf') or oa.get('url')
            if pdf:
                print(f"[Unpaywall] DOI={doi} => {pdf}")
                return pdf
        else:
            print(f"[Unpaywall] DOI={doi} HTTP {resp.status_code}")
    except Exception as e:
        print(f"[Unpaywall] DOI={doi} 异常: {e}")
    # Europe PMC
    try:
        params = {'query': f'EXT_ID:{doi} AND OPEN_ACCESS:Y', 'format': 'json'}
        resp = requests.get(EUROPEPMC_API, params=params, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('resultList', {}).get('result', [])
            if results:
                pdf = results[0].get('pdfUrl')
                if pdf:
                    print(f"[EuropePMC] DOI={doi} => {pdf}")
                    return pdf
        else:
            print(f"[EuropePMC] DOI={doi} HTTP {resp.status_code}")
    except Exception as e:
        print(f"[EuropePMC] DOI={doi} 异常: {e}")
        # CORE: 需要 CORE_API_KEY，若未设置则跳过
    if CORE_API_KEY and CORE_API_KEY != 'YOUR_CORE_API_KEY':
        try:
            params = {'q': doi, 'cursor': '*', 'pageSize': 1}
            headers_core = {'Authorization': CORE_API_KEY}
            resp = requests.get(CORE_API, params=params, headers=headers_core, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                ids = data.get('data', [])
                if ids:
                    core_id = ids[0]
                    pdf = f"https://core.ac.uk:443/api-v2/articles/get/{core_id}?metadata=false&download=true&apiKey={CORE_API_KEY}"
                    print(f"[CORE] DOI={doi} => {pdf}")
                    return pdf
            else:
                print(f"[CORE] DOI={doi} HTTP {resp.status_code}")
        except Exception as e:
            print(f"[CORE] DOI={doi} 异常: {e}")
    else:
        print(f"[CORE] 跳过 CORE，未配置 CORE_API_KEY")
    # OpenAlex
    try:
        params = {'filter': f'doi:{doi}', 'mailto': EMAIL}
        resp = requests.get(OPENALEX_API, params=params, headers=HEADERS, timeout=TIMEOUT)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', [])
            if results:
                oa_locs = results[0].get('open_access', {}).get('oa_locations', [])
                for loc in oa_locs:
                    pdf = loc.get('url_for_pdf')
                    if pdf:
                        print(f"[OpenAlex] DOI={doi} => {pdf}")
                        return pdf
        else:
            print(f"[OpenAlex] DOI={doi} HTTP {resp.status_code}")
    except Exception as e:
        print(f"[OpenAlex] DOI={doi} 异常: {e}")
    return None

# =====================================
# 来源2：Crossref + 多源OA
# =====================================
def fetch_crossref_multisource() -> List[Dict]:
    """
    并发检索 Crossref + 多源 OA，提高元数据获取速度
    """
    print("[Crossref] 并发检索开始...")
    papers = {}
    per_kw = MAX_PAPERS // len(KEYWORDS) + 1
    # 内部函数处理单个关键词
    def process_kw(kw):
        local = {}
        for offset in range(0, per_kw, BATCH_SIZE):
            params = {
                'query.title': kw,
                'filter': 'from-pub-date:2018-01-01',
                'rows': BATCH_SIZE,
                'offset': offset
            }
            try:
                resp = SESSION_NON_PROXY.get(CROSSREF_API, params=params, headers=HEADERS, timeout=TIMEOUT)
                data = resp.json()
                items = data.get('message', {}).get('items', [])
                if not items:
                    break
                for it in items:
                    doi = it.get('DOI')
                    if not doi:
                        continue
                    pid = md5(doi)
                    if pid in papers or pid in local:
                        continue
                    pdf_url = fetch_oa_pdf(doi)
                    if pdf_url:
                        local[pid] = {'id': pid, 'doi': doi, 'pdf_url': pdf_url}
            except Exception as e:
                print(f"[Crossref] {kw} offset={offset} 异常: {e}")
        print(f"[Crossref] {kw} 完成, 本地收集={len(local)} 篇")
        return local
    # 并发执行
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=min(10, len(KEYWORDS))) as executor:
        future_to_kw = {executor.submit(process_kw, kw): kw for kw in KEYWORDS}
        for future in as_completed(future_to_kw):
            kw = future_to_kw[future]
            try:
                result = future.result()
                papers.update(result)
                print(f"[Crossref] {kw} 合并后总数={len(papers)}")
                if len(papers) >= MAX_PAPERS:
                    break
            except Exception as e:
                print(f"[Crossref] {kw} 处理异常: {e}")
    print(f"[Crossref] 并发检索完成, 总收集={len(papers)} 篇")
    return list(papers.values())

# =====================================
# 异步下载函数
# =====================================
async def download_one(session: aiohttp.ClientSession, paper: Dict, seen: set[str]) -> None:
    pid, url = paper['id'], paper['pdf_url']
    if pid in seen: return
    out = os.path.join(SAVE_DIR, f"{pid}.pdf")
    for attempt in range(1, 4):
        print(f"[下载] {pid} 尝试({attempt}/3) URL={url}")
        try:
            async with session.get(url, timeout=TIMEOUT, allow_redirects=True) as r:
                if r.status == 200:
                    data = await r.read()
                    if data.startswith(b'%PDF') and len(data) > 1024:
                        with open(out, 'wb') as f:
                            f.write(data)
                        save_seen_id(pid)
                        print(f"[成功] {pid}")
                        return
                print(f"[失败] {pid} HTTP {r.status}")
        except Exception as e:
            print(f"[异常] {pid}: {e}")
        await asyncio.sleep(random.uniform(5, 10))
    print(f"[下载失败] {pid}")

async def bulk_download(papers: List[Dict]) -> None:
    ensure_dir(SAVE_DIR)
    seen = load_seen_ids()
    connector = aiohttp.TCPConnector(limit=CONCURRENCY, ssl=SSL_CONTEXT)
    async with aiohttp.ClientSession(connector=connector, trust_env=True, headers=HEADERS) as session:
        tasks = [download_one(session, p, seen) for p in papers]
        for _ in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await _

# =====================================
# 主程序
# =====================================
async def main():
    ensure_dir(SAVE_DIR)
    arxiv_papers = fetch_arxiv()
    crossref_papers = fetch_crossref_multisource()
    all_papers = {p['id']: p for p in (arxiv_papers + crossref_papers)}
    print(f"总计去重后: {len(all_papers)} 篇")
    await bulk_download(list(all_papers.values()))
    print(f"下载完成，已保存: {len(load_seen_ids())} 篇")

if __name__ == '__main__':
    asyncio.run(main())
