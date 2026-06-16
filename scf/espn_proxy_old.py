# -*- coding: utf8 -*-
# 腾讯云 SCF Web函数 - ESPN CORS 代理（强制Google DNS解析）
import json
import urllib.request
import socket
import struct
import os

# ========== 强制使用 Google DNS 8.8.8.8 解析 ESPN 域名 ==========
# 解决腾讯云内网 DNS 解析 ESPN API 域名返回错误 CDN 节点的问题
def google_dns_resolve(hostname):
    """通过 Google DNS 8.8.8.8 解析域名，返回 IPv4 地址"""
    txn_id = os.urandom(2)
    header = txn_id + struct.pack('>HHHHH', 0x0100, 1, 0, 0, 0)
    query = b''
    for label in hostname.split('.'):
        query += bytes([len(label)]) + label.encode()
    query += b'\x00' + struct.pack('>HH', 1, 1)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)
    try:
        sock.sendto(header + query, ('8.8.8.8', 53))
        data, _ = sock.recvfrom(1024)
        offset = 12
        while data[offset] != 0:
            offset += data[offset] + 1
        offset += 5
        offset += 2 + 2 + 4
        rdlen = struct.unpack('>H', data[offset:offset+2])[0]
        offset += 2
        if rdlen == 4:
            return '.'.join(str(b) for b in data[offset:offset+4])
    except Exception:
        pass
    finally:
        sock.close()
    return None

_original_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    if host and 'espn' in host.lower():
        ip = google_dns_resolve(host)
        if ip:
            return _original_getaddrinfo(ip, port, family, type, proto, flags)
    return _original_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _patched_getaddrinfo
# ========== DNS 修补结束 ==========

def main_handler(event, context):
    qs = (event.get('queryStringParameters') or 
          event.get('queryString') or 
          event.get('query') or {})
    
    if isinstance(qs, str):
        from urllib.parse import parse_qs
        qs = parse_qs(qs)
        qs = {k: v[0] for k, v in qs.items()}

    # ===== 路由：/predict =====
    path = (event.get('path') or '').strip()
    if path == '/predict' or qs.get('action','') == 'predict':
        from scf_predict import handle_predict
        result = handle_predict(qs)
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Cache-Control': 'no-cache',
            },
            'body': json.dumps(result, ensure_ascii=False)
        }

    target_url = qs.get('url', '') or ''

    if not target_url:
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'text/plain', 'Access-Control-Allow-Origin': '*'},
            'body': 'ESPN Proxy (Tencent SCF + Google DNS) is running'
        }

    try:
        req = urllib.request.Request(target_url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Encoding': 'identity',
            'Origin': 'https://baili026.github.io',
            'Referer': 'https://baili026.github.io/',
        })
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read().decode('utf-8')
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Cache-Control': 'public, max-age=30',
            },
            'body': data
        }
    except Exception as e:
        return {
            'statusCode': 502,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': str(e)})
        }
