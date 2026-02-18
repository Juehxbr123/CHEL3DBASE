<?php
session_start();

$dsn = sprintf(
  'mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
  getenv('MYSQL_HOST') ?: 'mysql',
  getenv('MYSQL_PORT') ?: '3306',
  getenv('MYSQL_DB') ?: 'chel3d_db'
);

$pdo = new PDO(
  $dsn,
  getenv('MYSQL_USER') ?: 'chel3d_user',
  getenv('MYSQL_PASSWORD') ?: '',
  [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
  ]
);

$adminUser = getenv('ADMIN_USER') ?: 'admin';
$adminPassword = getenv('ADMIN_PASSWORD') ?: 'admin123';
$statuses = ['Черновик', 'Новая заявка', 'В работе', 'Готово', 'Отменено'];

if (isset($_GET['logout'])) {
  session_destroy();
  header('Location: /');
  exit;
}

if (!isset($_SESSION['ok'])) {
  if (
    $_SERVER['REQUEST_METHOD'] === 'POST'
    && ($_POST['login'] ?? '') === $adminUser
    && ($_POST['password'] ?? '') === $adminPassword
  ) {
    $_SESSION['ok'] = true;
    header('Location: /');
    exit;
  }

  echo '<form method="post" style="max-width:320px;margin:60px auto;font-family:Arial">
    <h2>Вход в админку Chel3D</h2>
    <input name="login" placeholder="Логин" style="width:100%;margin-bottom:8px">
    <input type="password" name="password" placeholder="Пароль" style="width:100%;margin-bottom:8px">
    <button>Войти</button>
  </form>';
  exit;
}

if (isset($_POST['set_status'])) {
  $id = (int)($_POST['order_id'] ?? 0);
  $status = $_POST['status'] ?? '';

  if ($id > 0 && in_array($status, $statuses, true)) {
    $stmt = $pdo->prepare('UPDATE orders SET status=:s WHERE id=:id');
    $stmt->execute([':s' => $status, ':id' => $id]);
  }
}

function h($v) {
  return htmlspecialchars((string)$v, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}

$tab = $_GET['tab'] ?? 'заявки';
$orderId = (int)($_GET['order_id'] ?? 0);

echo '<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Chel3D админка</title>
<style>
  body{font-family:Arial;margin:20px}
  a{margin-right:12px}
  table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #ddd;padding:8px;vertical-align:top}
</style>
</head><body>';

echo '<h1>Chel3D админка</h1><p>Пользователь: ' . h($adminUser) . ' | <a href="?logout=1">Выйти</a></p>';
echo '<nav><a href="?tab=сводка">Сводка</a><a href="?tab=заявки">Заявки</a></nav><hr>';

if ($tab === 'сводка') {
  echo '<h2>Сводка</h2>';

  foreach ($statuses as $st) {
    $stmt = $pdo->prepare('SELECT COUNT(*) cnt FROM orders WHERE status=:s');
    $stmt->execute([':s' => $st]);
    $row = $stmt->fetch();

    echo '<p><b>' . h($st) . '</b>: ' . (int)($row['cnt'] ?? 0) . '</p>';
  }
}

if ($tab === 'заявки') {
  if ($orderId > 0) {
    $st = $pdo->prepare('SELECT * FROM orders WHERE id=:id');
    $st->execute([':id' => $orderId]);
    $o = $st->fetch();

    if (!$o) {
      echo '<p>Заявка не найдена</p>';
    } else {
      echo '<h2>Заявка #' . h($o['id']) . '</h2>';

      echo '<form method="post">
        <input type="hidden" name="order_id" value="' . h($o['id']) . '">
        <select name="status">';

      foreach ($statuses as $s) {
        echo '<option ' . ($s === $o['status'] ? 'selected' : '') . ' value="' . h($s) . '">' . h($s) . '</option>';
      }

      echo '</select>
        <button name="set_status" value="1">Сменить статус</button>
      </form>';

      echo '<p><b>Тип заявки:</b> ' . h($o['request_type']) . '</p>';
      echo '<p><b>Кратко:</b> ' . nl2br(h($o['summary'])) . '</p>';

      $payload = json_decode((string)$o['order_payload'], true) ?: [];

      echo '<h3>Параметры</h3><ul>';
      foreach ($payload as $k => $v) {
        $vv = is_array($v) ? json_encode($v, JSON_UNESCAPED_UNICODE) : (string)$v;
        echo '<li><b>' . h($k) . ':</b> ' . h($vv) . '</li>';
      }
      echo '</ul>';

      echo '<p><a href="?tab=заявки">← Назад</a></p>';
    }
  } else {
    $orders = $pdo->query('SELECT * FROM orders ORDER BY created_at DESC LIMIT 500')->fetchAll();

    echo '<h2>Заявки</h2>
      <table>
        <tr>
          <th>№</th>
          <th>Клиент</th>
          <th>Тип</th>
          <th>Кратко</th>
          <th>Статус</th>
          <th>Создана</th>
          <th></th>
        </tr>';

    foreach ($orders as $o) {
      echo '<tr>
        <td>' . h($o['id']) . '</td>
        <td>' . h($o['full_name']) . ' @' . h($o['username']) . '</td>
        <td>' . h($o['request_type']) . '</td>
        <td>' . h($o['summary']) . '</td>
        <td>' . h($o['status']) . '</td>
        <td>' . h($o['created_at']) . '</td>
        <td><a href="?tab=заявки&order_id=' . (int)$o['id'] . '">Открыть</a></td>
      </tr>';
    }

    echo '</table>';
  }
}

echo '</body></html>';
