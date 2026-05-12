#!/usr/bin/env python3
"""LLM代理管理 - 管理和切换LLM代理

SOP: llm_proxy_manage_sop.md
用途: 检查/切换/测试LLM代理连接
DIY: 一个脚本只做代理管理
"""

import json, sys
try:
    import urllib.request as req
except ImportError:
    import urllib2 as req

PROXY_LIST = {
    'local': 'http://localhost:15721',
    'newapi': 'http://localhost:3000',
    'cliproxy': 'http://localhost:8200',
}

def test_proxy(name, url):
    """测试代理连接"""
    try:
        resp = req.urlopen(url + '/v1/models', timeout=5)
        data = json.loads(resp.read())
        models = data.get('data', [])[:5]
        print('✅ %s (%s) 可用' % (name, url))
        for m in models:
            print('   🤖 %s' % m.get('id', 'unknown'))
        return True
    except Exception as e:
        print('❌ %s (%s) 不可用: %s' % (name, url, e))
        return False

def check_all():
    """检查所有代理"""
    print('🔍 检查所有LLM代理:')
    results = {}
    for name, url in PROXY_LIST.items():
        results[name] = test_proxy(name, url)
    available = sum(1 for v in results.values() if v)
    print()
    print('📊 %d/%d 可用' % (available, len(results)))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='LLM代理管理')
    parser.add_argument('action', choices=['check', 'test', 'list'], help='操作')
    parser.add_argument('--proxy', help='代理名称或URL')
    args = parser.parse_args()

    if args.action == 'check':
        check_all()
    elif args.action == 'test':
        proxy = args.proxy
        if proxy in PROXY_LIST:
            test_proxy(proxy, PROXY_LIST[proxy])
        elif proxy:
            test_proxy(proxy, proxy)
        else:
            print('⚠️ 请指定代理名称或URL')
    elif args.action == 'list':
        print('📋 可用代理:')
        for name, url in PROXY_LIST.items():
            print('  %s: %s' % (name, url))

if __name__ == '__main__':
    main()
