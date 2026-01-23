# backend/app/services/risk_engine.py
from typing import Dict, Tuple
from datetime import datetime, timedelta

# ----- 配置 -----
BASE_DECREASE = 4
STREAK_BONUS = 2
MAX_STREAK_BONUS = 10
MAX_SCORE = 100
REBOUND_PER_DAY = 2  # 每天未打卡增加多少score


def apply_task_checkin(tags: Dict, task_title: str) -> Tuple[Dict, Dict]:
    """
    原有打卡减少逻辑 + 计算 delta
    返回:
      new_tags: 更新后的标签字典
      delta_dict: {tag_name: {"old_score": x, "new_score": y, "rebound_score": z}}
    """
    if not tags or not task_title:
        return tags, {}

    new_tags = tags.copy()
    delta_dict = {}

    for tag_name, tag_data in new_tags.items():
        if f"【{tag_name}】" not in task_title:
            continue

        old_score = tag_data.get("score", 0)

        # streak 奖励
        streak = tag_data.get("streak", 0)
        bonus = min(streak * STREAK_BONUS, MAX_STREAK_BONUS)
        total_decrease = BASE_DECREASE + bonus
        tag_data["streak"] = streak + 1

        new_score = max(0, old_score - total_decrease)
        tag_data["score"] = new_score

        # 更新最后打卡日期
        tag_data["last_checkin"] = datetime.utcnow().strftime("%Y-%m-%d")

        # 记录 delta，用于前端展示
        delta_dict[tag_name] = {
            "old_score": old_score,
            "new_score": new_score,
            "rebound_score": old_score  # 可根据需要调整
        }

    return new_tags, delta_dict


def rebound_tags(tags: Dict) -> Dict:
    """长期未打卡自动回弹 score"""
    new_tags = tags.copy()
    today = datetime.utcnow().date()

    for tag_name, tag_data in new_tags.items():
        last_checkin_str = tag_data.get("last_checkin")
        if not last_checkin_str:
            days_missed = 1  # 没打卡过
        else:
            last_checkin_date = datetime.strptime(last_checkin_str, "%Y-%m-%d").date()
            days_missed = (today - last_checkin_date).days
            if days_missed <= 0:
                continue  # 今天已打卡，不回弹

        rebound_value = REBOUND_PER_DAY * days_missed
        old_score = tag_data.get("score", 0)
        tag_data["score"] = min(old_score + rebound_value, MAX_SCORE)

    return new_tags


def checkin_with_rebound(tags_json: Dict, task_title: str) -> Dict:
    """
    回弹+打卡整合逻辑 (修正版)
    """
    # 1. 先回弹
    tags_after_rebound = rebound_tags(tags_json)

    # 2. 再打卡，注意这里要解包，拿到更新后的标签和分数变化
    updated_tags, delta_from_checkin = apply_task_checkin(tags_after_rebound, task_title)

    # 3. 构造最终的 delta (用于前端展示)
    # 我们只对那些真正发生了分数变化的标签感兴趣
    final_delta = {}
    for tag_name, delta_data in delta_from_checkin.items():
        rebound_score = tags_after_rebound.get(tag_name, {}).get("score", 100)
        
        # 💡 把新数据都装进去
        final_delta[tag_name] = {
            "old_score": delta_data["old_score"],
            "rebound_score": rebound_score,
            "new_score": delta_data["new_score"],
            "streak": updated_tags.get(tag_name, {}).get("streak", 0)
        }

    return {
        "tags": updated_tags,
        "delta": final_delta
    }

from datetime import datetime, timedelta
from typing import Dict, List

# ----- 自动降级逻辑 ----- #
def update_level_with_streak(tag_data: Dict, safe_levels: List[Dict]):
    """
    更新单个标签的等级，根据连续低分天数自动降级
    tag_data 示例结构:
    {
        "score": 35,
        "level": 2,
        "days_below_threshold": 3,  # 连续低分天数计数
        ...
    }
    safe_levels: [
        {"level": 0, "min_score": 0, "max_score": 14},
        {"level": 1, "min_score": 15, "max_score": 39},
        {"level": 2, "min_score": 40, "max_score": 69},
        {"level": 3, "min_score": 70, "max_score": 100}
    ]
    """
    current_score = tag_data.get("score", 100)
    current_level = tag_data.get("level", 0)

    # 当前等级对应的安全分数下限
    safe_level_info = next((lvl for lvl in safe_levels if lvl["level"] == current_level), None)
    if not safe_level_info:
        return

    threshold = safe_level_info["min_score"]  # 低于这个分数开始倒计时
    days_below = tag_data.get("days_below_threshold", 0)

    # 如果低于安全分数，增加计数
    if current_score < threshold:
        days_below += 1
    else:
        # 高于阈值，倒计时重置
        days_below = 0

    # 连续 X 天低于安全区，则降一级（最小等级为 0）
    REQUIRED_DAYS = 7
    if days_below >= REQUIRED_DAYS and current_level > 0:
        tag_data["level"] = current_level - 1
        days_below = 0  # 降级后重置计数

    tag_data["days_below_threshold"] = days_below


def auto_downgrade_tags(tags: Dict, safe_levels: List[Dict]) -> Dict:
    """遍历所有标签，执行自动降级"""
    new_tags = tags.copy()
    for tag_name, tag_data in new_tags.items():
        update_level_with_streak(tag_data, safe_levels)
    return new_tags

def daily_tag_update(tags_json: Dict, safe_levels: List[Dict], task_title: str = None) -> Dict:
    """
    每天调用或打开 APP 时更新标签：
    1️⃣ 先回弹未打卡的标签
    2️⃣ 如果当天有打卡任务，执行打卡逻辑
    3️⃣ 自动降级
    """
    # 1️⃣ 回弹
    tags_after_rebound = rebound_tags(tags_json)

    # 2️⃣ 打卡（如果有任务标题）
    if task_title:
        tags_after_checkin, delta = apply_task_checkin(tags_after_rebound, task_title)
    else:
        tags_after_checkin, delta = tags_after_rebound, {}

    # 3️⃣ 自动降级
    final_tags = auto_downgrade_tags(tags_after_checkin, safe_levels)

    return {
        "tags": final_tags,
        "delta": delta  # delta 只有打卡才会变化
    }
