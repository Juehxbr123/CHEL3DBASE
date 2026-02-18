import React, { useContext } from 'react';
import { Button, Card, Form, Input, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import AuthContext from '../contexts/AuthContext';

const Login = () => {
  const { login } = useContext(AuthContext);
  const navigate = useNavigate();

  const submit = async (v) => {
    const result = await login(v.password);
    if (!result.success) return message.error(result.error);
    message.success('Добро пожаловать');
    navigate('/dashboard');
  };

  return (
    <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh' }}>
      <Card title="Вход в админку" style={{ width: 360 }}>
        <Form onFinish={submit}>
          <Form.Item name="password" rules={[{ required: true, message: 'Введите пароль' }]}>
            <Input.Password placeholder="Пароль" />
          </Form.Item>
          <Button type="primary" htmlType="submit" block>Войти</Button>
        </Form>
      </Card>
    </div>
  );
};

export default Login;
