# -*- coding: utf-8 -*-
# 腾讯云 SCF Web函数 - 赛果/预测/爆冷 数据读写代理
# 数据存储：GitHub (data/results.json, data/predictions.json, data/upsets.json)
import json
import os
import base64
import urllib.request
import urllib.parse

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO = 'BAILG-git/worldcup-26'
BRANCH = 'main'

def github_api(url, method='GET', body=None):
    """调用 GitHub REST API"""
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, headers={
        'User-Agent': 'worldcup-scf',
        'Authorization': f'Bearer {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
    })
    req.get_method = lambda: method
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        return json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode('utf-8'))

def read_json(file_path):
    """从 GitHub 读取 JSON 文件"""
    if not GITHUB_TOKEN:
        return {}
    url = f'https://api.github.com/repos/{REPO}/contents/{file_path}'
    try:
        meta = github_api(url, 'GET')
        content = meta.get('content', '')
        sha = meta.get('sha', '')
        if content:
            data = json.loads(base64.b64decode(content).decode('utf-8'))
            return {'data': data, 'sha': sha}
    except Exception as e:
        print(f'read_json error: {e}')
    return {'data': {}, 'sha': ''}

def write_json(file_path, data, msg):
    """写 JSON 到 GitHub"""
    if not GITHUB_TOKEN:
        return {'error': 'GITHUB_TOKEN not configured'}
    url = f'https://api.github.com/repos/{REPO}/contents/{file_path}'
    existing = read_json(file_path)
    sha = existing.get('sha', '')
    content = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')).decode('utf-8')
    body = {'message': msg, 'content': content, 'branch': BRANCH}
    if sha:
        body['sha'] = sha
    result = github_api(url, 'PUT', body)
    if result.get('content'):
        return {'ok': True}
    return {'error': result.get('message', 'write failed')}

# ========== /results ==========
def handle_results_get():
    result = read_json('data/results.json')
    return result.get('data', {})

def handle_results_post(body):
    # body: { matchId: { score:[h,a], ht:[h,a] } }
    existing = read_json('data/results.json').get('data', {})
    existing.update(body)
    return write_json('data/results.json', existing, f'update results via SCF')

# ========== /predictions ==========
def handle_predictions_get():
    result = read_json('data/predictions.json')
    return result.get('data', {})

def handle_predictions_post(body):
    # body: { matchId: { score:['1:0','2:0'], wdl:['主胜'], goals:['2','3'] } }
    existing = read_json('data/predictions.json').get('data', {})
    existing.update(body)
    return write_json('data/predictions.json', existing, f'update predictions via SCF')

# ========== /upsets (保留原有逻辑) ==========
UPSETS_PATH = 'data/upsets.json'
def handle_upsets_get():
    result = read_json(UPSETS_PATH)
    return result.get('data', {})

def handle_upsets_post(body):
    existing = read_json(UPSETS_PATH).get('data', {})
    existing.update(body)
    return write_json(UPSETS_PATH, existing, f'update upsets via SCF')

# ========== SCF 主入口 ==========
def main_handler(event, context):
    qs = (event.get('queryStringParameters') or
          event.get('queryString') or
          event.get('query') or {}))
    if isinstance(qs, str):
        qs = dict(urllib.parse.parse_qsl(qs))

    path = (event.get('path') or '').strip()
    method = (event.get('httpMethod') or 'GET').upper()

    cors_headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }

    if method == 'OPTIONS':
        return {'statusCode': 204, 'headers': cors_headers, 'body': ''}

    # /results
    if '/results' in path:
        if method == 'GET':
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps(handle_results_get(), ensure_ascii=False)}
        if method == 'POST':
            try:
                raw_body = event.get('body', '{}') or '{}'
                payload = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
                result = handle_results_post(payload)
            except Exception as e:
                result = {'error': str(e)}
            return {'statusCode': 200 if result.get('ok') else 500, 'headers': cors_headers, 'body': json.dumps(result, ensure_ascii=False)}

    # /predictions
    if '/predictions' in path:
        if method == 'GET':
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps(handle_predictions_get(), ensure_ascii=False)}
        if method == 'POST':
            try:
                raw_body = event.get('body', '{}') or '{}'
                payload = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
                result = handle_predictions_post(payload)
            except Exception as e:
                result = {'error': str(e)}
            return {'statusCode': 200 if result.get('ok') else 500, 'headers': cors_headers, 'body': json.dumps(result, ensure_ascii=False)}

    # /upsets
    if '/upsets' in path:
        if method == 'GET':
            return {'statusCode': 200, 'headers': cors_headers, 'body': json.dumps(handle_upsets_get(), ensure_ascii=False)}
        if method == 'POST':
            try:
                raw_body = event.get('body', '{}') or '{}'
                payload = json.loads(raw_body) if isinstance(raw_body, str) else raw_body
                result = handle_upsets_post(payload)
            except Exception as e:
                result = {'error': str(e)}
            return {'statusCode': 200 if result.get('ok') else 500, 'headers': cors_headers, 'body': json.dumps(result, ensure_ascii=False)}

    # 调试
    return {'statusCode': 200, 'headers': cors_headers,
            'body': json.dumps({'msg': 'World Cup SCF v3', 'path': path, 'method': method}, ensure_ascii=False)}
