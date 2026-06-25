"""
从 ESPN API 拉取已完赛比分，更新 Elo，生成预测 JSON
用于 GitHub Actions 定时执行
"""
import json
import urllib.request
import urllib.parse
import os
import sys

# ESPN Scoreboard API
ESPN_URL = "https://site.web.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# 日期范围：世界杯期间
WC_START = "20260611"
WC_END = "20260719"

# 球队名映射：ESPN -> 中文
ESPN_NAME_MAP = {
    "Mexico": "墨西哥", "South Africa": "南非", "South Korea": "韩国",
    "Czech Republic": "捷克", "Canada": "加拿大", "Bosnia and Herzegovina": "波黑",
    "Qatar": "卡塔尔", "Switzerland": "瑞士", "Brazil": "巴西",
    "Morocco": "摩洛哥", "Haiti": "海地", "Scotland": "苏格兰",
    "United States": "美国", "Paraguay": "巴拉圭", "Australia": "澳大利亚",
    "Turkey": "土耳其", "Germany": "德国", "Curacao": "库拉索",
    "Ivory Coast": "科特迪瓦", "Ecuador": "厄瓜多尔",
    "Netherlands": "荷兰", "Japan": "日本", "Sweden": "瑞典",
    "Tunisia": "突尼斯", "Belgium": "比利时", "Egypt": "埃及",
    "Iran": "伊朗", "New Zealand": "新西兰", "Spain": "西班牙",
    "Cape Verde Islands": "佛得角", "Saudi Arabia": "沙特阿拉伯",
    "Uruguay": "乌拉圭", "France": "法国", "Senegal": "塞内加尔",
    "Iraq": "伊拉克", "Norway": "挪威", "Argentina": "阿根廷",
    "Algeria": "阿尔及利亚", "Austria": "奥地利", "Jordan": "约旦",
    "Portugal": "葡萄牙", "DR Congo": "民主刚果", "Uzbekistan": "乌兹别克斯坦",
    "Colombia": "哥伦比亚", "England": "英格兰", "Croatia": "克罗地亚",
    "Ghana": "加纳", "Panama": "巴拿马",
    # 别名
    "Korea Republic": "韩国", "Korea DPR": "韩国",
    "Cote d'Ivoire": "科特迪瓦", "Côte d'Ivoire": "科特迪瓦",
    "Bosnia-Herzegovina": "波黑", "Bosnia": "波黑",
    "Cape Verde": "佛得角", "Cabo Verde": "佛得角",
    "USA": "美国", "US": "美国",
    "IR Iran": "伊朗", "Iran PR": "伊朗",
}


def fetch_espn_scores():
    """从 ESPN 拉取已完赛比分"""
    finished = []
    dates_to_check = []

    # 生成日期列表（从开赛到今天）
    from datetime import datetime, timedelta
    start = datetime.strptime(WC_START, "%Y%m%d")
    end = datetime.strptime(WC_END, "%Y%m%d")
    today = datetime.utcnow()
    actual_end = min(end, today + timedelta(days=1))

    current = start
    while current <= actual_end:
        dates_to_check.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    for date_str in dates_to_check:
        url = f"{ESPN_URL}?dates={date_str}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WorldCupPredictor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for event in data.get("events", []):
                status = event.get("status", {}).get("type", {}).get("name", "")
                if status != "STATUS_FULL" and status != "STATUS_FINAL":
                    continue

                competitions = event.get("competitions", [])
                if len(competitions) < 1:
                    continue

                comp = competitions[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue

                home_team = None
                away_team = None
                home_score = None
                away_score = None

                for c in competitors:
                    name_en = c.get("team", {}).get("displayName", "")
                    name_cn = ESPN_NAME_MAP.get(name_en, name_en)
                    score = c.get("score")
                    if c.get("homeAway") == "home":
                        home_team = name_cn
                        home_score = int(score) if score else None
                    else:
                        away_team = name_cn
                        away_score = int(score) if score else None

                if home_team and away_team and home_score is not None and away_score is not None:
                    finished.append({
                        "id": event.get("id", ""),
                        "home": home_team,
                        "away": away_team,
                        "score_h": home_score,
                        "score_a": away_score,
                        "is_host": home_team in ["墨西哥", "美国", "加拿大"],
                        "is_neutral": True,
                    })

        except Exception as e:
            print(f"[WARN] ESPN fetch failed for {date_str}: {e}", file=sys.stderr)
            continue

    return finished


def fetch_espn_all():
    """从 ESPN 拉取所有比赛数据（包括未开始、进行中、已完赛）"""
    all_events = []
    dates_to_check = []

    # 生成日期列表（从开赛到结束+3天）
    from datetime import datetime, timedelta
    start = datetime.strptime(WC_START, "%Y%m%d")
    end = datetime.strptime(WC_END, "%Y%m%d")
    today = datetime.utcnow()
    actual_end = min(end, today + timedelta(days=3))  # 多查3天，覆盖未来比赛

    current = start
    while current <= actual_end:
        dates_to_check.append(current.strftime("%Y%m%d"))
        current += timedelta(days=1)

    for date_str in dates_to_check:
        url = f"{ESPN_URL}?dates={date_str}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WorldCupPredictor/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for event in data.get("events", []):
                event_id = event.get("id", "")
                status = event.get("status", {}).get("type", {}).get("name", "")

                competitions = event.get("competitions", [])
                if len(competitions) < 1:
                    continue

                comp = competitions[0]
                competitors = comp.get("competitors", [])
                if len(competitors) < 2:
                    continue

                home_team = None
                away_team = None
                home_score = None
                away_score = None

                for c in competitors:
                    name_en = c.get("team", {}).get("displayName", "")
                    name_cn = ESPN_NAME_MAP.get(name_en, name_en)
                    score = c.get("score")
                    if c.get("homeAway") == "home":
                        home_team = name_cn
                        home_score = int(score) if score else None
                    else:
                        away_team = name_cn
                        away_score = int(score) if score else None

                if home_team and away_team:
                    all_events.append({
                        "id": event_id,
                        "home": home_team,
                        "away": away_team,
                        "score_h": home_score,
                        "score_a": away_score,
                        "status": status,
                        "is_host": home_team in ["墨西哥", "美国", "加拿大"],
                        "is_neutral": True,
                    })

        except Exception as e:
            print(f"[WARN] ESPN fetch failed for {date_str}: {e}", file=sys.stderr)
            continue

    return all_events


def match_to_group_id(home, away):
    """根据主客队名推算小组赛ID (A_0 ~ L_5)"""
    from elo_montecarlo import GROUPS, MATCH_TEMPLATE

    for g, teams in GROUPS.items():
        for h_idx, a_idx, m_idx in MATCH_TEMPLATE:
            if teams[h_idx] == home and teams[a_idx] == away:
                return f"{g}_{m_idx}"
    return None


def save_matches_json(events, data_dir):
    """保存ESPN数据到matches.json，供前端读取"""
    output = {
        "generatedAt": datetime.utcnow().isoformat() + "Z",
        "events": events
    }
    path = os.path.join(data_dir, "matches.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"       Saved matches.json ({len(events)} events)")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)  # worldcup-26/
    data_dir = os.path.join(project_dir, "data")

    # 0. 拉取 ESPN 所有比赛数据（包括未开始、进行中、已完赛）
    print("[0/4] Fetching ESPN all matches...")
    all_events = fetch_espn_all()
    print(f"       Found {len(all_events)} total events")

    # 保存 matches.json 供前端读取
    save_matches_json(all_events, data_dir)

    # 1. 筛选已完赛数据
    print("[1/4] Filtering finished matches...")
    finished_raw = [e for e in all_events if e.get("status") == "STATUS_FINAL"]
    print(f"       Found {len(finished_raw)} finished matches")

    # 映射到 group match ID
    finished_matches = []
    for fm in finished_raw:
        mid = match_to_group_id(fm["home"], fm["away"])
        if mid:
            fm["id"] = mid
            finished_matches.append(fm)

    print(f"       Mapped {len(finished_matches)} to group matches")

    # 2. 加载之前的数据（如果有）
    prev_path = os.path.join(data_dir, "predictions.json")
    prev_finished = []
    if os.path.exists(prev_path):
        with open(prev_path, "r", encoding="utf-8") as f:
            prev_data = json.load(f)
        for mid, pred in prev_data.get("predictions", {}).items():
            if pred.get("locked") and mid != "generatedAt":
                prev_finished.append({
                    "id": mid,
                    "home": "", "away": "",  # 不需要，Elo 已更新
                    "score_h": int(pred["score"].split("-")[0]),
                    "score_a": int(pred["score"].split("-")[1]),
                    "is_host": False,
                    "is_neutral": True,
                })

    # 合并（去重，以 ESPN 数据为准）
    seen = set()
    all_finished = []
    for fm in finished_matches:
        if fm["id"] not in seen:
            all_finished.append(fm)
            seen.add(fm["id"])
    for fm in prev_finished:
        if fm["id"] not in seen:
            all_finished.append(fm)
            seen.add(fm["id"])

    # 3. 运行预测
    print(f"[2/4] Running Elo+MonteCarlo predictions with {len(all_finished)} finished matches...")
    sys.path.insert(0, script_dir)
    from elo_montecarlo import run_predictions
    result = run_predictions(finished_matches=all_finished, output_dir=data_dir)

    print(f"[3/4] Done. {len(result['predictions'])} predictions generated.")

    # 4. 再次保存 matches.json（确保最新）
    print("[4/4] Updating matches.json...")
    all_events = fetch_espn_all()
    save_matches_json(all_events, data_dir)


if __name__ == "__main__":
    main()
