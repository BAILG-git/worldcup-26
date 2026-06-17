"""
World Cup 2026 预测引擎 — Elo + 蒙特卡洛模拟
替代 Poisson 模型，输出静态 JSON 供前端读取
"""
import json
import math
import random
import os
from datetime import datetime

# ========== 1. 初始 Elo 评级 ==========
# 基于 FIFA 排名 + 身价 + 历史世界杯表现综合初始化
INITIAL_ELO = {
    # A组
    "墨西哥": 1720, "南非": 1480, "韩国": 1650, "捷克": 1580,
    # B组
    "加拿大": 1600, "波黑": 1520, "卡塔尔": 1460, "瑞士": 1730,
    # C组
    "巴西": 1920, "摩洛哥": 1780, "海地": 1380, "苏格兰": 1560,
    # D组
    "美国": 1750, "巴拉圭": 1540, "澳大利亚": 1570, "土耳其": 1630,
    # E组
    "德国": 1930, "库拉索": 1350, "科特迪瓦": 1620, "厄瓜多尔": 1660,
    # F组
    "荷兰": 1890, "日本": 1680, "瑞典": 1640, "突尼斯": 1550,
    # G组
    "比利时": 1800, "埃及": 1590, "伊朗": 1530, "新西兰": 1340,
    # H组
    "西班牙": 1960, "佛得角": 1440, "沙特阿拉伯": 1490, "乌拉圭": 1770,
    # I组
    "法国": 1980, "塞内加尔": 1700, "伊拉克": 1470, "挪威": 1650,
    # J组
    "阿根廷": 1940, "阿尔及利亚": 1580, "奥地利": 1640, "约旦": 1420,
    # K组
    "葡萄牙": 1910, "民主刚果": 1510, "乌兹别克斯坦": 1490, "哥伦比亚": 1720,
    # L组
    "英格兰": 1950, "克罗地亚": 1760, "加纳": 1500, "巴拿马": 1400,
}

# ========== 2. 比赛数据 ==========
GROUPS = {
    "A": ["墨西哥", "南非", "韩国", "捷克"],
    "B": ["加拿大", "波黑", "卡塔尔", "瑞士"],
    "C": ["巴西", "摩洛哥", "海地", "苏格兰"],
    "D": ["美国", "巴拉圭", "澳大利亚", "土耳其"],
    "E": ["德国", "库拉索", "科特迪瓦", "厄瓜多尔"],
    "F": ["荷兰", "日本", "瑞典", "突尼斯"],
    "G": ["比利时", "埃及", "伊朗", "新西兰"],
    "H": ["西班牙", "佛得角", "沙特阿拉伯", "乌拉圭"],
    "I": ["法国", "塞内加尔", "伊拉克", "挪威"],
    "J": ["阿根廷", "阿尔及利亚", "奥地利", "约旦"],
    "K": ["葡萄牙", "民主刚果", "乌兹别克斯坦", "哥伦比亚"],
    "L": ["英格兰", "克罗地亚", "加纳", "巴拿马"],
}

# [home_idx, away_idx, match_idx_in_group]
MATCH_TEMPLATE = [
    (0, 1, 0), (2, 3, 1), (0, 2, 2), (1, 3, 3), (0, 3, 4), (1, 2, 5)
]

# 球队风格数据（attack/defense 1-10）
STYLE_DATA = {
    "墨西哥": {"style": "快速转换", "attack": 7.5, "defense": 6.0},
    "南非": {"style": "稳守突击", "attack": 5.0, "defense": 6.5},
    "韩国": {"style": "快速转换", "attack": 7.0, "defense": 6.5},
    "捷克": {"style": "身体对抗", "attack": 6.5, "defense": 5.5},
    "加拿大": {"style": "高位逼抢", "attack": 6.5, "defense": 5.5},
    "波黑": {"style": "稳守突击", "attack": 5.5, "defense": 6.0},
    "卡塔尔": {"style": "技术传控", "attack": 5.0, "defense": 5.0},
    "瑞士": {"style": "防守反击", "attack": 6.5, "defense": 7.5},
    "巴西": {"style": "控球压迫", "attack": 9.5, "defense": 7.5},
    "摩洛哥": {"style": "防守反击", "attack": 7.0, "defense": 8.0},
    "海地": {"style": "稳守突击", "attack": 4.5, "defense": 4.5},
    "苏格兰": {"style": "身体对抗", "attack": 6.0, "defense": 6.5},
    "美国": {"style": "高位逼抢", "attack": 7.0, "defense": 6.5},
    "巴拉圭": {"style": "防守反击", "attack": 5.5, "defense": 6.0},
    "澳大利亚": {"style": "身体对抗", "attack": 5.5, "defense": 6.0},
    "土耳其": {"style": "高位逼抢", "attack": 7.0, "defense": 5.5},
    "德国": {"style": "高位逼抢", "attack": 9.0, "defense": 7.5},
    "库拉索": {"style": "技术传控", "attack": 4.5, "defense": 4.0},
    "科特迪瓦": {"style": "快速转换", "attack": 7.0, "defense": 5.5},
    "厄瓜多尔": {"style": "高位逼抢", "attack": 6.5, "defense": 6.0},
    "荷兰": {"style": "控球压迫", "attack": 8.5, "defense": 7.0},
    "日本": {"style": "技术传控", "attack": 7.5, "defense": 6.5},
    "瑞典": {"style": "身体对抗", "attack": 7.0, "defense": 6.0},
    "突尼斯": {"style": "防守反击", "attack": 5.5, "defense": 6.0},
    "比利时": {"style": "控球压迫", "attack": 8.0, "defense": 6.5},
    "埃及": {"style": "防守反击", "attack": 6.5, "defense": 6.0},
    "伊朗": {"style": "稳守突击", "attack": 5.5, "defense": 6.5},
    "新西兰": {"style": "身体对抗", "attack": 4.5, "defense": 5.5},
    "西班牙": {"style": "技术传控", "attack": 9.5, "defense": 8.0},
    "佛得角": {"style": "技术传控", "attack": 5.0, "defense": 5.0},
    "沙特阿拉伯": {"style": "技术传控", "attack": 5.0, "defense": 5.5},
    "乌拉圭": {"style": "快速转换", "attack": 7.5, "defense": 7.0},
    "法国": {"style": "快速转换", "attack": 9.5, "defense": 7.5},
    "塞内加尔": {"style": "快速转换", "attack": 7.5, "defense": 6.5},
    "伊拉克": {"style": "防守反击", "attack": 5.0, "defense": 5.5},
    "挪威": {"style": "直接进攻", "attack": 8.0, "defense": 5.5},
    "阿根廷": {"style": "控球压迫", "attack": 9.0, "defense": 8.0},
    "阿尔及利亚": {"style": "快速转换", "attack": 6.5, "defense": 5.5},
    "奥地利": {"style": "高位逼抢", "attack": 7.0, "defense": 6.5},
    "约旦": {"style": "防守反击", "attack": 5.0, "defense": 6.0},
    "葡萄牙": {"style": "技术传控", "attack": 8.5, "defense": 7.5},
    "民主刚果": {"style": "身体对抗", "attack": 6.0, "defense": 5.5},
    "乌兹别克斯坦": {"style": "稳守突击", "attack": 5.5, "defense": 5.5},
    "哥伦比亚": {"style": "快速转换", "attack": 7.5, "defense": 6.0},
    "英格兰": {"style": "高位逼抢", "attack": 9.0, "defense": 7.0},
    "克罗地亚": {"style": "技术传控", "attack": 7.0, "defense": 7.0},
    "加纳": {"style": "快速转换", "attack": 6.5, "defense": 5.0},
    "巴拿马": {"style": "防守反击", "attack": 4.5, "defense": 5.0},
}

# 东道主
HOSTS = ["墨西哥", "美国", "加拿大"]

# 卫冕冠军
DEFENDING_CHAMP = "阿根廷"

# 风格克制矩阵
STYLE_COUNTER = {
    ("高位逼抢", "控球压迫"): 0.08,
    ("高位逼抢", "技术传控"): 0.05,
    ("防守反击", "高位逼抢"): 0.08,
    ("防守反击", "快速转换"): 0.05,
    ("控球压迫", "防守反击"): 0.08,
    ("控球压迫", "稳守突击"): 0.05,
    ("身体对抗", "技术传控"): 0.06,
    ("身体对抗", "快速转换"): 0.04,
}

# 洲际归属
CONTINENT = {
    "墨西哥": "NA", "南非": "AF", "韩国": "AS", "捷克": "EU",
    "加拿大": "NA", "波黑": "EU", "卡塔尔": "AS", "瑞士": "EU",
    "巴西": "SA", "摩洛哥": "AF", "海地": "NA", "苏格兰": "EU",
    "美国": "NA", "巴拉圭": "SA", "澳大利亚": "AS", "土耳其": "EU",
    "德国": "EU", "库拉索": "NA", "科特迪瓦": "AF", "厄瓜多尔": "SA",
    "荷兰": "EU", "日本": "AS", "瑞典": "EU", "突尼斯": "AF",
    "比利时": "EU", "埃及": "AF", "伊朗": "AS", "新西兰": "OC",
    "西班牙": "EU", "佛得角": "AF", "沙特阿拉伯": "AS", "乌拉圭": "SA",
    "法国": "EU", "塞内加尔": "AF", "伊拉克": "AS", "挪威": "EU",
    "阿根廷": "SA", "阿尔及利亚": "AF", "奥地利": "EU", "约旦": "AS",
    "葡萄牙": "EU", "民主刚果": "AF", "乌兹别克斯坦": "AS", "哥伦比亚": "SA",
    "英格兰": "EU", "克罗地亚": "EU", "加纳": "AF", "巴拿马": "NA",
}


# ========== 3. Elo 引擎 ==========
class EloEngine:
    K = 40  # 世界杯 K 值（高波动）
    HOME_ADVANTAGE = 65  # 主场 Elo 加成
    HOST_BONUS = 80      # 东道主额外加成

    def __init__(self, initial_ratings=None):
        self.ratings = dict(initial_ratings or INITIAL_ELO)

    def expected_score(self, elo_a, elo_b):
        """Elo 期望得分（0-1）"""
        return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))

    def win_prob(self, team_a, team_b, is_host=False, is_neutral=True):
        """计算胜率（含主场/东道主修正）"""
        elo_a = self.ratings[team_a]
        elo_b = self.ratings[team_b]

        # 主场加成
        if not is_neutral:
            elo_a += self.HOME_ADVANTAGE
        # 东道主加成（小组赛）
        if is_host:
            elo_a += self.HOST_BONUS

        exp_a = self.expected_score(elo_a, elo_b)

        # 三元概率模型：Elo -> 胜/平/负
        # 用经验公式：平局概率与 elo 差成反比
        elo_diff = abs(elo_a - elo_b)
        draw_base = 0.28 - min(elo_diff, 200) * 0.0005
        draw_prob = max(0.15, min(0.30, draw_base))

        if exp_a > 0.5:
            win_prob = exp_a * (1 - draw_prob)
            lose_prob = (1 - exp_a) * (1 - draw_prob)
        else:
            win_prob = exp_a * (1 - draw_prob)
            lose_prob = (1 - exp_a) * (1 - draw_prob)

        # 归一化
        total = win_prob + draw_prob + lose_prob
        return {
            "win": win_prob / total,
            "draw": draw_prob / total,
            "lose": lose_prob / total
        }

    def update(self, team_a, team_b, goals_a, goals_b, is_host=False, is_neutral=True):
        """根据实际比分更新 Elo"""
        elo_a = self.ratings[team_a]
        elo_b = self.ratings[team_b]

        if not is_neutral:
            elo_a += self.HOME_ADVANTAGE
        if is_host:
            elo_a += self.HOST_BONUS

        exp_a = self.expected_score(elo_a, elo_b)

        if goals_a > goals_b:
            actual_a = 1.0
        elif goals_a < goals_b:
            actual_a = 0.0
        else:
            actual_a = 0.5

        self.ratings[team_a] += self.K * (actual_a - exp_a)
        self.ratings[team_b] += self.K * ((1 - actual_a) - (1 - exp_a))


# ========== 4. 蒙特卡洛模拟 ==========
class MonteCarloSimulator:
    """
    基于 Elo 差值构建进球分布，蒙特卡洛模拟比分
    核心思路：
    - Elo 差 -> 期望进球（非线性映射，强队压制弱队时 λ 更高）
    - 风格克制 -> 微调进球期望
    - 蒙特卡洛跑 N 次 -> 统计比分频率
    """

    def __init__(self, elo_engine, style_data=None):
        self.elo = elo_engine
        self.style = style_data or STYLE_DATA
        self.N = 10000  # 模拟次数

    def _elo_to_lambda(self, elo_diff, is_stronger_side=True):
        """Elo 差 -> 期望进球数（非线性映射）"""
        # 基础值：世界杯场均 1.35-1.65 球
        base = 1.35
        # Elo 差每 100 分 -> 进球 +0.15（强队方）/ -0.10（弱队方）
        if is_stronger_side:
            return max(0.4, min(base + abs(elo_diff) * 0.0018, 3.2))
        else:
            return max(0.3, min(base - abs(elo_diff) * 0.0012, 2.8))

    def _style_adjustment(self, team_a, team_b):
        """风格克制修正"""
        sa = self.style.get(team_a, {}).get("style", "")
        sb = self.style.get(team_b, {}).get("style", "")
        adj_a, adj_b = 0.0, 0.0
        for (s1, s2), bonus in STYLE_COUNTER.items():
            if sa == s1 and sb == s2:
                adj_a += bonus
            elif sb == s1 and sa == s2:
                adj_b += bonus
        return adj_a, adj_b

    def _get_attack_defense_factor(self, team):
        """攻防因子（影响进球方差）"""
        s = self.style.get(team, {"attack": 5.5, "defense": 5.5})
        atk_factor = s["attack"] / 5.5  # >1 进攻强
        def_factor = 5.5 / max(s["defense"], 1.0)  # >1 防守弱
        return atk_factor, def_factor

    def simulate_match(self, home, away, is_host=False, round_num=1, is_knockout=False):
        """
        蒙特卡洛模拟一场比赛
        返回: { score_a, score_b, wdl, score_b, score_c, prob_h/d/a, ... }
        """
        # Elo 差
        elo_h = self.elo.ratings[home]
        elo_a = self.elo.ratings[away]
        home_adj = elo_h + (self.elo.HOME_ADVANTAGE if not is_knockout else 0) + (self.elo.HOST_BONUS if is_host and not is_knockout else 0)
        elo_diff = home_adj - elo_a

        # 风格修正
        style_adj_h, style_adj_a = self._style_adjustment(home, away)

        # 攻防因子
        atk_h, def_h = self._get_attack_defense_factor(home)
        atk_a, def_a = self._get_attack_defense_factor(away)

        # 期望进球
        lambda_h = self._elo_to_lambda(elo_diff, is_stronger_side=(elo_diff >= 0))
        lambda_a = self._elo_to_lambda(-elo_diff, is_stronger_side=(elo_diff < 0))

        # 攻防修正：主队进攻强→λ↑；客队防守差→主队λ↑
        lambda_h *= (atk_h * 0.6 + def_a * 0.4)
        lambda_a *= (atk_a * 0.6 + def_h * 0.4)

        # 风格克制修正
        lambda_h *= (1 + style_adj_h)
        lambda_a *= (1 + style_adj_a)

        # 同大洲修正（更熟悉→进球略降、平局略升）
        same_cont = CONTINENT.get(home) == CONTINENT.get(away)
        if same_cont:
            lambda_h *= 0.97
            lambda_a *= 0.97

        # 小组赛第三轮生死战
        if round_num >= 3:
            lambda_h = min(lambda_h * 1.08, 3.5)
            lambda_a = min(lambda_a * 1.08, 3.5)

        # 淘汰赛更保守
        if is_knockout:
            lambda_h *= 0.92
            lambda_a *= 0.92

        # 卫冕冠军小组赛首轮偏慢热
        if home == DEFENDING_CHAMP and round_num == 1:
            lambda_h *= 0.95
        if away == DEFENDING_CHAMP and round_num == 1:
            lambda_a *= 0.95

        lambda_h = max(0.3, min(lambda_h, 3.5))
        lambda_a = max(0.25, min(lambda_a, 3.0))

        # ========== 蒙特卡洛 ==========
        score_counts = {}  # "h-a" -> count
        win_h = draw_c = win_a = 0
        rng = random.Random(hash(f"{home}_{away}") + 42)  # 确定性种子

        for _ in range(self.N):
            # 泊松采样进球数（但用 Elo + 攻防修正后的 λ）
            gh = self._poisson_sample(lambda_h, rng)
            ga = self._poisson_sample(lambda_a, rng)

            # 淘汰赛：平局时加时赛（简化为再模拟一截）
            if is_knockout and gh == ga:
                gh_ext = self._poisson_sample(lambda_h * 0.35, rng)
                ga_ext = self._poisson_sample(lambda_a * 0.35, rng)
                gh_total = gh + gh_ext
                ga_total = ga + ga_ext
                # 点球大战（仍平则随机）
                if gh_total == ga_total:
                    if rng.random() < 0.5:
                        gh_total += 1
                    else:
                        ga_total += 1
                gh, ga = gh_total, ga_total

            key = f"{gh}-{ga}"
            score_counts[key] = score_counts.get(key, 0) + 1

            if gh > ga:
                win_h += 1
            elif gh < ga:
                win_a += 1
            else:
                draw_c += 1

        # 排序比分
        sorted_scores = sorted(score_counts.items(), key=lambda x: -x[1])
        top_scores = [(k, v / self.N) for k, v in sorted_scores[:20]]

        # 概率
        prob_h = win_h / self.N
        prob_d = draw_c / self.N
        prob_a = win_a / self.N

        # 主比分
        score_a_str = top_scores[0][0]
        score_a_prob = top_scores[0][1]

        # scoreB：反向赛果中概率最高的
        ha, aa = map(int, score_a_str.split("-"))
        if ha > aa:
            target = "away"  # 主胜→找客胜
        elif ha < aa:
            target = "home"  # 客胜→找主胜
        else:
            target = "home" if prob_h >= prob_a else "away"  # 平局→概率高的胜方

        score_b_str = None
        for s, p in top_scores:
            sh, sa = map(int, s.split("-"))
            if target == "home" and sh > sa and p >= 0.01:
                score_b_str = s
                break
            elif target == "away" and sa > sh and p >= 0.01:
                score_b_str = s
                break
            elif target == "draw" and sh == sa and p >= 0.01 and s != score_a_str:
                score_b_str = s
                break
        if not score_b_str:
            score_b_str = top_scores[1][0] if len(top_scores) > 1 else "1-0"

        # scoreC：大球备选（总进球更高且概率合理）
        score_c_str = None
        base_total = ha + aa
        for s, p in top_scores:
            sh, sa = map(int, s.split("-"))
            if sh + sa > base_total and p >= 0.015:
                score_c_str = s
                break
        if not score_c_str:
            for s, p in top_scores:
                sh, sa = map(int, s.split("-"))
                if sh + sa >= base_total and p >= 0.02 and s != score_a_str:
                    score_c_str = s
                    break
        if not score_c_str:
            score_c_str = score_b_str

        # 置信度
        if score_a_prob > 0.15:
            confidence = "高"
        elif score_a_prob < 0.08:
            confidence = "低"
        else:
            confidence = "中"

        # 总进球分布
        total_goals_dist = {}
        for s, p in top_scores:
            sh, sa = map(int, s.split("-"))
            t = sh + sa
            total_goals_dist[t] = total_goals_dist.get(t, 0) + p
        sorted_totals = sorted(total_goals_dist.items(), key=lambda x: -x[1])
        top_totals = [f"{t}球" for t, _ in sorted_totals[:3]]
        avg_goals = lambda_h + lambda_a
        goals_label = "大球" if avg_goals > 2.8 else ("小球" if avg_goals < 2.0 else "适中")

        # 赛果标签
        if ha > aa:
            wdl = "主胜"
            wdl_label = f"{home}·胜"
        elif ha < aa:
            wdl = "客胜"
            wdl_label = f"{away}·胜"
        else:
            wdl = "平局"
            wdl_label = "平局"

        # 冷门预警
        cold_warn = ""
        is_cold = False
        cold_factors = []
        elo_gap = abs(elo_diff)
        weaker = away if elo_diff > 0 else home
        if elo_gap > 150 and prob_h > 0.55 and elo_diff > 0 and prob_a > 0.18:
            cold_factors.append(f"{weaker}近期状态佳")
        if same_cont and elo_gap > 100:
            cold_factors.append("同大洲更熟悉")
        if is_host and elo_gap < 100:
            cold_factors.append("东道主加持")
        if len(cold_factors) >= 2:
            cold_warn = "；".join(cold_factors)
            is_cold = True

        # 分析原因
        reasons = []
        if elo_gap > 120:
            stronger = home if elo_diff > 0 else away
            reasons.append(f"【实力】{stronger}全面占优（Elo差{int(elo_gap)}）")
        elif elo_gap > 50:
            stronger = home if elo_diff > 0 else away
            reasons.append(f"【实力】{stronger}占优（Elo差{int(elo_gap)}）")
        else:
            reasons.append(f"【实力】势均力敌（Elo差{int(elo_gap)}）")

        sh = self.style.get(home, {})
        sa_s = self.style.get(away, {})
        reasons.append(f"【攻防】{home}攻{sh.get('attack',5.5):.1f}/守{sh.get('defense',5.5):.1f} vs {away}攻{sa_s.get('attack',5.5):.1f}/守{sa_s.get('defense',5.5):.1f}")
        reasons.append(f"【打法】{sh.get('style','')} vs {sa_s.get('style','')}")
        if style_adj_h > 0:
            reasons.append(f"【克制】{home}打法克制{away}")
        elif style_adj_a > 0:
            reasons.append(f"【克制】{away}打法克制{home}")

        round_label = {1: "首轮", 2: "关键战", 3: "生死战"}.get(round_num, "淘汰赛")
        if is_knockout:
            round_label = "淘汰赛"
        reasons.append(f"【战意】{round_label}")
        if is_host:
            reasons.append(f"【主场】{home}东道主")
        if same_cont:
            reasons.append(f"【同洲】同大洲交锋")

        reasons.append(f"【概率】胜平负 {int(prob_h*100)}%/{int(prob_d*100)}%/{int(prob_a*100)}%")
        reasons.append(f"【预期】λ₁={lambda_h:.2f} λ₂={lambda_a:.2f} | 总进{avg_goals:.1f}球（{goals_label}）")
        reasons.append(f"【比分】①{score_a_str}（{wdl_label}，置信{confidence}）②{score_b_str}（备选）③{score_c_str}（大球）")
        if cold_warn:
            reasons.append(f"⚠️冷门预警：{cold_warn}")

        return {
            "score": score_a_str,
            "scoreB": score_b_str,
            "scoreC": score_c_str,
            "wdl": wdl,
            "wdlLabel": wdl_label,
            "goals": "/".join(top_totals) + f"（{goals_label}）",
            "goalsNum": ha + aa,
            "reason": "；".join(reasons),
            "isUpset": is_cold,
            "coldWarning": cold_warn,
            "confidence": confidence,
            "lambda": {"h": round(lambda_h, 2), "a": round(lambda_a, 2), "total": round(lambda_h + lambda_a, 2)},
            "probH": round(prob_h, 4),
            "probD": round(prob_d, 4),
            "probA": round(prob_a, 4),
            "eloDiff": int(elo_diff),
            "topScores": top_scores[:10],
        }

    @staticmethod
    def _poisson_sample(lam, rng):
        """泊松分布采样"""
        L = math.exp(-lam)
        k = 0
        p = 1.0
        while True:
            k += 1
            p *= rng.random()
            if p < L:
                break
        return k - 1


# ========== 5. 主流程 ==========
def run_predictions(finished_matches=None, output_dir="data"):
    """
    执行全量预测
    finished_matches: [{"id": "A_0", "home": "墨西哥", "away": "南非", "score_h": 2, "score_a": 1}, ...]
    """
    finished_matches = finished_matches or []

    # 初始化 Elo 引擎
    engine = EloEngine()

    # 先用已完赛结果更新 Elo
    for fm in finished_matches:
        engine.update(fm["home"], fm["away"], fm["score_h"], fm["score_a"],
                      is_host=fm.get("is_host", False),
                      is_neutral=fm.get("is_neutral", True))

    # 蒙特卡洛模拟器
    sim = MonteCarloSimulator(engine)

    # 预测所有小组赛
    predictions = {}
    for group_name, teams in GROUPS.items():
        for h_idx, a_idx, m_idx in MATCH_TEMPLATE:
            mid = f"{group_name}_{m_idx}"
            home = teams[h_idx]
            away = teams[a_idx]

            # 如果已完赛，用实际比分
            finished = next((f for f in finished_matches if f["id"] == mid), None)
            if finished:
                predictions[mid] = {
                    "score": f"{finished['score_h']}-{finished['score_a']}",
                    "scoreB": "-",
                    "scoreC": "-",
                    "wdl": "主胜" if finished["score_h"] > finished["score_a"] else ("客胜" if finished["score_h"] < finished["score_a"] else "平局"),
                    "wdlLabel": f"{home}·胜" if finished["score_h"] > finished["score_a"] else (f"{away}·胜" if finished["score_h"] < finished["score_a"] else "平局"),
                    "goals": "",
                    "goalsNum": finished["score_h"] + finished["score_a"],
                    "reason": "已完赛",
                    "isUpset": False,
                    "coldWarning": "",
                    "confidence": "确定",
                    "locked": True,
                    "probH": 0, "probD": 0, "probA": 0,
                    "eloDiff": 0,
                }
            else:
                is_host = home in HOSTS and not (m_idx >= 3)  # 小组赛前2轮有东道主加成
                round_num = m_idx // 2 + 1  # 第1/2/3轮
                result = sim.simulate_match(home, away, is_host=is_host, round_num=round_num)
                result["locked"] = False
                predictions[mid] = result

    # 输出
    output = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "engine": "Elo+MonteCarlo",
        "simulations": sim.N,
        "elo_ratings": {k: round(v, 1) for k, v in engine.ratings.items()},
        "predictions": predictions,
    }

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "predictions.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 预测完成，输出到 {out_path}")
    print(f"   共 {len(predictions)} 场比赛")
    return output


if __name__ == "__main__":
    # 本地测试：可以传入已完赛数据
    run_predictions(output_dir="data")
