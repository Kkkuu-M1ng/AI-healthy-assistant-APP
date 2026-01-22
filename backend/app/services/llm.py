# backend/app/services/llm.py
import json
import base64
from openai import OpenAI

API_KEY = "sk-6f0b8c5f36bd4b6fb9551538767cf996"

client = OpenAI(
    api_key=API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

EXPERT_PROFILES = {
    "child": {
        "role": "你是一位专业的儿科医生。",
        "focus": """
        【工作准则】：
        1. 核心关注点：儿童体征（精神状态、食欲、体温）、用药剂量安全（需询问体重）、生长发育是否符合年龄段。
        2. 沟通风格：语言必须简洁清晰，避免使用复杂医学术语。
        3. 安全红线：严禁推荐阿司匹林类退烧药；对于抗生素使用持极度谨慎态度。
        """
    },
    "pregnant": {
        "role": "你是一位专业的妇产科医生。",
        "focus": """
        【工作准则】：
        1. 核心关注点：孕周、胎动情况、有无腹痛/见红/破水等产科急症信号。
        2. 安全红线：所有用药和生活建议都必须将“对胎儿无害”作为最高优先级。严禁推荐任何FDA C级及以上的药物。
        3. 沟通风格：必须具备高度的安抚性，同时给出明确的观察指标。
        """
    },
    "elder": {
        "role": "你是一位专业的老年病科（全科）医生。",
        "focus": """
        【工作准则】：
        1. 核心关注点：必须优先考虑用户的既往病史（高血压、糖尿病等）和当前用药清单，警惕药物相互作用。
        2. 沟通风格：解释病情要慢、要通俗，避免信息过载。给出的任务必须简单、易于执行。
        3. 安全红线：对于胸痛、头晕、言语不清等疑似心脑血管急症的描述，必须在第一时间强烈建议拨打120。
        """
    },
    "common": {
        "role": "你是一位专业的全科医生。",
        "focus": """
        【工作准则】：
        1. 核心关注点：对常见病、多发病进行初步诊断和鉴别。如果信息不足，通过追问来收集关键病史。
        2. 沟通风格：保持客观、科学、严谨。
        3. 安全红线：提供所有建议时，必须附带“本建议不替代线下医生面诊”的免责声明。
        """
    }
}

def chat_with_ai_vision(
    history_messages: list, 
    persona: dict, 
    mode: str = "common", # 👈 2. 确保函数能接收 mode 参数
    image_base_64: str = None
) -> dict:
    
    # 3. 动态选择专家人设
    expert = EXPERT_PROFILES.get(mode, EXPERT_PROFILES["common"])
    
    # 4. 构造“专家版”系统指令
    system_instruction = f"""
    【你的身份】：{expert['role']}
    【你的工作重点】：{expert['focus']}

    【用户画像参考】：{persona}

    【任务】：分析用户的文字和图片，结合画像给出回复，并提取新发现的症状标签。

    【输出格式要求】：
    你必须且只能输出一个严格的 JSON 对象，格式如下：
    {{
      "reply": "你的自然语言回复",
      "new_tags": ["本次新发现的症状标签"]
    }}
    """

    # 5. 消息对齐逻辑 (保持不变)
    start_index = 0
    # ... (你原来的 start_index 逻辑) ...
    actual_history = history_messages[start_index:]
    
    # 6. 构造消息体 (保持不变)
    messages = [{"role": "system", "content": system_instruction}]
    model_to_use = "qwen-max" # 默认用最聪明的

    if image_base_64:
        model_to_use = "qwen-vl-plus"
        # ... (你原来的图片拼接逻辑) ...
    else:
        messages.extend(actual_history)

    try:
        # 7. 调用 AI (保持不变)
        response = client.chat.completions.create(
            model=model_to_use, 
            messages=messages,
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content
        return json.loads(raw_content)

    except Exception as e:
        print(f"❌ AI 调用失败: {e}")
        return {"reply": "抱歉，专家大脑暂时离线。", "new_tags": []}


def summarize_session_title(chat_content: str) -> str:
    """
    让 AI 根据聊天内容生成一个 6 字以内的简短标题
    """
    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{
                "role":
                "system",
                "content":
                "你是一个助手，请根据用户提供的健康咨询片段，总结一个 9 字以内的简短标题。不要输出多余文字。"
            }, {
                "role": "user",
                "content": chat_content
            }],
            max_tokens=10  # 限制长度，节省资源
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
    你是智能健康管理助理。请根据用户画像和问诊历史生成健康建议和任务。

    要求：
    1. 建议不超过 2 条，每条标题前必须带上【标签】，并解释原因。
        -你需要额外返回一个 detail_json 字段，用于描述“具体怎么执行”。
            detail_json 结构如下：
            {{
            "actions": [
                {{ "text": "..." }}
            ],
            "tips": ["..."]
            }}
            actions 的生成规则（必须严格遵守）：
            1. 每一条必须是【具体可执行行为】，普通人今天就能照着做
            2. 必须以动词开头（如：走、记录、减少、替换、固定、停止）
            3. 禁止使用以下词语：注意、建议、尽量、保持、避免、可以
            4. 不允许抽象表述，如“改善作息”“控制饮食”“加强锻炼”
            5. 每条尽量包含数量或时间（如 10 分钟、3 次、7 天）
            tips 用于补充说明或安抚，不是行动步骤：
            - 可以包含“如果……可以……”
            - 可以包含风险提醒
            - 不得出现具体执行动作
    2. 任务分为一次性任务和长期任务，每次仅生成两条，一条长期任务一条一次性任务。
        - 每条任务必须包含 title, freq, due, tags
        - title 前必须带上对应的【标签】
        - tags 是一个数组，包含对应的标签，如 ["黄疸"]
    3. 对长期观察指标（如血压、血糖、体重）生成 repeating=True，每天/每周可打卡。
    4. 对一次性检查生成 repeating=False。
    5. 每条任务和建议标题前必须带标签，格式 【标签】任务标题 或 【标签】建议标题。
    ---
    【JSON 输出格式示例 (你必须严格模仿这个结构)】：
    {{
      "reply": "我已根据您的对话为您整理了健康方案，请注意查收。",
      "new_advice": [
        {{
          "title": "控制盐摄入，维持血压稳定",
          "reason": "高盐饮食是高血压的核心风险因素，控制摄入有助于降低心血管压力。",
          "tags": ["饮食", "高血压"],
          "detail_json": {{
            "actions": [
              {{"text": "每日食盐总量不超过5克（约一啤酒瓶盖）。"}},
              {{"text": "减少使用酱油、蚝油、咸菜等高盐调味品。"}},
              {{"text": "尝试使用天然香料（如葱、姜、蒜、柠檬汁）替代盐来调味。"}}
            ],
            "tips": [
              "点外卖时备注“少盐”或“酱汁分装”。",
              "警惕面包、饼干等加工食品中的“隐形盐”。"
            ]
          }}
        }}
      ],
      "new_tasks": [
        {{
          "title": "【高血压】每日早晚测量血压",
          "freq": "每日两次",
          "due": "长期",
          "tags": ["监测", "高血压"],
          "repeating": true
        }},
        {{
          "title": "【高血压】预约社区医院年度体检",
          "freq": "一次性",
          "due": "本月内",
          "tags": ["检查", "高血压"],
          "repeating": false
        }}
      ]
    }}
    ---

    用户画像：{persona}
    """

    try:
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{
                "role": "system",
                "content": system_instruction
            }, {
                "role": "user",
                "content": f"请总结这段对话并开具方案：{str(chat_history)}"
            }],
            response_format={"type": "json_object"})
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"生成方案失败: {e}")
        return {"reply": "未能生成方案", "new_advice": [], "new_tasks": []}
