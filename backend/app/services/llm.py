# backend/app/services/llm.py
import json
from openai import OpenAI

API_KEY = "sk-6f0b8c5f36bd4b6fb9551538767cf996" 

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def chat_with_ai(history_messages: list, persona: dict) -> dict:
    """
    真实调用通义千问，并注入健康画像
    """
    
    # 2. 构造最关键的“紧箍咒” (System Prompt)
    system_instruction = f"""
    你是一个极其专业的 AI 医生助手。你的唯一任务是根据用户的健康画像和对话历史，提供医疗建议。

    【用户当前的健康画像】：
    - 基本信息：{persona.get('gender', '未知')}, {persona.get('age', '未知')}岁, 身高{persona.get('height', '-')}cm, 体重{persona.get('weight', '-')}kg
    - 既往病史：{persona.get('tags_json', '无')}
    - 【安全红线】过敏史：{persona.get('allergies', '无')}
    - 【安全红线】当前用药：{persona.get('meds', '无')}
    - 生理状态：{persona.get('special_status', '正常')}

    【工作守则】：
    1. 必须优先考虑过敏史和当前用药。如果建议药物，严禁包含过敏成分，并防止药物冲突。
    2. 如果用户描述出现胸痛、呼吸困难、大出血等症状，必须在回复的第一句建议立即拨打120。
    3. 你的回复必须是【标准JSON格式】，严禁输出任何 Markdown 标记或多余的解释文字。

    【输出格式要求】：
    {{
      "reply": "你对用户说的通俗易懂的安抚和建议话语",
      "new_advice": [
        {{"title": "建议标题", "reason": "为什么给这个建议", "tags": ["分类"]}}
      ],
      "new_tasks": [
        {{"title": "任务标题", "freq": "频率", "due": "建议执行时间"}}
      ]
    }}
    """

    try:
        # 3. 发起真实请求
        response = client.chat.completions.create(
            model="qwen-plus", # 也可以用 qwen-max 逻辑更强
            messages=[
                {"role": "system", "content": system_instruction}
            ] + history_messages,
            # 强制模型返回 JSON 对象 (灵积平台高级功能)
            response_format={ "type": "json_object" } 
        )

        # 4. 解析结果
        ai_raw_content = response.choices[0].message.content
        return json.loads(ai_raw_content)

    except Exception as e:
        print(f"❌ 大模型调用失败: {e}")
        # 兜底回复
        return {
            "reply": "抱歉，我的医学库暂时连接中断，请稍后再试。",
            "new_advice": [],
            "new_tasks": []
        }