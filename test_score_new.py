import sys
sys.path.insert(0, 'D:\\DemoProject')
from scf.main import predict_match

tests = [
    ('德国', '库拉索', 'A1'),
    ('巴西', '哥斯达黎加', 'A2'),
    ('法国', '瑞士', 'A3'),
    ('阿根廷', '墨西哥', 'C1'),
]
for home, away, mid in tests:
    r = predict_match(home, away, mid)
    la = r.get('lambda', {})
    print(f'{home} vs {away}')
    print(f'  scoreA={r["score"]}  scoreB={r.get("scoreB","")}  scoreC={r.get("scoreC","")}')
    print(f'  λH={la.get("home",0):.2f}  λA={la.get("away",0):.2f}')
    print()
