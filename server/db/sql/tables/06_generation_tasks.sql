-- generation_tasks — 异步 AI 任务（联网检索 / 出题）
-- 依赖：users（user_id 可选，未登录时为 NULL）

CREATE TABLE IF NOT EXISTS `generation_tasks` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `task_id` VARCHAR(36) NOT NULL COMMENT '任务 UUID',
  `task_type` ENUM('research', 'generate') NOT NULL COMMENT '任务类型',
  `user_id` BIGINT UNSIGNED NULL COMMENT '发起用户，可为空',
  `status` ENUM('pending', 'running', 'done', 'failed') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
  `step` ENUM(
    'pending',
    'research',
    'topic_candidates',
    'knowledge',
    'questions',
    'done',
    'failed'
  ) NOT NULL DEFAULT 'pending' COMMENT '当前步骤',
  `progress_message` VARCHAR(128) NULL COMMENT '进度文案',
  `request_payload` JSON NOT NULL COMMENT '请求参数快照',
  `result` JSON NULL COMMENT '完成结果',
  `error_message` TEXT NULL COMMENT '失败原因',
  `session_id` VARCHAR(36) NULL COMMENT '出题完成后关联的 session_id',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
  `expires_at` DATETIME(3) NOT NULL COMMENT '任务过期时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_user_created` (`user_id`, `created_at` DESC),
  KEY `idx_expires_at` (`expires_at`),
  CONSTRAINT `fk_task_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='异步 AI 生成任务';
