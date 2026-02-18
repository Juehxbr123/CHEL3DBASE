import React, { useEffect, useState } from 'react';
import { Button, Card, Descriptions, Modal, Select, Space, Table, Tag, message } from 'antd';
import axios from 'axios';

const СТАТУСЫ = ['Черновик', 'Новая заявка', 'В работе', 'Готово', 'Отменено'];

const статусЦвет = {
  'Черновик': 'default',
  'Новая заявка': 'blue',
  'В работе': 'orange',
  'Готово': 'green',
  'Отменено': 'red',
};

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [current, setCurrent] = useState(null);

  const load = async () => {
    const res = await axios.get('/api/orders/');
    setOrders(res.data);
  };

  useEffect(() => { load(); }, []);

  const setStatus = async (id, status) => {
    try {
      await axios.put(`/api/orders/${id}`, { status });
      message.success('Статус обновлён');
      load();
    } catch {
      message.error('Не удалось обновить статус');
    }
  };

    return (
       <>
      <h2>Заявки</h2>
      <Table rowKey="id" dataSource={orders} pagination={{ pageSize: 20 }} columns={[
        { title: '№', dataIndex: 'id' },
        { title: 'Клиент', render: (_, r) => `${r.full_name || ''} @${r.username || ''}` },
        { title: 'Тип заявки', dataIndex: 'request_type' },
        { title: 'Кратко', dataIndex: 'summary', ellipsis: true },
        { title: 'Статус', render: (_, r) => (
          <Select value={r.status} style={{ width: 160 }} onChange={(v) => setStatus(r.id, v)}>
            {СТАТУСЫ.map((s) => <Select.Option key={s} value={s}>{s}</Select.Option>)}
          </Select>
                  ) },
        { title: 'Метка', render: (_, r) => <Tag color={статусЦвет[r.status]}>{r.status}</Tag> },
        { title: 'Действия', render: (_, r) => <Button onClick={() => setCurrent(r)}>Открыть</Button> },
      ]} />

      <Modal open={!!current} onCancel={() => setCurrent(null)} footer={null} width={900} title={`Заявка #${current?.id || ''}`}>
        {current && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Тип заявки">{current.request_type || '-'}</Descriptions.Item>
              <Descriptions.Item label="Краткое описание">{current.summary || '-'}</Descriptions.Item>
              <Descriptions.Item label="Создана">{current.created_at}</Descriptions.Item>
            </Descriptions>
            <Card title="Выбранные параметры">
              {Object.entries(current.order_payload || {}).map(([k, v]) => (
                <p key={k}><b>{k}:</b> {typeof v === 'object' ? JSON.stringify(v) : String(v)}</p>
              ))}
            </Card>
          </Space>
        )}
      </Modal>
    </>
  );
};

export default Orders;
