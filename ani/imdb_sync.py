import asyncio
import csv
import io
import json
import re
import time
import threading
import requests
from django.core.files.base import ContentFile
from django.db import close_old_connections
from django.utils import timezone


# ── Playwright async helpers ──────────────────────────────────────────────────

async def _async_make_browser():
    from playwright.async_api import async_playwright
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    ctx = await browser.new_context(
        user_agent=(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        locale='en-US',
    )
    page = await ctx.new_page()
    await page.goto('https://www.imdb.com/', timeout=30000)
    await asyncio.sleep(4)  # wait for AWS WAF JS challenge to complete
    return p, browser, page


async def _async_get_next_data(page, url):
    try:
        await page.goto(url, timeout=30000)
        await asyncio.sleep(1)
        content = await page.content()
        m = re.search(
            r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
            content, re.DOTALL
        )
        return json.loads(m.group(1)) if m else None
    except Exception:
        return None


async def _async_fetch_watchlist_ids(page, url):
    nd = await _async_get_next_data(page, url)
    if not nd:
        return []
    ids, seen = [], set()

    def _walk(obj, depth=0):
        if depth > 25:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ('id', 'titleId', 'tconst') and isinstance(v, str) and re.match(r'^tt\d+$', v):
                    if v not in seen:
                        seen.add(v)
                        ids.append(v)
                else:
                    _walk(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item, depth + 1)

    _walk(nd)
    return ids


def _extract_credits(principal_credits):
    creators, directors = [], []
    for group in (principal_credits or []):
        cat = ((group.get('category') or {}).get('text') or '').lower().strip()
        names = [
            ((c.get('name') or {}).get('nameText') or {}).get('text', '').strip()
            for c in (group.get('credits') or [])
        ]
        names = [n for n in names if n]
        # "Creator" / "Creators" 都命中
        if 'creator' in cat:
            creators.extend(names)
        elif 'director' in cat:
            directors.extend(names)
    return creators or directors


def _translate_to_zh(text):
    if not text:
        return None
    try:
        from deep_translator import GoogleTranslator
        return GoogleTranslator(source='en', target='zh-TW').translate(text)
    except Exception:
        return None


async def _async_scrape_title(page, imdb_id):
    nd = await _async_get_next_data(page, f'https://www.imdb.com/title/{imdb_id}/')
    if not nd:
        return None
    try:
        above = ((nd.get('props') or {}).get('pageProps') or {}).get('aboveTheFoldData') or {}
        ry = above.get('releaseYear') or {}
        return {
            'imdb_id':     imdb_id,
            'title':       ((above.get('titleText') or {}).get('text')),
            'year':        ry.get('year'),
            'status':      'FINISHED' if ry.get('endYear') else None,
            'imdb_stars':  (above.get('ratingsSummary') or {}).get('aggregateRating'),
            'poster_url':  (above.get('primaryImage') or {}).get('url'),
            'creators':    _extract_credits(above.get('principalCredits')),
            'description': ((above.get('plot') or {}).get('plotText') or {}).get('plainText'),
        }
    except Exception:
        return None


async def _async_scrape_zh_title(page, imdb_id):
    nd = await _async_get_next_data(page, f'https://www.imdb.com/title/{imdb_id}/releaseinfo')
    if not nd:
        return None
    try:
        page_props = ((nd.get('props') or {}).get('pageProps') or {})
        categories = (page_props.get('contentData') or {}).get('categories') or []
        for cat in categories:
            for item in ((cat.get('section') or {}).get('items') or []):
                for attr in (item.get('attributes') or []):
                    if (attr.get('text') or '').strip().lower() == 'taiwan':
                        title = item.get('rowTitle') or item.get('title')
                        if title:
                            return title
        text = json.dumps(nd, ensure_ascii=False)
        for pattern in [
            r'"(?:rowTitle|title)"\s*:\s*"([一-鿿][^"]{0,80})"[^}]{0,300}"Taiwan"',
            r'"Taiwan"[^}]{0,300}"(?:rowTitle|title)"\s*:\s*"([一-鿿][^"]{0,80})"',
        ]:
            m = re.search(pattern, text)
            if m:
                return m.group(1)
    except Exception:
        pass
    return None


# ── Non-async helpers ─────────────────────────────────────────────────────────

def parse_watchlist_csv(csv_text):
    """解析 IMDb 匯出的 CSV，回傳 tt ID 列表。"""
    ids, seen = [], set()
    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            tid = (row.get('Const') or row.get('tconst') or '').strip()
            if re.match(r'^tt\d+$', tid) and tid not in seen:
                seen.add(tid)
                ids.append(tid)
    except Exception:
        pass
    return ids


def download_poster(url, imdb_id):
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        ct = (resp.headers.get('content-type') or '').split(';')[0].strip()
        ext = {'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp'}.get(ct)
        if not ext:
            raw = url.split('?')[0].rsplit('.', 1)[-1].lower()
            ext = raw if raw in ('jpg', 'png', 'webp') else 'jpg'
        return f'{imdb_id}.{ext}', ContentFile(resp.content)
    except Exception:
        return None, None


def _sync_entry_db(data, zh_title, force_stars=True):
    """同步一筆動畫到資料庫，回傳 log 訊息。"""
    from .models import Ani, Person

    imdb_id = data.get('imdb_id')
    ani = Ani.objects.filter(IMDb_ID=imdb_id).first()
    is_new = ani is None
    if is_new:
        ani = Ani(IMDb_ID=imdb_id)

    filled = []

    if is_new:
        ani.title = data.get('title') or imdb_id
        if data.get('title'):
            filled.append('英文標題')
    elif data.get('title') and not ani.title:
        ani.title = data['title']
        filled.append('英文標題')

    if data.get('year') and not ani.year:
        ani.year = data['year']
        filled.append('年份')

    if data.get('imdb_stars') is not None and (force_stars or not ani.imdb_stars):
        ani.imdb_stars = data['imdb_stars']
        filled.append('評分')

    if data.get('status') == 'FINISHED' and not ani.status:
        ani.status = Ani.StatusChoices.FINISHED
        filled.append('狀態')

    if zh_title and not ani.title_zh:
        ani.title_zh = zh_title
        filled.append('繁中標題')

    ani.save()

    if data.get('poster_url') and not ani.poster:
        fname, content = download_poster(data['poster_url'], imdb_id)
        if content:
            ani.poster.save(fname, content, save=True)
            filled.append('海報')

    if data.get('creators') and not ani.creators.exists():
        for name in data['creators']:
            person, _ = Person.objects.get_or_create(name=name)
            ani.creators.add(person)
        filled.append('創作者')

    if data.get('description') and not ani.description:
        zh_desc = _translate_to_zh(data['description'])
        ani.description = zh_desc or data['description']
        ani.save(update_fields=['description'])
        filled.append('簡介')

    if is_new:
        return f'新增（{", ".join(filled) or "基本"}）'
    elif filled:
        return f'補齊 {", ".join(filled)}'
    else:
        return '無變更'


# ── Background job ─────────────────────────────────────────────────────────────

def _db_init_job(job_id, total):
    from .models import SyncJob
    SyncJob.objects.filter(id=job_id).update(
        status=SyncJob.Status.RUNNING, total=total
    )

def _db_append_log(job_id, text, extra=None):
    from .models import SyncJob
    job = SyncJob.objects.get(id=job_id)
    job.log += text
    fields = ['log']
    if extra:
        for k, v in extra.items():
            setattr(job, k, v)
            fields.append(k)
    job.save(update_fields=fields)

def _db_set_progress(job_id, progress, log_line):
    from .models import SyncJob
    job = SyncJob.objects.get(id=job_id)
    job.progress = progress
    job.log += log_line
    job.save(update_fields=['progress', 'log'])

def _db_finish(job_id):
    from .models import SyncJob
    SyncJob.objects.filter(id=job_id).update(
        status=SyncJob.Status.DONE,
        finished_at=timezone.now(),
    )

def _db_error(job_id, msg):
    from .models import SyncJob
    SyncJob.objects.filter(id=job_id).update(
        status=SyncJob.Status.ERROR,
        log=msg,
        finished_at=timezone.now(),
    )


def _db_filter_new(imdb_ids):
    """回傳清單中尚未在資料庫的 ID。"""
    from .models import Ani
    existing = set(
        Ani.objects.filter(IMDb_ID__in=imdb_ids).values_list('IMDb_ID', flat=True)
    )
    return [tid for tid in imdb_ids if tid not in existing]


def _db_needs(imdb_id, force_stars):
    """回傳該筆資料需要爬取哪些內容，新作品一律全爬。"""
    from .models import Ani
    ani = Ani.objects.filter(IMDb_ID=imdb_id).first()
    if ani is None:
        return {'main': True, 'releaseinfo': True}
    return {
        'main': (
            not ani.title or not ani.year or not ani.poster
            or not ani.creators.exists() or not ani.description
            or (force_stars or not ani.imdb_stars)
        ),
        'releaseinfo': not ani.title_zh,
    }


async def _async_run_job(job_id, imdb_ids, force_stars=True,
                         new_only=False, smart_scan=False):
    from asgiref.sync import sync_to_async
    import functools

    db_init        = sync_to_async(_db_init_job)
    db_log         = sync_to_async(_db_append_log)
    db_progress    = sync_to_async(_db_set_progress)
    db_finish      = sync_to_async(_db_finish)
    db_error       = sync_to_async(_db_error)
    db_entry       = sync_to_async(functools.partial(_sync_entry_db, force_stars=force_stars))
    db_filter_new  = sync_to_async(_db_filter_new)
    db_needs       = sync_to_async(_db_needs)

    await db_init(job_id, len(imdb_ids))

    p = browser = None
    try:
        await db_log(job_id, '正在啟動瀏覽器...\n')
        p, browser, page = await _async_make_browser()
        await db_log(job_id, '瀏覽器就緒\n')

        # 解析 watchlist sentinel → 真正的 ID 列表
        if len(imdb_ids) == 1 and imdb_ids[0].startswith('__watchlist__'):
            wl_url = imdb_ids[0][len('__watchlist__'):]
            await db_log(job_id, '正在抓取 Watchlist...\n')
            imdb_ids = await _async_fetch_watchlist_ids(page, wl_url)
            if not imdb_ids:
                raise RuntimeError('Watchlist 為空或無法解析')
            await db_log(job_id, f'Watchlist 共 {len(imdb_ids)} 筆\n')

        # 僅新作品模式：預先過濾已存在的 ID
        if new_only:
            before = len(imdb_ids)
            imdb_ids = await db_filter_new(imdb_ids)
            skipped = before - len(imdb_ids)
            await db_log(job_id,
                f'已過濾 {skipped} 筆既有作品，剩 {len(imdb_ids)} 筆待新增\n',
                extra={'total': len(imdb_ids)})
        else:
            await db_log(job_id, f'共 {len(imdb_ids)} 筆，開始同步\n',
                         extra={'total': len(imdb_ids)})

        if not imdb_ids:
            await db_finish(job_id)
            return

        for i, tid in enumerate(imdb_ids):
            try:
                if smart_scan:
                    needs = await db_needs(tid, force_stars)
                    if not needs['main'] and not needs['releaseinfo']:
                        line = f'[{tid}] 略過（欄位已完整）\n'
                        await db_progress(job_id, i + 1, line)
                        continue
                else:
                    needs = {'main': True, 'releaseinfo': True}

                data = await _async_scrape_title(page, tid) if needs['main'] else None
                if data or not needs['main']:
                    zh = await _async_scrape_zh_title(page, tid) if needs['releaseinfo'] else None
                    if data:
                        msg = await db_entry(data, zh)
                        label = data.get('title') or tid
                    else:
                        # main 不需爬但 releaseinfo 需要時
                        msg = await db_entry({'imdb_id': tid}, zh)
                        label = tid
                else:
                    msg, label = '抓取失敗', tid
                line = f'[{tid}] {label} → {msg}\n'
            except Exception as e:
                line = f'[{tid}] 錯誤：{e}\n'

            await db_progress(job_id, i + 1, line)

        await db_finish(job_id)

    except Exception as e:
        import traceback
        await db_error(job_id,
            f'致命錯誤：{type(e).__name__}: {e}\n\n{traceback.format_exc()}')
    finally:
        try:
            if browser:
                await browser.close()
            if p:
                await p.stop()
        except Exception:
            pass


def _run_job(job_id, imdb_ids, force_stars=True, new_only=False, smart_scan=False):
    close_old_connections()
    try:
        asyncio.run(_async_run_job(
            job_id, imdb_ids,
            force_stars=force_stars,
            new_only=new_only,
            smart_scan=smart_scan,
        ))
    finally:
        close_old_connections()


def start_sync(imdb_ids, force_stars=True, new_only=False, smart_scan=False):
    """建立 SyncJob 並啟動背景執行緒，回傳 job_id。"""
    from .models import SyncJob
    job = SyncJob.objects.create(total=len(imdb_ids))
    threading.Thread(
        target=_run_job,
        args=(job.id, list(imdb_ids)),
        kwargs={'force_stars': force_stars, 'new_only': new_only, 'smart_scan': smart_scan},
        daemon=True,
    ).start()
    return job.id
