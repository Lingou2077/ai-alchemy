-- quiz_records — 闯关历史
-- 依据：docs/用户系统与成长体系-方案设计文档.md §4.2
-- 依赖：users

CREATE TABLE IF NOT EXISTS `quiz_records` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户 ID',
  `session_id` VARCHAR(36) NOT NULL COMMENT '闯关会话 ID，幂等键',
  `topic` VARCHAR(128) NOT NULL COMMENT '学习主题',
  `accuracy` DECIMAL(5, 2) NOT NULL COMMENT '正确率 0.00-100.00',
  `question_count` INT UNSIGNED NOT NULL COMMENT '题目数量',
  `duration_sec` INT UNSIGNED NOT NULL COMMENT '用时（秒）',
  `status` ENUM('completed', 'failed') NOT NULL COMMENT 'completed=炼成; failed=灵韵散尽',
  `summary` TEXT NULL COMMENT 'AI 知识总结',
  `suggestion` TEXT NULL COMMENT 'AI 学习建议',
  `weak_points` JSON NULL COMMENT '薄弱点 [{name, reason}]',
  `finished_at` DATETIME(3) NOT NULL COMMENT '闯关完成时间',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '记录写入时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_finished` (`user_id`, `finished_at` DESC),
  CONSTRAINT `fk_quiz_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='闯关历史';
