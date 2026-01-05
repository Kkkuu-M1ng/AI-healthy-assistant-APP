def update_persona_risk(current_tags: dict, task_title: str) -> dict:
    """
    风险值进化引擎：根据完成的任务，降低对应标签的风险分
    """
    # 1. 简单的任务分值映射逻辑 (你可以根据需求扩展)
    score_to_deduct = 5 # 默认减5分
    target_tag = None
    
    # 模拟简单的关键词匹配逻辑，判断这个任务是针对哪个标签的
    if "血糖" in task_title:
        target_tag = "糖尿病"
        score_to_deduct = 15
    elif "步行" in task_title or "运动" in task_title or "体温" in task_title:
        target_tag = "肥胖" # 假设运动关联肥胖
        score_to_deduct = 20
    elif "药" in task_title:
        # 如果是通用的吃药，可以所有标签都稍微减一点分
        score_to_deduct = 5

    # 2. 执行减分逻辑
    if target_tag and target_tag in current_tags:
        tag_data = current_tags[target_tag]
        tag_data["score"] -= score_to_deduct
        
        # 3. 检查是否触发 Level 降级 (好转)
        if tag_data["score"] <= 0:
            if tag_data["level"] > 1:
                # 降级：Level 2 -> Level 1
                tag_data["level"] -= 1
                tag_data["score"] = 100 # 开启新一级的风险消除
            else:
                # 已经是 Level 1 且 Score 归零 -> 痊愈！
                # 触发删除逻辑
                del current_tags[target_tag]
                print(f"🎉 恭喜！{target_tag} 已从画像中消除。")
                
    return current_tags