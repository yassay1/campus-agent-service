import asyncio
from app.db.session import engine, Base
from app.db import models  # 导入所有模型

async def init_database():
    """初始化数据库表结构"""
    print("🔧 开始初始化数据库...")

    async with engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)

    print("✅ 数据库表创建成功！")

    # 验证表是否创建
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        tables = [row[0] for row in result.fetchall()]
        print(f"\n📊 已创建的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table}")

if __name__ == "__main__":
    asyncio.run(init_database())