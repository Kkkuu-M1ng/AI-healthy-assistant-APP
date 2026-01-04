import time
import json

def chat_with_ai(history_messages: list) -> dict:
    """
    模拟 AI 服务：返回 { "reply": "...", "new_advice": [...], "new_tasks": [...] }
    """
    # 1. 模拟网络延迟
    time.sleep(1)
    
    # 2. 获取用户最后一句
    last_msg = history_messages[-1]['content'] if history_messages else ""

    # 3. 构造基础回复
    reply_text = f"【模拟AI】收到描述：{last_msg}。请注意观察体温变化。"

    # 4. 模拟智能提取逻辑
    # 只要用户提到特定关键词，我们就假装 AI 提取出了建议
    generated_advice = []
    generated_tasks = []

    if "烧" in last_msg or "热" in last_msg or "温" in last_msg:
        generated_advice.append({
            "title": "物理降温",
            "reason": "监测到发热症状",
            "tags": ["护理", "紧急"]
        })
        generated_tasks.append({
            "title": "测量体温",
            "freq": "每2小时",
            "due": "今日"
        })
    
    if "痛" in last_msg:
         generated_advice.append({
            "title": "卧床休息",
            "reason": "疼痛需要减少活动",
            "tags": ["生活"]
        })

    # 5. 返回结构化数据
    return {
        "reply": reply_text,
        "new_advice": generated_advice,
        "new_tasks": generated_tasks
    }