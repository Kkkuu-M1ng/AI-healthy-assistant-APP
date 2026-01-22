# backend/app/tests/test_safe_zone_downgrade.py

from copy import deepcopy
from app.routers.tasks import complete_task  # 直接导入你的后端打卡函数

# 模拟一个任务对象，替代数据库
TASK_TEMPLATE = {
    "id": 28,
    "member_id": 1,
    "title": "【黄疸】确保每日足量哺乳",
    "freq": "长期",
    "score": 100,            # 初始分数
    "current_level": 3,      # 初始风险等级
    "streak": 0,             # 安全区连续天数
    "safe_days_needed": 3,   # 达到降级所需天数
    "safe_levels": [
        {"level": 0, "min_score": 0, "max_score": 14},
        {"level": 1, "min_score": 15, "max_score": 39},
        {"level": 2, "min_score": 40, "max_score": 69},
        {"level": 3, "min_score": 70, "max_score": 100},
    ],
    "repeating": True
}

def simulate_daily_checkins(task_template, days=10):
    """
    模拟连续打卡多天，打印安全区降级逻辑状态
    """
    task = deepcopy(task_template)  # 每次使用新对象
    print(f"\n=== 模拟连续打卡 {days} 天 ===\n")

    for day in range(1, days + 1):
        print(f"=== 第 {day} 天打卡 ===")
        try:
            # 直接调用后端逻辑
            result = complete_task(task)
        except Exception as e:
            print("打卡出错:", e)
            result = None

        if result:
            # 打印当天结果
            print(f"score: {result.get('score')}")
            print(f"current_level: {result.get('current_level')}")
            print(f"streak: {result.get('streak')}")
            print(f"delta: {result.get('delta')}")
        else:
            print("score: None")
            print("current_level: None")
            print("streak: None")
            print("delta: None")

        print("")  # 空行分隔每天结果

if __name__ == "__main__":
    simulate_daily_checkins(TASK_TEMPLATE, days=10)
