import json
import sqlite3
import os

def run_import():
    # 1. 确认文件路径
    json_file = 'wiki_data.json'
    db_file = 'app.db' # 👈 如果你的数据库叫 app.db 请对齐

    if not os.path.exists(json_file):
        print("❌ 错误：找不到 wiki_data.json 文件")
        return

    # 2. 读取数据
    with open(json_file, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    # 3. 连接数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 4. 清理旧数据（防止重复导入）
    cursor.execute("DELETE FROM wikiarticle")
    
    print(f"🚀 开始导入 {len(articles)} 篇权威文献...")

    # 5. 循环插入
    for art in articles:
        # 💡 确保将列表转为 JSON 字符串
        tags_str = json.dumps(art['tags_json'], ensure_ascii=False)
        
        cursor.execute("""
            INSERT INTO wikiarticle (
                title, category, source, summary, tags_json, content, 
                cover_url,  -- 👈 1. 加上这一列
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now')) -- 👈 2. 多加一个问号
        """, (
            art['title'],
            art['category'],
            art['source'],
            art['summary'],
            tags_str,
            art['content'],
            "" # 👈 3. 传一个空字符串作为封面图占位，解决 NOT NULL 报错
        ))


    conn.commit()
    conn.close()
    print("✅ 批量导入圆满成功！")

if __name__ == "__main__":
    run_import()