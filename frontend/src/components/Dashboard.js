import React, { useEffect, useState } from 'react';
import { Card, Col, Row } from 'antd';
import axios from 'axios';

const Dashboard = () => {
    const [stats, setStats] = useState({ total_orders: 0, new_orders: 0, active_orders: 0 });
  useEffect(() => { axios.get('/api/orders/stats').then((r) => setStats(r.data)); }, []);
  return (
    <>
      <h2>Сводка</h2>
      <Row gutter={16}>
        <Col span={8}><Card title="Всего заявок">{stats.total_orders}</Card></Col>
        <Col span={8}><Card title="Новых">{stats.new_orders}</Card></Col>
        <Col span={8}><Card title="В работе">{stats.active_orders}</Card></Col>
      </Row>
    </>
  );
};

export default Dashboard;
