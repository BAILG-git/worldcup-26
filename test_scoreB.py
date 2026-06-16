import sys
sys.path.insert(0, '.')
from scf.main import predict_match
import json

# 测试德国 vs 库拉索
r = predict_match('德国', '库拉索', 'A1')
print('=== 德国 vs 库拉索 ===')
print(f"scoreA: {r['score']}")
print(f"scoreB: {r['scoreB']}")
print(f"scoreC: {r.get('scoreC', 'N/A')}")
print(f"probH: {r['probH']}, probD: {r['probD']}, probA: {r['probA']}")
print()

# 测试法国 vs 瑞士
r2 = predict_match('法国', '瑞士', 'A2')
print('=== 法国 vs 瑞士 ===')
print(f"scoreA: {r2['score']}")
print(f"scoreB: {r2['scoreB']}")
print(f"scoreC: {r2.get('scoreC', 'N/A')}")
print()

# 测试巴西 vs 哥斯达黎加
r3 = predict_match('巴西', '哥斯达黎加', 'G1')
print('=== 巴西 vs 哥斯达黎加 ===')
print(f"scoreA: {r3['score']}")
print(f"scoreB: {r3['scoreB']}")
print(f"scoreC: {r3.get('scoreC', 'N/A')}")
