# 建表 SQL（按表拆分）

执行顺序由文件名前缀保证，**请勿打乱**：

| 文件 | 表 | 依赖 |
|------|-----|------|
| `02_users.sql` | `users` | — |
| `03_quiz_records.sql` | `quiz_records` | `users` |
| `04_wrong_questions.sql` | `wrong_questions` | `users` |
| `05_exp_logs.sql` | `exp_logs` | `users` |

后续表结构变更：优先修改对应单表文件，再执行 `npm run db:init`（`CREATE IF NOT EXISTS` 可重复执行）；破坏性变更请另写迁移脚本。
