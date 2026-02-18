import React, { useContext } from 'react';
import { Layout, Menu, Button } from 'antd';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import AuthContext from '../contexts/AuthContext';

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout } = useContext(AuthContext);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider>
        <div style={{ color: '#fff', padding: 16, fontWeight: 'bold' }}>Chel3D Админка</div>
        <Menu
          theme="dark"
          selectedKeys={[location.pathname]}
          onClick={({ key }) => navigate(key)}
          items={[
            { key: '/dashboard', label: 'Сводка' },
            { key: '/orders', label: 'Заявки' },
            { key: '/bot-config', label: 'Тексты бота' },
          ]}
        />
      </Layout.Sider>
      <Layout>
        <Layout.Header style={{ background: '#fff', textAlign: 'right' }}><Button onClick={() => { logout(); navigate('/login'); }}>Выйти</Button></Layout.Header>
        <Layout.Content style={{ margin: 16, background: '#fff', padding: 16 }}><Outlet /></Layout.Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
