import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = "http://localhost:8000";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [role, setRole] = useState(localStorage.getItem('role') || 'customer');
  
  // Auth state
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [selectedRole, setSelectedRole] = useState('customer');

  // Data states
  const [restaurants, setRestaurants] = useState([]);
  const [selectedRest, setSelectedRest] = useState(null);
  const [menu, setMenu] = useState([]);
  const [cart, setCart] = useState([]);
  const [orders, setOrders] = useState([]);
  const [aiQuery, setAiQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');

  useEffect(() => {
    if (token) {
      fetchOrders();
      if (role === 'customer') fetchRestaurants();
    }
  }, [token, role]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post(`${API_URL}/login`, { email, password });
      const jwt = res.data.access_token || res.data.token;
      const userRole = res.data.role || selectedRole;
      
      setToken(jwt);
      setRole(userRole);
      localStorage.setItem('token', jwt);
      localStorage.setItem('role', userRole);
    } catch (err) {
      alert("Login failed. Check backend connection or credentials.");
    }
  };

  const fetchRestaurants = async () => {
    try {
      const res = await axios.get(`${API_URL}/restaurants`);
      setRestaurants(res.data);
    } catch (err) { console.error(err); }
  };

  const fetchMenu = async (restId) => {
    try {
      const res = await axios.get(`${API_URL}/restaurants/${restId}/menu`);
      setMenu(res.data);
      setSelectedRest(restId);
    } catch (err) { console.error(err); }
  };

  const addToCart = (item) => {
    setCart([...cart, { ...item, quantity: 1 }]);
  };

  const placeOrder = async () => {
    try {
      await axios.post(`${API_URL}/orders`, {
        restaurant_id: selectedRest,
        items: cart.map(i => ({ menu_item_id: i.id, quantity: i.quantity }))
      }, { headers: { Authorization: `Bearer ${token}` } });
      alert("Order placed successfully with mock payment!");
      setCart([]);
      fetchOrders();
    } catch (err) { alert("Failed to place order"); }
  };

  const fetchOrders = async () => {
    try {
      const res = await axios.get(`${API_URL}/orders`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrders(res.data);
    } catch (err) { console.error(err); }
  };

  const updateOrderStatus = async (orderId, status) => {
    try {
      await axios.patch(`${API_URL}/orders/${orderId}/status`, { status }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      fetchOrders();
    } catch (err) { alert("Failed to update status"); }
  };

  const getAiInsights = async () => {
    try {
      const res = await axios.post(`${API_URL}/customer/insights`, { query: aiQuery }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAiResponse(res.data.insight || res.data.response);
    } catch (err) { alert("AI Insight failed"); }
  };

  if (!token) {
    return (
      <div style={{ fontFamily: 'sans-serif', padding: '40px', maxWidth: '400px', margin: 'auto' }}>
        <h2>CampusBite Login</h2>
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: '10px' }}>
            <label>Email: </label><br/>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required style={{ width: '100%', padding: '8px' }} />
          </div>
          <div style={{ marginBottom: '10px' }}>
            <label>Password: </label><br/>
            <input type="password" value={password} onChange={e => setPassword(e.target.value)} required style={{ width: '100%', padding: '8px' }} />
          </div>
          <div style={{ marginBottom: '15px' }}>
            <label>Role: </label><br/>
            <select value={selectedRole} onChange={e => setSelectedRole(e.target.value)} style={{ width: '100%', padding: '8px' }}>
              <option value="customer">Customer</option>
              <option value="owner">Restaurant Owner</option>
              <option value="delivery_partner">Delivery Partner</option>
            </select>
          </div>
          <button type="submit" style={{ width: '100%', padding: '10px', background: '#ff4757', color: '#fff', border: 'none', cursor: 'pointer' }}>Login</button>
        </form>
      </div>
    );
  }

  return (
    <div style={{ fontFamily: 'sans-serif', padding: '20px', maxWidth: '900px', margin: 'auto' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid #ccc', paddingBottom: '10px' }}>
        <h2>CampusBite Dashboard ({role.toUpperCase()})</h2>
        <button onClick={() => { localStorage.clear(); setToken(''); }} style={{ background: '#333', color: '#fff', border: 'none', padding: '5px 10px', cursor: 'pointer' }}>Logout</button>
      </header>

      {role === 'customer' && (
        <div>
          <h3>Available Restaurants</h3>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            {restaurants.map(r => (
              <div key={r.id} onClick={() => fetchMenu(r.id)} style={{ border: '1px solid #ddd', padding: '15px', cursor: 'pointer', background: selectedRest === r.id ? '#f0f0f0' : '#fff' }}>
                <h4>{r.name}</h4>
                <p>{r.cuisine}</p>
              </div>
            ))}
          </div>

          {selectedRest && (
            <div>
              <h3>Menu</h3>
              <ul>
                {menu.map(item => (
                  <li key={item.id} style={{ marginBottom: '10px' }}>
                    {item.name} - ${item.price} <button onClick={() => addToCart(item)} style={{ marginLeft: '10px' }}>Add to Cart</button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {cart.length > 0 && (
            <div style={{ background: '#f9f9f9', padding: '15px', marginTop: '20px' }}>
              <h3>Your Cart</h3>
              <ul>{cart.map((c, i) => <li key={i}>{c.name} (x{c.quantity})</li>)}</ul>
              <button onClick={placeOrder} style={{ background: '#2ed573', color: '#fff', border: 'none', padding: '10px 20px', cursor: 'pointer' }}>Place Order (Mock Pay)</button>
            </div>
          )}

          <div style={{ marginTop: '30px', background: '#f1f2f6', padding: '15px' }}>
            <h3>AI Order Insights</h3>
            <input type="text" placeholder="e.g., Summarize my last 5 orders" value={aiQuery} onChange={e => setAiQuery(e.target.value)} style={{ width: '70%', padding: '8px' }} />
            <button onClick={getAiInsights} style={{ padding: '8px 15px', marginLeft: '10px' }}>Ask AI</button>
            {aiResponse && <p style={{ background: '#fff', padding: '10px', marginTop: '10px' }}>{aiResponse}</p>}
          </div>
        </div>
      )}

      {(role === 'owner' || role === 'delivery_partner') && (
        <div>
          <h3>Incoming Orders</h3>
          <table border="1" cellPadding="10" style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
            <thead>
              <tr><th>Order ID</th><th>Status</th><th>Actions</th></tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id}>
                  <td>{o.id}</td>
                  <td>{o.status}</td>
                  <td>
                    {role === 'owner' && o.status === 'PLACED' && (
                      <button onClick={() => updateOrderStatus(o.id, 'ACCEPTED')}>Accept</button>
                    )}
                    {role === 'owner' && o.status === 'READY' && (
                      <button onClick={() => updateOrderStatus(o.id, 'ASSIGNED')}>Assign Driver</button>
                    )}
                    {role === 'delivery_partner' && o.status === 'ASSIGNED' && (
                      <button onClick={() => updateOrderStatus(o.id, 'OUT_FOR_DELIVERY')}>Out for Delivery</button>
                    )}
                    {role === 'delivery_partner' && o.status === 'OUT_FOR_DELIVERY' && (
                      <button onClick={() => updateOrderStatus(o.id, 'DELIVERED')}>Mark Delivered</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
