# 数据库初始化

依据 [用户系统与成长体系-方案设计文档.md](../../docs/用户系统与成长体系-方案设计文档.md) §4。

## 库名

| 库 | 用途 |
|----|------|
| `ai_alchemy` | 本地开发 |
| `ai_alchemy_test` | pytest 集成测试 |

字符集：`utf8mb4` / `utf8mb4_unicode_ci`

## SQL 文件结构

```
db/sql/
├── 01_create_databases.sql    # 创建 ai_alchemy、ai_alchemy_test
└── tables/                    # 按表拆分，按文件名顺序执行
    ├── README.md
    ├── 02_users.sql
    ├── 03_quiz_records.sql
    ├── 04_wrong_questions.sql
    └── 05_exp_logs.sql
```

| 表 | 文件 | 说明 |
|----|------|------|
| `users` | `tables/02_users.sql` | 用户与成长 |
| `quiz_records` | `tables/03_quiz_records.sql` | 闯关历史 |
| `wrong_questions` | `tables/04_wrong_questions.sql` | 错题本 |
| `exp_logs` | `tables/05_exp_logs.sql` | 经验流水 |

## 一键初始化

1. 复制 `server/.env.example` 为 `server/.env`，填写 `DATABASE_URL`（密码勿提交 Git）
2. 安装依赖：`pip install pymysql python-dotenv`
3. 执行：

```bash
npm run db:init
```

或：

```bash
cd server
python scripts/init_database.py
```

## 手动执行（可选）

```bash
mysql -h 127.0.0.1 -P 3306 -u root -p < db/sql/01_create_databases.sql
mysql -h 127.0.0.1 -P 3306 -u root -p ai_alchemy < db/sql/tables/02_users.sql
mysql -h 127.0.0.1 -P 3306 -u root -p ai_alchemy < db/sql/tables/03_quiz_records.sql
mysql -h 127.0.0.1 -P 3306 -u root -p ai_alchemy < db/sql/tables/04_wrong_questions.sql
mysql -h 127.0.0.1 -P 3306 -u root -p ai_alchemy < db/sql/tables/05_exp_logs.sql
# 测试库 ai_alchemy_test 同样执行 tables/*.sql
```
