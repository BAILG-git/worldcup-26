# -*- coding: utf8 -*-
# 预测引擎 v15.3 - Python版（运行在SCF）
# 从 index.html 的 predictMatch() 移植

import math
import json

# ========== 球队数据（与 index.html TEAM_DATA 同步） ==========
# 格式: {name: {value, rank, attack, defense, style}}
TEAM_PROFILE = {
    # 欧洲
    '德国':   {'value':'8.5亿欧','rank':4, 'attack':7.5,'defense':7.5,'style':'整体压迫'},
    '法国':   {'value':'7.8亿欧','rank':3, 'attack':7.2,'defense':6.5,'style':'防守反击'},
    '英格兰': {'value':'9.2亿欧','rank':5, 'attack':7.0,'defense':6.8,'style':'高压逼抢'},
    '西班牙': {'value':'6.5亿欧','rank':8, 'attack':7.8,'defense':6.0,'style':'传控'},
    '葡萄牙':{'value':'5.8亿欧','rank':7, 'attack':7.0,'defense':6.2,'style':'控球'},
    '荷兰':  {'value':'4.2亿欧','rank':6, 'attack':6.8,'defense':6.5,'style':'高压逼抢'},
    '意大利':{'value':'3.8亿欧','rank':9, 'attack':6.0,'defense':7.2,'style':'整体压迫'},
    '比利时':{'value':'3.5亿欧','rank':10,'attack':6.5,'defense':6.0,'style':'防守反击'},
    '克罗地亚':{'value':'2.1亿欧','rank':12,'attack':6.2,'defense':6.5,'style':'控球'},
    '瑞士':  {'value':'1.8亿欧','rank':18,'attack':6.0,'defense':6.8,'style':'稳守反击'},
    '丹麦':  {'value':'2.5亿欧','rank':19,'attack':6.2,'defense':6.8,'style':'整体压迫'},
    '波兰':  {'value':'1.2亿欧','rank':25,'attack':5.8,'defense':6.0,'style':'防守反击'},
    '奥地利':{'value':'2.8亿欧','rank':22,'attack':6.5,'defense':6.2,'style':'高压逼抢'},
    '乌克兰':{'value':'1.5亿欧','rank':24,'attack':6.0,'defense':6.0,'style':'稳守反击'},
    '捷克':  {'value':'1.1亿欧','rank':36,'attack':5.8,'defense':6.5,'style':'稳守反击'},
    '匈牙利':{'value':'1.0亿欧','rank':38,'attack':5.5,'defense':6.8,'style':'稳守反击'},
    '罗马尼亚':{'value':'0.8亿欧','rank':45,'attack':5.2,'defense':6.2,'style':'稳守反击'},
    '塞尔维亚':{'value':'1.8亿欧','rank':26,'attack':6.2,'defense':5.8,'style':'高压逼抢'},
    # 南美
    '巴西':   {'value':'7.2亿欧','rank':1, 'attack':7.5,'defense':6.2,'style':'高压逼抢'},
    '阿根廷': {'value':'5.5亿欧','rank':2, 'attack':7.0,'defense':6.0,'style':'控球'},
    '乌拉圭': {'value':'2.8亿欧','rank':15,'attack':6.5,'defense':6.8,'style':'稳守反击'},
    '厄瓜多尔':{'value':'1.5亿欧','rank':30,'attack':6.0,'defense':6.2,'style':'高压逼抢'},
    '哥伦比亚':{'value':'1.8亿欧','rank':16,'attack':6.5,'defense':6.0,'style':'控球'},
    '智利':   {'value':'1.2亿欧','rank':31,'attack':6.0,'defense':5.8,'style':'高压逼抢'},
    '秘鲁':   {'value':'0.6亿欧','rank':40,'attack':5.5,'defense':6.0,'style':'稳守反击'},
    '巴拉圭': {'value':'0.7亿欧','rank':48,'attack':5.2,'defense':6.5,'style':'稳守反击'},
    # 中北美
    '美国':     {'value':'2.5亿欧','rank':11,'attack':6.5,'defense':6.2,'style':'高压逼抢'},
    '墨西哥':   {'value':'1.5亿欧','rank':14,'attack':6.2,'defense':6.0,'style':'稳守反击'},
    '加拿大':   {'value':'1.2亿欧','rank':42,'attack':5.8,'defense':6.5,'style':'稳守反击'},
    '哥斯达黎加':{'value':'0.4亿欧','rank':50,'attack':5.0,'defense':6.0,'style':'稳守反击'},
    # 亚洲
    '日本':   {'value':'1.8亿欧','rank':17,'attack':6.5,'defense':5.8,'style':'高压逼抢'},
    '韩国':   {'value':'1.2亿欧','rank':23,'attack':6.2,'defense':5.5,'style':'防守反击'},
    '澳大利亚':{'value':'0.9亿欧','rank':27,'attack':5.8,'defense':6.2,'style':'整体压迫'},
    '伊朗':   {'value':'0.5亿欧','rank':20,'attack':5.5,'defense':6.5,'style':'稳守反击'},
    '沙特':   {'value':'0.4亿欧','rank':53,'attack':5.0,'defense':5.8,'style':'控球'},
    '卡塔尔': {'value':'0.3亿欧','rank':55,'attack':5.2,'defense':5.5,'style':'控球'},
    # 非洲
    '塞内加尔':{'value':'1.0亿欧','rank':21,'attack':6.0,'defense':6.0,'style':'防守反击'},
    '摩洛哥': {'value':'1.5亿欧','rank':13,'attack':6.2,'defense':6.2,'style':'防守反击'},
    '加纳':   {'value':'0.5亿欧','rank':60,'attack':5.5,'defense':5.5,'style':'高压逼抢'},
    '喀麦隆': {'value':'0.8亿欧','rank':38,'attack':5.8,'defense':5.8,'style':'高压逼抢'},
    '突尼斯': {'value':'0.4亿欧','rank':46,'attack':5.2,'defense':6.0,'style':'稳守反击'},
    '埃及':   {'value':'0.8亿欧','rank':33,'attack':5.8,'defense':5.5,'style':'防守反击'},
    '南非':   {'value':'0.5亿欧','rank':56,'attack':5.5,'defense':5.8,'style':'高压逼抢'},
    '科特迪瓦':{'value':'0.9亿欧','rank':32,'attack':6.0,'defense':5.8,'style':'高压逼抢'},
    # 大洋洲
    '新西兰': {'value':'0.3亿欧','rank':65,'attack':4.8,'defense':5.5,'style':'稳守反击'},
    # 友谊赛弱队（补全）
    '库拉索':   {'value':'0.26亿欧','rank':90,'attack':4.0,'defense':4.5,'style':'稳守反击'},
    '直布罗陀': {'value':'0.02亿欧','rank':200,'attack':3.0,'defense':3.5,'style':'稳守反击'},
}

STYLE_COUNTER = {
    '整体压迫': {'beat':['防守反击','稳守反击'], 'lost':['传控','控球']},
    '高压逼抢': {'beat':['稳守反击','防守反击'], 'lost':['传控','控球']},
    '传控':   {'beat':['整体压迫','高压逼抢'], 'lost':['稳守反击','防守反击']},
    '控球':   {'beat':['整体压迫','高压逼抢'], 'lost':['稳守反击','防守反击']},
    '防守反击': {'beat':['传控','控球'],       'lost':['整体压迫','高压逼抢']},
    '稳守反击': {'beat':['传控','控球'],       'lost':['高压逼抢','整体压迫']},
}

CONT_MAP = {
    '西班牙':'EU','德国':'EU','法国':'EU','英格兰':'EU','葡萄牙':'EU','荷兰':'EU',
    '意大利':'EU','比利时':'EU','克罗地亚':'EU','瑞士':'EU','波兰':'EU','奥地利':'EU',
    '乌克兰':'EU','捷克':'EU','匈牙利':'EU','罗马尼亚':'EU','塞尔维亚':'EU','丹麦':'EU',
    '巴西':'SA','阿根廷':'SA','乌拉圭':'SA','厄瓜多尔':'SA','哥伦比亚':'SA','智利':'SA',
    '秘鲁':'SA','巴拉圭':'SA',
    '美国':'NA','墨西哥':'NA','加拿大':'NA','哥斯达黎加':'NA',
    '日本':'AS','韩国':'AS','澳大利亚':'AS','伊朗':'AS','沙特':'AS','卡塔尔':'AS',
    '加纳':'AF','摩洛哥':'AF','喀麦隆':'AF','塞内加尔':'AF','突尼斯':'AF',
    '埃及':'AF','南非':'AF','科特迪瓦':'AF',
    '新西兰':'OC',
}

def parse_val(v):
    if not v or not isinstance(v, str): return 1.0
    v = v.strip()
    import re
    m = re.search(r'([\d\.]+)', v)
    if not m: return 1.0
    num = float(m.group(1))
    if '亿' in v: return num * 100
    if '万' in v: return num / 100
    return num

def style_matchup(h_style, a_style):
    if h_style in STYLE_COUNTER and a_style in STYLE_COUNTER.get(h_style, {}).get('beat', []):
        return 0.18
    if a_style in STYLE_COUNTER and h_style in STYLE_COUNTER.get(a_style, {}).get('beat', []):
        return -0.18
    return 0.0

def poisson_p(k, lam):
    """泊松概率 P(X=k) for lambda=lam, 数值稳定版"""
    if lam <= 0: return 0.0
    if k < 0: return 0.0
    # 用 log 避免溢出: log(P) = -lam + k*log(lam) - log(k!)
    # log(k!) = lgamma(k+1)
    import math as m
    logp = -lam + k * m.log(lam) - m.lgamma(k + 1)
    return m.exp(logp)

def poisson_win(lH, lA, side, max_goals=12):
    """计算胜平负概率，循环到 max_goals"""
    pH, pD, pA = 0.0, 0.0, 0.0
    for hg in range(max_goals + 1):
        ph = poisson_p(hg, lH)
        for ag in range(max_goals + 1):
            p = ph * poisson_p(ag, lA)
            if hg > ag: pH += p
            elif hg < ag: pA += p
            else: pD += p
    total = pH + pD + pA
    if total <= 0: total = 1.0
    # 归一化（防止浮点误差）
    pH /= total; pD /= total; pA /= total
    if side == 'home': return pH
    if side == 'away': return pA
    return pD

def predict_match(home, away, match_id='', injuries=None, suspended=None):
    """
    预测单场比赛，返回预测结果 dict
    injuries: {home: [{position:'前锋'}, ...], away: [...]}
    suspended: {home: [...], away: [...]}
    """
    td = TEAM_PROFILE
    h = td.get(home) or {'value':'1亿欧','rank':50,'attack':5.5,'defense':5.5,'style':'整体压迫'}
    a = td.get(away) or {'value':'1亿欧','rank':50,'attack':5.5,'defense':5.5,'style':'整体压迫'}

    hv = parse_val(h.get('value','1亿欧'))
    av = parse_val(a.get('value','1亿欧'))
    hr = h.get('rank', 50)
    ar = a.get('rank', 50)
    hs = {'attack': h.get('attack',5.5), 'defense': h.get('defense',5.5), 'style': h.get('style','整体压迫')}
    asp = {'attack': a.get('attack',5.5), 'defense': a.get('defense',5.5), 'style': a.get('style','整体压迫')}

    # 伤停
    h_inj = (injuries or {}).get('home', []) if isinstance(injuries, dict) else []
    a_inj = (injuries or {}).get('away', []) if isinstance(injuries, dict) else []
    h_sus = len((suspended or {}).get('home', [])) if isinstance(suspended, dict) else 0
    a_sus = len((suspended or {}).get('away', [])) if isinstance(suspended, dict) else 0

    # ===== 第一层：四维度打分 =====
    is_host = (h.get('is_host', False) or home in ['美国','墨西哥','加拿大'])
    is_knockout = any(x in match_id for x in ['r32','r16','qf','sf','final'])
    defending_champ = '阿根廷'

    # 硬实力
    eloH = math.log10(max(hv, 0.01)) * 30 + 1300
    eloA = math.log10(max(av, 0.01)) * 30 + 1300
    eloDiff = eloH - eloA
    rSH = max(0, 100 - hr)
    rSA = max(0, 100 - ar)
    hard_bonus = 0
    if is_host: hard_bonus += 8
    if home == defending_champ and not is_knockout: hard_bonus -= 5
    if away == defending_champ and not is_knockout: hard_bonus += 5

    hardScoreH = ((eloDiff > 0 and 58 or 42) + (rSH - rSA) * 0.8 + (hs['attack'] - asp['attack']) * 3.5 + (hs['defense'] - asp['defense']) * 2.5 + hard_bonus) * 0.40

    # 近期状态
    formH = (hs['attack'] / max(hs['defense'], 1)) * 10
    formA = (asp['attack'] / max(asp['defense'], 1)) * 10
    cH = rSH / (hv * 0.5 + 10) if hv > 0 else 0.5
    cA = rSA / (av * 0.5 + 10) if av > 0 else 0.5
    formBonusH, formBonusA = 0, 0
    if hs['defense'] >= 7.5 and hs['attack'] <= 4.0: formBonusA -= 12
    if asp['defense'] >= 7.5 and asp['attack'] <= 4.0: formBonusH -= 12
    if hs['defense'] >= 8.0: formBonusH += 15
    if asp['defense'] >= 8.0: formBonusA += 15
    recentScore = ((formH - formA + formBonusH - formBonusA) + (cH - cA) * 5) * 0.25

    # 交锋克制
    style_bonus = style_matchup(hs['style'], asp['style'])
    cont_h = CONT_MAP.get(home, '??')
    cont_a = CONT_MAP.get(away, '??')
    is_same_continent = (cont_h == cont_a)
    h2h_penalty = 0
    if style_bonus < -0.15 and abs(eloDiff) < 150: h2h_penalty = -0.10
    h2hScore = (style_bonus + (0.05 if is_same_continent else 0) + h2h_penalty) * 0.15

    # 临场修正
    def classify_injuries(inj_list):
        fwd, mid, df = 0, 0, 0
        for i in inj_list:
            pos = (i.get('position','') or i.get('role','') or '')
            if any(k in pos for k in ['前锋','中锋','边锋','影锋','攻击手','射手']): fwd += 1
            elif any(k in pos for k in ['后腰','前腰','中场','组织']): mid += 1
            elif any(k in pos for k in ['后卫','中卫','边卫','门将']): df += 1
            else: fwd += 1
        return fwd, mid, df

    h_fwd, h_mid, h_def = classify_injuries(h_inj)
    a_fwd, a_mid, a_def = classify_injuries(a_inj)
    injury_impact = (-(h_fwd + h_mid + h_def) * 0.08 + (a_fwd + a_mid + a_def) * 0.08 - h_sus * 0.06 + a_sus * 0.06) * 0.20

    # 战意
    gp_parts = match_id.replace('-','_').split('_')
    is_group = len(gp_parts) >= 2 and gp_parts[0] in 'ABCDEFGHIJKL' and gp_parts[1].isdigit()
    g_round = int(gp_parts[1]) if is_group else 0
    if not is_group:
        if 'r32' in match_id: g_round = 10
        elif 'r16' in match_id: g_round = 11
        elif 'qf' in match_id: g_round = 12
        elif 'sf' in match_id: g_round = 13
        elif 'final' in match_id: g_round = 14

    mot_map = {1:1.0, 2:1.12, 3:1.30, 10:1.25, 11:1.30, 12:1.35, 13:1.40, 14:1.45}
    motivation = mot_map.get(g_round, 1.10)
    mot_label = {1:'首轮',2:'关键战',3:'生死战'}.get(g_round, '常规')
    mot_impact = (motivation - 1) * 8 * 0.20

    site_bonus = 0
    if g_round >= 3: site_bonus += 10
    site_impact = site_bonus * 0.20

    home_score = (6 if is_host else 2) * 0.20

    deltaS = hardScoreH + recentScore + h2hScore + injury_impact + mot_impact + home_score + site_impact

    # ===== 第二层：泊松λ计算 =====
    AvgHG, AvgAG = 1.65, 1.35
    homeAtkNorm = hs['attack'] / 5.5
    awayDefWeak = 5.5 / max(asp['defense'], 1)
    awayAtkNorm = asp['attack'] / 5.5
    homeDefWeak = 5.5 / max(hs['defense'], 1)

    # K1
    if deltaS > 0:
        K1 = min(math.pow(1.06, deltaS / 15), math.pow(1.06, 3))
    else:
        K1 = max(0.82, 1 + deltaS / 350)

    # K2
    K2 = 1.2 if (is_host and not is_knockout) else 1.0

    # K3 伤停
    KH3 = 1.0
    KA3 = 1.0
    KH3 -= h_fwd * 0.30 + h_mid * 0.15
    KA3 += h_def * 0.25
    KA3 -= a_fwd * 0.30 + a_mid * 0.15
    KH3 += a_def * 0.25
    KH3 = max(0.4, KH3)
    KA3 = max(0.4, KA3)
    KH3 -= h_sus * 0.20
    KA3 -= a_sus * 0.20
    KH3 = max(0.4, KH3)
    KA3 = max(0.4, KA3)
    if motivation >= 1.28:
        KH3 += 0.15
        KA3 += 0.15

    # K4 战术克制
    K4 = 1.0
    h_offensive = any(k in hs['style'] for k in ['高压','传控','控球'])
    a_defensive = any(k in asp['style'] for k in ['防守','反击','稳守'])
    a_offensive = any(k in asp['style'] for k in ['高压','传控','控球'])
    h_defensive = any(k in hs['style'] for k in ['防守','反击','稳守'])
    if h_offensive and a_defensive: K4 = 0.95
    if a_offensive and h_defensive: K4 = 0.95

    # λ 最终
    lambdaH = max(0.3, min(AvgHG * homeAtkNorm * awayDefWeak * K1 * K2 * KH3 * K4, 4.5))
    lambdaA = max(0.2, min(AvgAG * awayAtkNorm * homeDefWeak * K1 * KA3 * K4, 4.0))

    # WC 专属修正
    wc_note = ''
    if (g_round == 1 or g_round == 2) and abs(deltaS) > 15:
        lambdaH = max(0.3, lambdaH - 0.15)
        lambdaA = max(0.2, lambdaA - 0.15)
        wc_note = '出线无忧保守'
    if g_round >= 3:
        lambdaH = min(4.5, lambdaH + 0.25)
        lambdaA = min(4.0, lambdaA + 0.25)
        wc_note = wc_note + '·第三轮生死战' if wc_note else '第三轮生死战'
    if is_same_continent and not wc_note:
        wc_note = '同大洲交锋'
    if is_knockout:
        wc_note = ('淘汰赛·' + wc_note) if wc_note else '淘汰赛'

    # ===== 泊松矩阵 & 双比分 =====
    probs = []
    for hg in range(6):
        for ag in range(6):
            p = poisson_p(hg, lambdaH) * poisson_p(ag, lambdaA)
            if p >= 0.005:
                probs.append({'hg': hg, 'ag': ag, 'p': p})
    probs.sort(key=lambda x: -x['p'])

    # 淘汰赛平局上浮
    if is_knockout:
        for pb in probs:
            if pb['hg'] == pb['ag']:
                pb['p'] *= 1.05

    # 同大洲平局上浮
    if is_same_continent:
        for pb in probs:
            if pb['hg'] == pb['ag']:
                pb['p'] *= 1.02

    s1 = probs[0] if probs else {'hg':1,'ag':1,'p':0.01}
    s1_wdl = 'H' if s1['hg'] > s1['ag'] else ('A' if s1['hg'] < s1['ag'] else 'D')
    s2 = None
    for p in probs:
        pw = 'H' if p['hg'] > p['ag'] else ('A' if p['hg'] < p['ag'] else 'D')
        if pw != s1_wdl:
            s2 = p
            break
    if not s2:
        s2 = probs[1] if len(probs) > 1 else {'hg':s1['hg'],'ag':s1['ag']+1,'p':0.01}

    scoreA = f"{s1['hg']}-{s1['ag']}"
    scoreB = f"{s2['hg']}-{s2['ag']}"

    # 胜平负概率
    probH = poisson_win(lambdaH, lambdaA, 'home')
    probD = poisson_win(lambdaH, lambdaA, 'draw')
    probA = poisson_win(lambdaH, lambdaA, 'away')

    # 赛果
    hg_f, ag_f = s1['hg'], s1['ag']
    if hg_f > ag_f:
        wdl, wdl_label = '主胜', f"{home}·胜"
    elif hg_f < ag_f:
        wdl, wdl_label = '客胜', f"{away}·胜"
    else:
        wdl, wdl_label = '平局', '平局'

    # 总进球
    g_dist = {}
    for pb in probs:
        t = pb['hg'] + pb['ag']
        g_dist[t] = g_dist.get(t, 0) + pb['p']
    top_goals = sorted(g_dist.items(), key=lambda x: -x[1])[:2]
    top_goals_str = '/'.join(f"{t}球" for t,_ in top_goals) or '2球'

    exp_total = lambdaH + lambdaA
    goals_range = '小球' if exp_total <= 2 else ('中小球' if exp_total <= 3 else ('适中' if exp_total <= 3.5 else '大球'))

    conf = '高' if s1['p'] > 0.12 else ('低' if s1['p'] < 0.06 else '中')

    # 分析文本
    strong_name = home if deltaS > 0 else away
    reasons = []
    if abs(deltaS) > 18:
        reasons.append(f"【实力】{strong_name}全面占优（ΔS={round(deltaS)}）")
    elif abs(deltaS) > 8:
        reasons.append(f"【实力】{strong_name}占优（ΔS={round(deltaS)}）")
    else:
        reasons.append(f"【实力】势均力敌（ΔS={round(deltaS)}）")
    reasons.append(f"【攻防】{home}攻{hs['attack']}/守{hs['defense']} vs {away}攻{asp['attack']}/守{asp['defense']}")
    reasons.append(f"【打法】{hs['style']} vs {asp['style']}")
    reasons.append(f"【战意】{mot_label}" + (f" · {wc_note}" if wc_note else ''))
    sp = []
    if h_fwd: sp.append(f"{home}前锋伤{h_fwd}")
    if a_fwd: sp.append(f"{away}前锋伤{a_fwd}")
    if h_sus: sp.append(f"{home}停{h_sus}")
    if a_sus: sp.append(f"{away}停{a_sus}")
    reasons.append(f"【伤停】{';'.join(sp) if sp else '阵容完整'}")
    if is_host:
        reasons.append(f"【主场】{home}东道主（K2={K2}）")
    reasons.append(f"【概率】胜{round(probH*100)}% 平{round(probD*100)}% 负{round(probA*100)}%")
    reasons.append(f"【预期】λH={lambdaH:.2f} λA={lambdaA:.2f} | 总进{exp_total:.1f}球（{goals_range}）")
    reasons.append(f"【比分】①{scoreA}（{wdl_label}，{conf}） ②{scoreB}（备选）")

    return {
        'score': scoreA,
        'scoreB': scoreB,
        'wdl': wdl,
        'wdlLabel': wdl_label,
        'goals': top_goals_str + f'（{goals_range}）',
        'reason': '；'.join(reasons),
        'confidence': conf,
        'lambda': {'h': round(lambdaH, 3), 'a': round(lambdaA, 3), 'total': round(exp_total, 2)},
        'probH': round(probH, 4),
        'probD': round(probD, 4),
        'probA': round(probA, 4),
        'deltaS': round(deltaS, 1),
        'wcNote': wc_note,
    }

# ========== SCF 路由入口 ==========
def handle_predict(params):
    """处理 /predict 路由"""
    home = params.get('home', '') or params.get('h', '')
    away = params.get('away', '') or params.get('a', '')
    match_id = params.get('matchId', '') or params.get('id', '')
    if not home or not away:
        return {'error': 'missing home/away'}
    result = predict_match(home, away, match_id)
    return result

if __name__ == '__main__':
    # 测试
    r = predict_match('德国', '库拉索', 'A1')
    print(json.dumps(r, ensure_ascii=False, indent=2))
