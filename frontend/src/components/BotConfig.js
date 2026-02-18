import React, { useEffect, useState } from 'react';
import { Button, Card, Input, Space, message } from 'antd';
import axios from 'axios';



const BotConfig = () => {
  const [cfg, setCfg] = useState({ welcome_menu_msg: '', about_text: '' });
  useEffect(() => { axios.get('/api/bot-config/').then((r) => setCfg((p) => ({ ...p, ...r.data }))); }, []);

  const save = async (key) => {
    await axios.put('/api/bot-config/', { key, value: cfg[key] });
    message.success('Сохранено');
  };

  return (
    <Space direction="vertical" style={{ width: '100%' }}>
      <Card title="Приветствие">
        <Input.TextArea rows={4} value={cfg.welcome_menu_msg} onChange={(e) => setCfg({ ...cfg, welcome_menu_msg: e.target.value })} />
        <Button style={{ marginTop: 8 }} onClick={() => save('welcome_menu_msg')}>Сохранить</Button>
      </Card>
      <Card title="О нас">
        <Input.TextArea rows={4} value={cfg.about_text} onChange={(e) => setCfg({ ...cfg, about_text: e.target.value })} />
        <Button style={{ marginTop: 8 }} onClick={() => save('about_text')}>Сохранить</Button>
      </Card>
    </Space>
  );
};

export default BotConfig;
