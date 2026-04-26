from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import secrets
import requests
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# ========== KONFIGURASI ==========
TELEGRAM_TOKEN = "8612708533:AAFGAqwjsqASljPT8-5ZXKYVcIwCK95w6W8"
TELEGRAM_CHAT_ID = "7297085736"
DANA_NUMBER = "6289654652309"

# ========== API TOP UP BOY ==========
TOPUPBOY_API_KEY = "YTiobTi9-UPQegDAS-msQPjh4i-Cszu80YN"
TOPUPBOY_API_URL = "https://topupboy.com/api/v1/transaction"  # GANTI DENGAN ENDPOINT ASLI

# ========== PRODUK ==========
PRODUCTS = {
    'ff_5': {'name': '5 Diamonds', 'game': 'FF', 'price': 1400, 'sku': 'FF_5_DIAMOND'},
    'ff_10': {'name': '10 Diamonds', 'game': 'FF', 'price': 1900, 'sku': 'FF_10_DIAMOND'},
    'ff_20': {'name': '20 Diamonds', 'game': 'FF', 'price': 3800, 'sku': 'FF_20_DIAMOND'},
    'ff_50': {'name': '50 Diamonds', 'game': 'FF', 'price': 8000, 'sku': 'FF_50_DIAMOND'},
    'ff_100': {'name': '100 Diamonds', 'game': 'FF', 'price': 16500, 'sku': 'FF_100_DIAMOND'},
    'ff_200': {'name': '200 Diamonds', 'game': 'FF', 'price': 26500, 'sku': 'FF_200_DIAMOND'},
    'ff_140': {'name': '140 Diamonds', 'game': 'FF', 'price': 18800, 'sku': 'FF_140_DIAMOND'},
    'ff_130': {'name': '130 Diamonds', 'game': 'FF', 'price': 17500, 'sku': 'FF_130_DIAMOND'},
    'ff_145': {'name': '145 Diamonds', 'game': 'FF', 'price': 19500, 'sku': 'FF_145_DIAMOND'},
    'ff_125': {'name': '125 Diamonds', 'game': 'FF', 'price': 16800, 'sku': 'FF_125_DIAMOND'},
    'ff_90': {'name': '90 Diamonds', 'game': 'FF', 'price': 12800, 'sku': 'FF_90_DIAMOND'},
    'ff_300': {'name': '300 Diamonds', 'game': 'FF', 'price': 39600, 'sku': 'FF_300_DIAMOND'},
}

def kirim_ke_telegram(pesan):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": pesan, "parse_mode": "HTML"}
        requests.post(url, json=data)
    except Exception as e:
        print(f"Error Telegram: {e}")

def topup_via_api(user_id, sku, amount):
def topup_via_api(user_id, sku, amount):
    try:
        headers = {
            "Authorization": f"Bearer {TOPUPBOY_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "game": "freefire",
            "user_id": user_id,
            "sku": sku,
            "amount": amount
        }

        print(f"📤 Sending to: {TOPUPBOY_API_URL}")
        print(f"Payload: {payload}")

        response = requests.post(TOPUPBOY_API_URL, json=payload, headers=headers, timeout=30)

        print(f"📥 Status Code: {response.status_code}")
        print(f"📥 Response Text: {response.text[:200]}")  # tampilkan 200 karakter pertama

        if response.status_code == 200:
            try:
                result = response.json()
                if result.get('status') == 'success':
                    return {'success': True, 'ref_id': result.get('ref_id')}
                else:
                    return {'success': False, 'message': result.get('message', 'Gagal topup')}
            except Exception as json_err:
                return {'success': False, 'message': f"Response bukan JSON: {response.text[:100]}"}
        else:
            return {'success': False, 'message': f"HTTP {response.status_code}: {response.text[:100]}"}
    except Exception as e:
        return {'success': False, 'message': str(e)}

def bulatkan_harga_cash(harga):
    if harga <= 1000:
        return 2000
    else:
        return ((harga + 999) // 1000) * 1000

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login_owner'))
        return f(*args, **kwargs)
    return decorated_function

# ========== ROUTES ==========
@app.route('/')
def index():
    return render_template('juanshop.html', products=PRODUCTS, dana_number=DANA_NUMBER)

@app.route('/api/create-order', methods=['POST'])
def create_order():
    try:
        data = request.json
        order_id = secrets.token_hex(4).upper()
        product = PRODUCTS.get(data.get('product_code'))
        customer_phone = data.get('customer_phone')
        metode = data.get('metode', 'dana')
        voucher = data.get('voucher')
        final_price = data.get('final_price')

        if not product:
            return jsonify({'success': False, 'message': 'Produk tidak ditemukan'}), 400

        harga_dasar = final_price if final_price else product['price']
        
        if metode == 'cash':
            harga_bayar = bulatkan_harga_cash(harga_dasar)
        else:
            harga_bayar = harga_dasar

        pesan_telegram = f"""
🛒 ORDER BARU!

🆔 ORDER ID: {order_id}
🎮 Game: {product['game']}
👤 Nama: {data.get('customer_name') or '-'}
📱 WA: {customer_phone}
🎮 User ID: {data.get('customer_id')}
💎 Produk: {product['name']}
💰 Harga: Rp {harga_bayar:,}
📌 Metode: {metode.upper()}

📞 Nomor DANA: {DANA_NUMBER}
        """
        kirim_ke_telegram(pesan_telegram)

        if not hasattr(app, 'orders'):
            app.orders = []
        app.orders.append({
            'order_id': order_id,
            'customer_name': data.get('customer_name'),
            'customer_phone': customer_phone,
            'customer_id': data.get('customer_id'),
            'product_name': product['name'],
            'product_code': data.get('product_code'),
            'sku': product.get('sku'),
            'price': harga_bayar,
            'original_price': harga_dasar,
            'metode': metode,
            'voucher': voucher,
            'status': 'pending',
            'created_at': datetime.now().isoformat()
        })

        return jsonify({
            'success': True,
            'order_id': order_id,
            'product_name': product['name'],
            'price': harga_bayar,
            'dana_number': DANA_NUMBER,
            'customer_id': data.get('customer_id')
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/check-login', methods=['GET'])
def check_login():
    if 'logged_in' in session:
        return jsonify({'logged_in': True, 'username': session.get('username')})
    return jsonify({'logged_in': False})

@app.route('/login', methods=['GET', 'POST'])
def login_owner():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'juanshop123':
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error='Username atau password salah!')
    return render_template('login.html', error=None)

@app.route('/logout')
def logout_owner():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    orders = getattr(app, 'orders', [])
    return render_template('admin_dashboard.html', username=session.get('username'), orders=orders)

# ========== API ADMIN ==========
@app.route('/api/admin/get-orders', methods=['GET'])
@login_required
def get_orders():
    orders = getattr(app, 'orders', [])
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/admin/process-topup', methods=['POST'])
@login_required
def process_topup():
    data = request.json
    order_id = data.get('order_id')
    order = next((o for o in app.orders if o['order_id'] == order_id), None)
    if not order:
        return jsonify({'success': False, 'message': 'Order tidak ditemukan'}), 404
    if order['status'] != 'pending':
        return jsonify({'success': False, 'message': 'Order sudah diproses'}), 400

    result = topup_via_api(order['customer_id'], order['sku'], order['original_price'])
    if result['success']:
        order['status'] = 'completed'
        order['ref_id'] = result.get('ref_id')
        kirim_ke_telegram(f"✅ TOPUP BERHASIL!\n🆔 Order ID: {order_id}\n👤 User ID: {order['customer_id']}\n💎 Produk: {order['product_name']}")
        return jsonify({'success': True, 'message': f'Topup berhasil! Diamond sudah dikirim'})
    else:
        return jsonify({'success': False, 'message': result.get('message', 'Gagal topup')})

@app.route('/api/admin/delete-order', methods=['POST'])
@login_required
def delete_order():
    data = request.json
    order_id = data.get('order_id')
    app.orders = [o for o in app.orders if o['order_id'] != order_id]
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
