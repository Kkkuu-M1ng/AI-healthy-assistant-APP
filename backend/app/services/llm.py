# backend/app/services/llm.py
import json
from openai import OpenAI

API_KEY = "sk-6f0b8c5f36bd4b6fb9551538767cf996" 

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def chat_with_ai(history_messages: list, persona: dict) -> str:
    """
    回归纯净聊天逻辑：
    1. 接收历史记录，保证 AI 记得你之前说过的话。
    2. 注入画像，保证 AI 了解你的身体状况。
    3. 返回纯文本回复。
    """
    
    system_instruction = f"""
    你是一个专业的家庭 AI 医疗助手。请根据用户的健康画像和对话历史，提供亲切、专业的健康咨询。

    【用户当前健康画像】：
    - 基本信息：{persona.get('gender')}, {persona.get('age')}岁, 身高{persona.get('height')}cm, 体重{persona.get('weight')}kg
    - 既往病史：{persona.get('tags_json')}
    - 过敏史：{persona.get('allergies')}
    - 当前用药：{persona.get('meds')}
    
    【工作准则】：
    1. 像医生一样思考，不要急于给出诊断，如果信息不足，请多询问用户的症状细节（如持续时间、疼痛性质等）。
    2. 绝对遵守过敏红线。
    3. 如果发现疑似急症，必须提醒用户立即就医。
    4. 直接输出回复文本，不要输出 JSON 格式，也不要带任何标签。
    """

    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "system", "content": system_instruction}] + history_messages,
            # 💡 注意：这里去掉了 response_format，回归普通文本
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"AI 调用失败: {e}")
        return "抱歉，我现在感觉大脑有点混乱，请稍后再试。"
    
def summarize_session_title(chat_content: str) -> str:
    """
    让 AI 根据聊天内容生成一个 6 字以内的简短标题
    """
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "你是一个助手，请根据用户提供的健康咨询片段，总结一个 9 字以内的简短标题。不要输出多余文字。"},
                {"role": "user", "content": chat_content}
            ],
            max_tokens=10 # 限制长度，节省资源
        )
        title = response.choices[0].message.content.strip()
        # 去掉可能的标点符号
        return title.replace("。", "").replace("！", "").replace('"', "")
    except Exception as e:
        print(f"总结标题失败: {e}")
        return "健康咨询"    