from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import hashlib

app = FastAPI()

# 基础数据
heavenly_stems = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
earthly_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
five_element_map = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土",
    "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
}
hidden_stems_map = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], "卯": ["乙"],
    "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"], "午": ["丁", "己"],
    "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"], "酉": ["辛"],
    "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]
}
sheng_map = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
ke_map = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

class BaziRequest(BaseModel):
    birth: str
    gender: Optional[str] = "unknown"
    location: Optional[str] = None
    longitude: Optional[float] = None

def get_element(char):
    return five_element_map.get(char, None)

def generate_ganzhi():
    result = []
    for i in range(60):
        result.append(heavenly_stems[i % 10] + earthly_branches[i % 12])
    return result

def get_ten_gods(day_master, other_gans):
    dm_elem = get_element(day_master)
    ten_gods_map = {
        "木": {"木": "比肩/劫财", "火": "食神/伤官", "土": "偏财/正财", "金": "七杀/正官", "水": "正印/偏印"},
        "火": {"木": "正印/偏印", "火": "比肩/劫财", "土": "食神/伤官", "金": "偏财/正财", "水": "七杀/正官"},
        "土": {"木": "七杀/正官", "火": "正印/偏印", "土": "比肩/劫财", "金": "食神/伤官", "水": "偏财/正财"},
        "金": {"木": "偏财/正财", "火": "七杀/正官", "土": "正印/偏印", "金": "比肩/劫财", "水": "食神/伤官"},
        "水": {"木": "食神/伤官", "火": "偏财/正财", "土": "七杀/正官", "金": "正印/偏印", "水": "比肩/劫财"}
    }
    result = []
    for gan in other_gans:
        target_elem = get_element(gan)
        if dm_elem and target_elem:
            tg_pair = ten_gods_map[dm_elem].get(target_elem, "未知")
            result.append({"干": gan, "五行": target_elem, "十神": tg_pair})
    return result

def generate_bazi_data(birth_str: str):
    dt_hash = int(hashlib.sha256(birth_str.encode()).hexdigest(), 16)
    ganzhi = generate_ganzhi()
    year_gz = ganzhi[dt_hash % 60]
    month_gz = ganzhi[(dt_hash // 10) % 60]
    day_gz = ganzhi[(dt_hash // 100) % 60]
    hour_gz = ganzhi[(dt_hash // 1000) % 60]

    stems = [year_gz[0], month_gz[0], day_gz[0], hour_gz[0]]
    branches = [year_gz[1], month_gz[1], day_gz[1], hour_gz[1]]
    five_elements = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for x in stems + branches:
        fe = get_element(x)
        if fe:
            five_elements[fe] += 1

    day_master = day_gz[0]
    ten_gods = get_ten_gods(day_master, stems)

    hidden_info = {}
    for b in branches:
        hidden = hidden_stems_map.get(b, [])
        tg_hidden = get_ten_gods(day_master, hidden)
        hidden_info[b] = {"藏干": hidden, "十神": tg_hidden}

    dm_elem = get_element(day_master)
    month_hidden = hidden_stems_map.get(month_gz[1], [])
    month_elements = [get_element(g) for g in month_hidden]
    de_ling = dm_elem in month_elements
    score = 0
    score += 3 if de_ling else 0
    score += five_elements.get(dm_elem, 0)
    score += five_elements.get(sheng_map.get(sheng_map.get(dm_elem)), 0)
    score += five_elements.get(dm_elem, 0)
    score -= five_elements.get(sheng_map.get(dm_elem), 0)
    score -= five_elements.get(ke_map.get(dm_elem), 0)
    status = "身旺" if score >= 6 else "身弱"
    if status == "身旺":
        yongshen = [sheng_map.get(dm_elem), ke_map.get(dm_elem)]
        yongshen_msg = f"你日主为{day_master}（{dm_elem}），命局得分为{score}，属【身旺】格局。建议用神为：{yongshen[0]}（泄），{yongshen[1]}（克）。"
    else:
        beisheng = [k for k, v in sheng_map.items() if v == dm_elem]
        yongshen_msg = f"你日主为{day_master}（{dm_elem}），命局得分为{score}，属【身弱】格局。建议用神为：{beisheng[0]}（印），{dm_elem}（比劫）。"

    return {
        "input_birth": birth_str,
        "four_pillars": {
            "year": year_gz,
            "month": month_gz,
            "day": day_gz,
            "hour": hour_gz
        },
        "day_master": day_master,
        "five_element_count": five_elements,
        "ten_gods": ten_gods,
        "hidden_stems_and_gods": hidden_info,
        "strength_judgment": {
            "日主": day_master,
            "五行": dm_elem,
            "得令": de_ling,
            "命局评分": score,
            "身强弱": status,
            "推荐用神": yongshen_msg
        }
    }

@app.post("/bazi")
def get_bazi(data: BaziRequest):
    return generate_bazi_data(data.birth)
