-- wrong_questions — 错题本
-- 依据：docs/用户系统与成长体系-方案设计文档.md §4.3
-- 依赖：users

CREATE TABLE IF NOT EXISTS `wrong_questions` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户 ID',
  `question_id` VARCHAR(64) NOT NULL COMMENT '题目 ID',
  `session_id` VARCHAR(36) NOT NULL COMMENT '来源闯关会话',
  `topic` VARCHAR(128) NOT NULL COMMENT '所属主题',
  `stem` TEXT NOT NULL COMMENT '题干',
  `options` JSON NOT NULL COMMENT '选项 [{key, text}]',
  `correct_answer` JSON NOT NULL COMMENT '正确答案 ["A"]',
  `explanation` TEXT NOT NULL COMMENT '讲解',
  `difficulty` VARCHAR(16) NOT NULL COMMENT 'easy/medium/hard',
  `wrong_count` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '累计答错次数',
  `last_wrong_at` DATETIME(3) NOT NULL COMMENT '最近答错时间',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '首次收录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_question` (`user_id`, `question_id`),
  KEY `idx_user_last_wrong` (`user_id`, `last_wrong_at` DESC),
  CONSTRAINT `fk_wrong_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='错题本';
