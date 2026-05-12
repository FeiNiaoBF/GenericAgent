"""
skill_scraper.py - 批量抓取外部技能/资源详情
用法: python skill_scraper.py <url1> <url2> ... [--output FILE]
"""
import sys, json, os, time
import requests
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'temp')
os.makedirs(OUTPUT_DIR, exist_ok=True)


def scrape_skill(url: str) -> dict:
    """抓取单个skill详情页，自动处理SSR和SPA"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # 提取标题
        title = soup.title.string.strip() if soup.title else url.split('/')[-1]

        # 尝试从script#__NEXT_DATA__提取JSON内容(SSR页面)
        next_data = soup.find('script', id='__NEXT_DATA__')
        content = ''
        if next_data:
            try:
                data = json.loads(next_data.string)
                # 递归搜索prompt字段
                content = _find_prompt(json.dumps(data))
            except:
                pass

        # 回退: 提取页面可见文本
        if not content:
            for tag in soup(['script', 'style', 'nav', 'footer']):
                tag.decompose()
            content = soup.get_text(separator='\n', strip=True)[:5000]

        return {
            'url': url,
            'title': title,
            'content': content[:8000],
            'scraped_at': datetime.now().isoformat(),
            'status': 'ok'
        }
    except Exception as e:
        return {'url': url, 'title': '', 'content': '', 'status': f'error: {e}'}


def _find_prompt(text: str) -> str:
    """从JSON文本中递归搜索prompt字段"""
    try:
        data = json.loads(text) if isinstance(text, str) else text
    except:
        return ''
    if isinstance(data, dict):
        for key in ['prompt', 'instructions', 'content', 'description']:
            if key in data and isinstance(data[key], str) and len(data[key]) > 50:
                return data[key]
        for v in data.values():
            r = _find_prompt(v)
            if r:
                return r
    elif isinstance(data, list):
        for item in data:
            r = _find_prompt(item)
            if r:
                return r
    return ''


def batch_scrape(urls: list, output_file: str = None) -> list:
    """批量抓取，间隔0.5s防限流"""
    results = []
    for i, url in enumerate(urls):
        print(f'[{i+1}/{len(urls)}] 抓取: {url}')
        result = scrape_skill(url)
        results.append(result)
        if i < len(urls) - 1:
            time.sleep(0.5)

    if output_file:
        path = os.path.join(OUTPUT_DIR, output_file)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f'\n✅ 已保存 {len(results)} 条结果到 {path}')

    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='批量抓取skill详情')
    parser.add_argument('urls', nargs='*', help='要抓取的URL列表')
    parser.add_argument('--output', '-o', default='scraped_skills.json', help='输出文件名')
    parser.add_argument('--input', '-i', help='从文件读取URL列表(每行一个)')
    args = parser.parse_args()

    urls = list(args.urls)
    if args.input:
        with open(args.input, 'r') as f:
            urls.extend([line.strip() for line in f if line.strip() and not line.startswith('#')])

    if not urls:
        print('用法: python skill_scraper.py <url1> <url2> ...')
        print('  或: python skill_scraper.py --input urls.txt -o output.json')
        sys.exit(1)

    batch_scrape(urls, args.output)
