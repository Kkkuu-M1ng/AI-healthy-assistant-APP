# backend/app/services/llm.py
import json
import base64
from openai import OpenAI

API_KEY = "sk-6f0b8c5f36bd4b6fb9551538767cf996" 

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def chat_with_ai_vision(history_messages: list, persona: dict, image_base64: str = None) -> dict:
    """
    多模态问诊核心：
    - 如果有图，调动视觉能力识别病症
    - 将病症转化为结构化标签返回
    """
    
    # 1. 构造具有“识图提取”能力的系统指令
    system_instruction = f"""
    你是一个专业的家庭医生助手，具备强大的视觉分析能力。
    【当前用户画像】：{persona}
    
    【你的任务】：
    1. 分析用户的文字描述和上传的图片（如化验单、患处照片）。
    2. 结合画像（如过敏史、病史）给出专业的建议。
    3. 如果从对话或图片中发现了用户此前未记录的【新症状或疾病】（例如：皮疹、发烧、结膜炎、外伤等），请将其提取出来。
    
    【核心原则】：
    1. 即使你建议用户就医，你也【必须】同时给出 2-3 条日常护理或生活方式的建议。
    2. 禁止仅仅重复“请就医”，那对用户没有帮助。

    【输出要求】：
    你必须且只能输出标准的 JSON 格式，包含以下字段：
    - reply: 你的自然语言回复（亲切、专业、简短）。
    - new_tags: 一个字符串数组，列出本次发现的新病症标签（如果没有发现，返回空数组 []）。
    """

    start_index = 0
    for i, msg in enumerate(history_messages):
        if msg["role"] == "user":
            start_index = i
            break
    
    # 截取从第一个用户提问开始的所有记录
    actual_history = history_messages[start_index:]

    # 2. 构造消息体
    # 如果有图片，我们需要把最后一轮消息转化为多模态格式
    messages = [{"role": "system", "content": system_instruction}]
    
    if image_base64:
        # 处理图片逻辑（保持不变）
        messages.extend(actual_history[:-1])
        last_msg_content = actual_history[-1]["content"]
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": last_msg_content},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ]
        })
    else:
        # 普通文字
        messages.extend(actual_history)

    try:
        # 3. 增加具体报错打印，方便我们以后看真相
        response = client.chat.completions.create(
            model="qwen-vl-plus", 
            messages=messages,
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        # 👇 这一行非常重要，以后崩了看这里
        print(f"❌ 通义千问调用真报错信息: {str(e)}") 
        return {"reply": "抱歉，我的大脑连接有点闪断，请再试一次。", "new_tags": []}
    
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
    
def generate_health_plan(chat_history: list, persona: dict) -> dict:
    """
    专门用于在问诊结束时，总结全案并生成结构化数据
    """
    system_instruction = f"""
    你是一个全科医生。请复盘以下这段医疗咨询对话，并结合用户的健康画像，给出最终的总结建议和待办任务。

    【重要：放宽门槛】：
    即使信息不完整，也不要拒答。你可以给出“通用性”的健康建议（如饮食调整、作息提醒、情绪安抚等）。
    
    【用户画像】：{persona}
    
    【输出要求】：
    1. 必须输出 JSON 格式。
    2. 建议（new_advice）应包含原理说明。
    3. 任务（new_tasks）必须具体可执行（如：每日3次，饭后30分钟）。
    4. 如果对话内容不足以给出建议，请在 reply 中说明，并让 new_advice 和 new_tasks 为空。

    你必须严格遵守以下键名，禁止自定义：
    - new_advice 数组内必须包含: "title", "reason", "tags"
    - new_tasks 数组内必须包含: "title", "freq", "due"
    """
    
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"请总结这段对话并开具方案：{str(chat_history)}"}
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"生成方案失败: {e}")
        return {"reply": "未能生成方案", "new_advice": [], "new_tasks": []}    