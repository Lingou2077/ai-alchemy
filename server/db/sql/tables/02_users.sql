-- users — 用户与成长
-- 依据：docs/用户系统与成长体系-方案设计文档.md §4.1
-- 须在目标库内执行（ai_alchemy / ai_alchemy_test）

CREATE TABLE IF NOT EXISTS `users` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `openid` VARCHAR(64) NOT NULL COMMENT '微信 openid',
  `nickname` VARCHAR(64) NOT NULL DEFAULT '炼金学徒' COMMENT '显示昵称',
  `avatar_url` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '头像 URL',
  `exp` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计经验值',
  `level` INT UNSIGNED NOT NULL DEFAULT 1 COMMENT '当前等级',
  `title` VARCHAR(32) NOT NULL DEFAULT '见习炼金师' COMMENT '当前称号',
  `total_quizzes` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计完成闯关次数',
  `created_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT '注册时间',
  `updated_at` DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3) COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_openid` (`openid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户与成长';
