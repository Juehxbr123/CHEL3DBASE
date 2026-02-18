CREATE TABLE IF NOT EXISTS orders (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id BIGINT NOT NULL,
  username VARCHAR(255) NULL,
  full_name VARCHAR(255) NULL,
  branch VARCHAR(64) NOT NULL,
  request_type VARCHAR(128) NULL,
  status ENUM('Черновик','Новая заявка','В работе','Готово','Отменено') NOT NULL DEFAULT 'Черновик',
  summary TEXT NULL,
  order_payload JSON NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_orders_user_status (user_id, status),
  KEY idx_orders_status_created (status, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS order_files (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  order_id BIGINT UNSIGNED NOT NULL,
  telegram_file_id VARCHAR(255) NOT NULL,
  original_name VARCHAR(255) NOT NULL,
  mime_type VARCHAR(255) NULL,
  file_size BIGINT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_order_files_order (order_id),
  CONSTRAINT fk_order_files_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS bot_config (
  config_key VARCHAR(191) NOT NULL,
  config_value TEXT NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO bot_config (config_key, config_value)
VALUES
('welcome_menu_msg', 'Добро пожаловать в Chel3D 👋\nВыберите нужный раздел:'),
('about_text', 'Chel3D — 3D-печать, 3D-сканирование и разработка моделей под задачу клиента.'),
('contacts_text', 'Свяжитесь с нами: @chel3d_support')
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value);
