-- exp_logs — 经验流水
-- 依据：docs/用户系统与成长体系-方案设计文档.md §4.4
-- 依赖：users

CREATE TABLE IF NOT EXISTS `exp_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id` BIGINT UNSIGNED NOT NULL COMMENT '用户 ID',
  `session_id` VARCHAR(36) NOT NULL COMMENT '闯关会话 ID，防重复结算',
  `amount` INT UNSIGNED NOT NULL COMMENT '本次获得 EXP',
  `reason` VARCHAR(64) NOT NULL COMMENT 'quiz_complete / quiz_success_bonus',
  `exp_before` INT UNSIGNED NOT NULL COMMENT '结算前经验',
  `exp_after` INT UNSIGNED NOT NULL COMMENT '结算后经验',
  `level_before` INT UNSIGNED NOT NULL COMMENT '结算前等级',
  `level_after` INT UNSIGNED NOT NULL COMMENT '结算后等级',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '结算时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_created` (`user_id`, `created_at` DESC),
  CONSTRAINT `fk_exp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='经验流水';
