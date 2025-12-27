# 连接数据库 + 创建表 + 提供会话 session

from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "app.db"  # 会生成在 backend/ 下
engine = create_engine(f"sqlite:///{sqlite_file_name}", echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
