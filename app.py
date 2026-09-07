from flask import Flask, request, jsonify, render_template_string
import sqlite3
import hashlib
import secrets
from datetime import datetime
import jwt
from config import Config
from database import init_db, get_connection

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db()

# HTML Templates
CUSTOMER_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>VTU Data Hub</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; background: #f5f5f5; }
        .header { background: #667eea; color: white; padding: 15px; text-align: center; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; background: white; border: none; border-radius: 8px; cursor: pointer; }
        .tab.active { background: #667eea; color: white; }
        .page { display: none; background: white; padding: 20px; border-radius: 8px; }
        .page.active { display: block; }
        .network-card { border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 15px; }
        .plan-item { padding: 12px; border: 1px solid #eee; border-radius: 5px; margin: 8px 0; cursor: pointer; }
        .plan-item:active { background: #f0f0f0; }
        input, button { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { background: #667eea; color: white; border: none; cursor: pointer; font-weight: bold; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: white; padding: 20px; border-radius: 8px; width: 90%; max-width: 400px; }
        .balance { font-size: 36px; font-weight: bold; text-align: center; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h2>📱 VTU Data Hub</h2>
        <span id="username"></span>
    </div>
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('buy', this)">Buy Data</button>
            <button class="tab" onclick="showTab('wallet', this)">Wallet</button>
            <button class="tab" onclick="showTab('history', this)">History</button>
        </div>
        
        <div id="buy" class="page active">
            <div id="networks"></div>
        </div>
        
        <div id="wallet" class="page">
            <div class="balance" id="balance">₦0</div>
            <input type="number" id="fundAmount" placeholder="Amount to fund (₦)" min="100">
            <button onclick="fundWallet()">Fund Wallet</button>
        </div>
        
        <div id="history" class="page">
            <div id="transactions"></div>
        </div>
    </div>
    
    <div id="authModal" class="modal">
        <div class="modal-content">
            <h3 id="authTitle">Login</h3>
            <div id="loginForm">
                <input type="email" id="loginEmail" placeholder="Email">
                <input type="password" id="loginPassword" placeholder="Password">
                <button onclick="login()">Login</button>
            </div>
            <div id="registerForm" style="display:none;">
                <input type="text" id="regUsername" placeholder="Username">
                <input type="email" id="regEmail" placeholder="Email">
                <input type="tel" id="regPhone" placeholder="Phone">
                <input type="password" id="regPassword" placeholder="Password">
                <button onclick="register()">Register</button>
            </div>
            <p style="text-align:center;margin-top:10px;">
                <a href="#" onclick="toggleAuth()" id="toggleLink">Create account</a>
            </p>
        </div>
    </div>
    
    <div id="purchaseModal" class="modal">
        <div class="modal-content">
            <h3>Confirm Purchase</h3>
            <p id="purchaseDetails"></p>
            <input type="tel" id="purchasePhone" placeholder="Phone number">
            <button onclick="confirmPurchase()">Confirm</button>
            <button onclick="closePurchase()" style="background:#ff4757;">Cancel</button>
        </div>
    </div>
    
    <script>
        let token = localStorage.getItem('token');
        let selectedPlan = null;
        
        if (token) {
            document.getElementById('authModal').classList.remove('active');
            loadNetworks();
            loadWallet();
        } else {
            document.getElementById('authModal').classList.add('active');
        }
        
        function showTab(tab, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            if (tab === 'wallet') loadWallet();
            if (tab === 'history') loadHistory();
        }
        
        function toggleAuth() {
            const loginForm = document.getElementById('loginForm');
            const registerForm = document.getElementById('registerForm');
            const title = document.getElementById('authTitle');
            const link = document.getElementById('toggleLink');
            if (loginForm.style.display === 'none') {
                loginForm.style.display = 'block';
                registerForm.style.display = 'none';
                title.textContent = 'Login';
                link.textContent = 'Create account';
            } else {
                loginForm.style.display = 'none';
                registerForm.style.display = 'block';
                title.textContent = 'Register';
                link.textContent = 'Login instead';
            }
        }
        
        async function login() {
            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else {
                token = data.token;
                localStorage.setItem('token', token);
                document.getElementById('username').textContent = data.username;
                document.getElementById('authModal').classList.remove('active');
                loadNetworks();
                loadWallet();
            }
        }
        
        async function register() {
            const user = {
                username: document.getElementById('regUsername').value,
                email: document.getElementById('regEmail').value,
                phone: document.getElementById('regPhone').value,
                password: document.getElementById('regPassword').value
            };
            const res = await fetch('/api/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(user)
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else {
                token = data.token;
                localStorage.setItem('token', token);
                document.getElementById('username').textContent = user.username;
                document.getElementById('authModal').classList.remove('active');
                loadNetworks();
                loadWallet();
            }
        }
        
        async function loadNetworks() {
            const res = await fetch('/api/networks', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const networks = await res.json();
            const container = document.getElementById('networks');
            container.innerHTML = '';
            networks.forEach(network => {
                const card = document.createElement('div');
                card.className = 'network-card';
                card.innerHTML = '<h3 style="color:' + network.color + '">' + network.name + '</h3>';
                network.plans.forEach(plan => {
                    const planDiv = document.createElement('div');
                    planDiv.className = 'plan-item';
                    planDiv.innerHTML = '<strong>' + plan.data_amount + '</strong> - ₦' + plan.price + ' (' + plan.validity + ')';
                    planDiv.onclick = function() { selectPlan(plan, network.name); };
                    card.appendChild(planDiv);
                });
                container.appendChild(card);
            });
        }
        
        function selectPlan(plan, networkName) {
            selectedPlan = {...plan, networkName};
            document.getElementById('purchaseDetails').innerHTML = 
                '<strong>Network:</strong> ' + networkName + '<br>' +
                '<strong>Data:</strong> ' + plan.data_amount + '<br>' +
                '<strong>Validity:</strong> ' + plan.validity + '<br>' +
                '<strong>Price:</strong> ₦' + plan.price;
            document.getElementById('purchaseModal').classList.add('active');
        }
        
        function closePurchase() {
            document.getElementById('purchaseModal').classList.remove('active');
            selectedPlan = null;
        }
        
        async function confirmPurchase() {
            const phone = document.getElementById('purchasePhone').value;
            if (!phone) {
                alert('Please enter phone number');
                return;
            }
            const res = await fetch('/api/purchase', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token},
                body: JSON.stringify({plan_id: selectedPlan.id, phone_number: phone})
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else {
                alert('Purchase successful! Ref: ' + data.reference);
                closePurchase();
                document.getElementById('purchasePhone').value = '';
                loadWallet();
            }
        }
        
        async function loadWallet() {
            const res = await fetch('/api/wallet', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const data = await res.json();
            document.getElementById('balance').textContent = '₦' + data.balance.toFixed(2);
        }
        
        async function fundWallet() {
            const amount = document.getElementById('fundAmount').value;
            if (!amount || amount < 100) {
                alert('Minimum funding is ₦100');
                return;
            }
            const res = await fetch('/api/fund-wallet', {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token},
                body: JSON.stringify({amount: parseFloat(amount)})
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else {
                alert('Wallet funded! Ref: ' + data.reference);
                document.getElementById('fundAmount').value = '';
                loadWallet();
            }
        }
        
        async function loadHistory() {
            const res = await fetch('/api/transactions', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const transactions = await res.json();
            const container = document.getElementById('transactions');
            container.innerHTML = '';
            if (transactions.length === 0) {
                container.innerHTML = '<p>No transactions yet</p>';
                return;
            }
            transactions.forEach(tx => {
                const div = document.createElement('div');
                div.style.padding = '10px';
                div.style.borderBottom = '1px solid #eee';
                div.innerHTML = '<strong>' + (tx.description || tx.type) + '</strong><br>' +
                              '<small>' + tx.created_at + '</small><br>' +
                              '<strong style="color:' + (tx.type === 'wallet_fund' ? 'green' : 'red') + '">' +
                              (tx.type === 'wallet_fund' ? '+' : '-') + '₦' + tx.amount.toFixed(2) + '</strong>';
                container.appendChild(div);
            });
        }
    </script>
</body>
</html>
'''

ADMIN_LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login - VTU</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; background: #1a1a2e; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .box { background: white; padding: 30px; border-radius: 10px; width: 90%; max-width: 400px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { width: 100%; padding: 12px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>
    <div class="box">
        <h2 style="text-align:center;">Admin Login</h2>
        <input type="email" id="email" placeholder="Admin Email" value="admin@vtu.com">
        <input type="password" id="password" placeholder="Password" value="admin123">
        <button onclick="login()">Login</button>
    </div>
    <script>
        async function login() {
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const res = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({email, password})
            });
            const data = await res.json();
            if (data.error) {
                alert(data.error);
            } else if (data.role !== 'admin') {
                alert('Access denied. Admin only.');
            } else {
                localStorage.setItem('adminToken', data.token);
                window.location.href = '/admin';
            }
        }
    </script>
</body>
</html>
'''

ADMIN_PAGE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - VTU</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: Arial; background: #f5f5f5; }
        .header { background: #1a1a2e; color: white; padding: 15px; text-align: center; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .tabs { display: flex; gap: 5px; margin-bottom: 20px; overflow-x: auto; }
        .tab { flex: 1; padding: 10px; background: white; border: none; border-radius: 8px; cursor: pointer; font-size: 12px; }
        .tab.active { background: #667eea; color: white; }
        .page { display: none; background: white; padding: 20px; border-radius: 8px; }
        .page.active { display: block; }
        .list-item { background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; }
        input, select { width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; }
        button { padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal.active { display: flex; }
        .modal-content { background: white; padding: 20px; border-radius: 8px; width: 90%; max-width: 400px; }
    </style>
</head>
<body>
    <div class="header">
        <h2>VTU Admin Panel</h2>
    </div>
    <div class="container">
        <div class="tabs">
            <button class="tab active" onclick="showTab('dashboard', this)">Dashboard</button>
            <button class="tab" onclick="showTab('plans', this)">Data Plans</button>
            <button class="tab" onclick="showTab('users', this)">Users</button>
            <button class="tab" onclick="showTab('transactions', this)">Transactions</button>
        </div>
        
        <div id="dashboard" class="page active">
            <h3>Dashboard</h3>
            <div id="stats"></div>
        </div>
        
        <div id="plans" class="page">
            <h3>Data Plans</h3>
            <button onclick="showAddPlan()">Add Plan</button>
            <div id="plansList"></div>
        </div>
        
        <div id="users" class="page">
            <h3>Users</h3>
            <div id="usersList"></div>
        </div>
        
        <div id="transactions" class="page">
            <h3>Transactions</h3>
            <div id="transactionsList"></div>
        </div>
    </div>
    
    <div id="planModal" class="modal">
        <div class="modal-content">
            <h3>Add/Edit Plan</h3>
            <input type="hidden" id="planId">
            <select id="planNetwork"></select>
            <input type="text" id="planData" placeholder="Data Amount (e.g., 1GB)">
            <input type="text" id="planValidity" placeholder="Validity (e.g., 30 days)">
            <input type="number" id="planPrice" placeholder="Price (₦)">
            <button onclick="savePlan()">Save</button>
            <button onclick="closeModal()" style="background:#ff4757;">Cancel</button>
        </div>
    </div>
    
    <script>
        let token = localStorage.getItem('adminToken');
        if (!token) {
            window.location.href = '/admin-login';
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
            loadPlans();
            loadUsers();
            loadTransactions();
        });
        
        function showTab(tab, btn) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            btn.classList.add('active');
            document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
        }
        
        async function loadDashboard() {
            const res = await fetch('/api/admin/stats', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const stats = await res.json();
            document.getElementById('stats').innerHTML = `
                <div class="list-item"><strong>Total Users:</strong> ${stats.total_users}</div>
                <div class="list-item"><strong>Active Users:</strong> ${stats.active_users}</div>
                <div class="list-item"><strong>Total Purchases:</strong> ${stats.total_purchases}</div>
                <div class="list-item"><strong>Total Revenue:</strong> ₦${stats.total_revenue}</div>
            `;
        }
        
        async function loadPlans() {
            const res = await fetch('/api/admin/plans', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const plans = await res.json();
            const container = document.getElementById('plansList');
            container.innerHTML = '';
            plans.forEach(plan => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <strong>${plan.network_name} - ${plan.data_amount}</strong><br>
                    <small>Price: ₦${plan.price} | Validity: ${plan.validity}</small><br>
                    <button onclick="editPlan(${JSON.stringify(plan).replace(/"/g, '&quot;')})">Edit Price</button>
                `;
                container.appendChild(div);
            });
            
            // Load networks for dropdown
            const networksRes = await fetch('/api/admin/networks', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const networks = await networksRes.json();
            const select = document.getElementById('planNetwork');
            select.innerHTML = '<option value="">Select Network</option>';
            networks.forEach(n => {
                select.innerHTML += `<option value="${n.id}">${n.name}</option>`;
            });
        }
        
        async function loadUsers() {
            const res = await fetch('/api/admin/users', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const users = await res.json();
            const container = document.getElementById('usersList');
            container.innerHTML = '';
            users.forEach(user => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <strong>${user.username}</strong><br>
                    <small>${user.email} | ${user.phone}</small>
                `;
                container.appendChild(div);
            });
        }
        
        async function loadTransactions() {
            const res = await fetch('/api/admin/transactions', {
                headers: {'Authorization': 'Bearer ' + token}
            });
            const transactions = await res.json();
            const container = document.getElementById('transactionsList');
            container.innerHTML = '';
            transactions.forEach(tx => {
                const div = document.createElement('div');
                div.className = 'list-item';
                div.innerHTML = `
                    <strong>${tx.username} - ${tx.description || tx.type}</strong><br>
                    <small>${tx.created_at} | Ref: ${tx.reference}</small><br>
                    <strong>₦${tx.amount}</strong>
                `;
                container.appendChild(div);
            });
        }
        
        function showAddPlan() {
            document.getElementById('planId').value = '';
            document.getElementById('planData').value = '';
            document.getElementById('planValidity').value = '';
            document.getElementById('planPrice').value = '';
            document.getElementById('planModal').classList.add('active');
        }
        
        function editPlan(plan) {
            document.getElementById('planId').value = plan.id;
            document.getElementById('planNetwork').value = plan.network_id;
            document.getElementById('planData').value = plan.data_amount;
            document.getElementById('planValidity').value = plan.validity;
            document.getElementById('planPrice').value = plan.price;
            document.getElementById('planModal').classList.add('active');
        }
        
        async function savePlan() {
            const id = document.getElementById('planId').value;
            const data = {
                network_id: parseInt(document.getElementById('planNetwork').value),
                data_amount: document.getElementById('planData').value,
                validity: document.getElementById('planValidity').value,
                price: parseFloat(document.getElementById('planPrice').value)
            };
            const url = id ? '/api/admin/plans/' + id : '/api/admin/plans';
            const method = id ? 'PUT' : 'POST';
            const res = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token},
                body: JSON.stringify(data)
            });
            if (res.ok) {
                closeModal();
                loadPlans();
            }
        }
        
        function closeModal() {
            document.getElementById('planModal').classList.remove('active');
        }
    </script>
</body>
</html>
'''

# Routes
@app.route('/')
def customer_page():
    return render_template_string(CUSTOMER_PAGE)

@app.route('/admin-login')
def admin_login_page():
    return render_template_string(ADMIN_LOGIN_PAGE)

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_PAGE)

# Helper functions
def verify_token(token_str):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token_str, app.config['JWT_SECRET'], algorithms=['HS256'])
        return payload
    except:
        return None

def get_auth_token():
    """Extract and verify authorization token"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token_str = auth_header[7:]
    return verify_token(token_str)

# API Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT id FROM users WHERE email = ?', (data.get('email'),))
    if c.fetchone():
        conn.close()
        return jsonify({'error': 'Email already registered'}), 400
    
    password_hash = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    c.execute('INSERT INTO users (username, email, password, phone) VALUES (?, ?, ?, ?)',
             (data.get('username'), data.get('email'), password_hash, data.get('phone')))
    user_id = c.lastrowid
    c.execute('INSERT INTO wallets (user_id, balance) VALUES (?, 0)', (user_id,))
    conn.commit()
    conn.close()
    
    token = jwt.encode({'user_id': user_id, 'role': 'customer'}, app.config['JWT_SECRET'], algorithm='HS256')
    return jsonify({'token': token, 'role': 'customer', 'username': data.get('username')}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM users WHERE email = ?', (data.get('email'),))
    user = c.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    password_hash = hashlib.sha256(data.get('password', '').encode()).hexdigest()
    if user[3] != password_hash:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    token = jwt.encode({'user_id': user[0], 'role': user[5]}, app.config['JWT_SECRET'], algorithm='HS256')
    return jsonify({'token': token, 'role': user[5], 'username': user[1]}), 200

@app.route('/api/networks')
def get_networks():
    payload = get_auth_token()
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM networks WHERE is_active = 1')
    networks = c.fetchall()
    result = []
    for network in networks:
        c.execute('SELECT * FROM data_plans WHERE network_id = ? AND is_active = 1', (network[0],))
        plans = c.fetchall()
        result.append({
            'id': network[0],
            'name': network[1],
            'color': network[2],
            'plans': [{'id': p[0], 'data_amount': p[2], 'validity': p[3], 'price': p[4]} for p in plans]
        })
    conn.close()
    return jsonify(result), 200

@app.route('/api/wallet')
def get_wallet():
    payload = get_auth_token()
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = payload['user_id']
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return jsonify({'balance': result[0] if result else 0}), 200

@app.route('/api/fund-wallet', methods=['POST'])
def fund_wallet():
    payload = get_auth_token()
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = payload['user_id']
    data = request.json
    amount = data.get('amount', 0)
    
    if amount < 100:
        return jsonify({'error': 'Minimum funding is ₦100'}), 400
    
    reference = f"FUND-{secrets.token_hex(6).upper()}"
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE wallets SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    c.execute('INSERT INTO transactions (user_id, type, amount, reference, description) VALUES (?, ?, ?, ?, ?)',
             (user_id, 'wallet_fund', amount, reference, 'Wallet funding'))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'reference': reference}), 200

@app.route('/api/purchase', methods=['POST'])
def purchase():
    payload = get_auth_token()
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = payload['user_id']
    data = request.json
    plan_id = data.get('plan_id')
    phone = data.get('phone_number')
    
    conn = get_connection()
    c = conn.cursor()
    
    c.execute('SELECT * FROM data_plans WHERE id = ? AND is_active = 1', (plan_id,))
    plan = c.fetchone()
    if not plan:
        conn.close()
        return jsonify({'error': 'Plan not found'}), 404
    
    c.execute('SELECT balance FROM wallets WHERE user_id = ?', (user_id,))
    balance_result = c.fetchone()
    balance = balance_result[0] if balance_result else 0
    
    if balance < plan[4]:
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    
    c.execute('SELECT name FROM networks WHERE id = ?', (plan[1],))
    network_name_result = c.fetchone()
    network_name = network_name_result[0] if network_name_result else 'Unknown'
    
    reference = f"VTU-{secrets.token_hex(6).upper()}"
    c.execute('UPDATE wallets SET balance = balance - ? WHERE user_id = ?', (plan[4], user_id))
    c.execute('INSERT INTO transactions (user_id, type, amount, reference, description) VALUES (?, ?, ?, ?, ?)',
             (user_id, 'data_purchase', plan[4], reference, f"{network_name} {plan[2]} for {phone}"))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'reference': reference}), 200

@app.route('/api/transactions')
def get_transactions():
    payload = get_auth_token()
    if not payload:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = payload['user_id']
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM transactions WHERE user_id = ? ORDER BY created_at DESC LIMIT 50', (user_id,))
    transactions = c.fetchall()
    conn.close()
    return jsonify([{'id': t[0], 'type': t[2], 'amount': t[3], 'reference': t[4],
                     'description': t[5], 'created_at': t[6]} for t in transactions]), 200

# Admin API Routes
@app.route('/api/admin/stats')
def admin_stats():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users WHERE role = "customer"')
    total_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM users WHERE role = "customer" AND is_active = 1')
    active_users = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM transactions WHERE type = "data_purchase"')
    total_purchases = c.fetchone()[0]
    c.execute('SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE type = "data_purchase"')
    total_revenue = c.fetchone()[0]
    conn.close()
    return jsonify({'total_users': total_users, 'active_users': active_users,
                   'total_purchases': total_purchases, 'total_revenue': total_revenue}), 200

@app.route('/api/admin/networks')
def admin_get_networks():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM networks')
    networks = c.fetchall()
    conn.close()
    return jsonify([{'id': n[0], 'name': n[1], 'color': n[2], 'is_active': n[3]} for n in networks]), 200

@app.route('/api/admin/plans')
def admin_get_plans():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT p.*, n.name FROM data_plans p JOIN networks n ON p.network_id = n.id')
    plans = c.fetchall()
    conn.close()
    return jsonify([{'id': p[0], 'network_id': p[1], 'data_amount': p[2], 'validity': p[3],
                     'price': p[4], 'is_active': p[5], 'network_name': p[6]} for p in plans]), 200

@app.route('/api/admin/plans', methods=['POST'])
def admin_add_plan():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute('INSERT INTO data_plans (network_id, data_amount, validity, price) VALUES (?, ?, ?, ?)',
             (data.get('network_id'), data.get('data_amount'), data.get('validity'), data.get('price')))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 201

@app.route('/api/admin/plans/<int:plan_id>', methods=['PUT'])
def admin_update_plan(plan_id):
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE data_plans SET data_amount = ?, validity = ?, price = ? WHERE id = ?',
             (data.get('data_amount'), data.get('validity'), data.get('price'), plan_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

@app.route('/api/admin/users')
def admin_get_users():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, email, phone, is_active FROM users WHERE role != "admin"')
    users = c.fetchall()
    conn.close()
    return jsonify([{'id': u[0], 'username': u[1], 'email': u[2], 'phone': u[3], 'is_active': u[4]} for u in users]), 200

@app.route('/api/admin/transactions')
def admin_get_transactions():
    payload = get_auth_token()
    if not payload or payload.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT t.*, u.username FROM transactions t JOIN users u ON t.user_id = u.id ORDER BY t.created_at DESC LIMIT 100')
    transactions = c.fetchall()
    conn.close()
    return jsonify([{'id': t[0], 'type': t[2], 'amount': t[3], 'reference': t[4],
                     'description': t[5], 'created_at': t[6], 'username': t[7]} for t in transactions]), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
