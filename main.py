
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Данные о доставке
DELIVERY_AREAS = {
    'akhaltsikhe': {
        'name': 'Ахалцихе',
        'price': 5,
        'type': 'city'
    },
    'aspindza': {
        'name': 'Аспиндза',
        'price': 20,
        'type': 'city'
    }
}

VILLAGES = [
    'Abatkhevi (აბათხევი)', 'Agara (აგარა)', 'Anda (ანდა)', 'Andriatsminda (ანდრიაწმინდა)',
    'Ani (ანი)', 'Atsquri (აჭურა)', 'Boga (ბოგა)', 'Chacharaki (ჭაჭარაქი)',
    'Chvinta (ჭვინთა)', 'Didi Pamaji (დიდი პამაჯი)', 'Eliatsminda (ელიაწმინდა)', 'Ghreli (ღრელი)',
    'Giorgitsminda (გიორგიწმინდა)', 'Gurkeli (გურკელი)', 'Ivlita (ივლიტა)', 'Julgha (ჯულღა)',
    'Khaki (ხაკი)', 'Kheoti (ხეოთი)', 'Klde (კლდე)', 'Mikeltsminda (მიქელწმინდა)',
    'Minadze (მინაძე)', 'Mugareti (მუგარეთი)', 'Muskhi (მუსხი)', 'Naokhrebi (ნაოხრები)',
    'Orali (ორალი)', 'Patara Pamaji (პატარა პამაჯი)', 'Persa (ფერსა)', 'Qulalisi (ყულალისი)',
    'Sadzeli (საძელი)', 'Saquneti (საყუნეთი)', 'Shurdo (შურდო)', 'Skhvilisi (სხვილისი)',
    'Sviri (სვირი)', 'Tatanisi (ტატანისი)', 'Tiseli (თისელი)', 'Tqemlana (ტყემლანა)',
    'Tsinubani (წინუბანი)', 'Tsira (წირა)', 'Tsnisi (წნისი)', 'Tsqaltbila (წყალთბილა)',
    'Tsqordza (წყორძა)', 'Tsqruti (წყრუთი)', 'Uraveli (ურაველი)', 'Zemo Skhvilisi (ზემო სხვილისი)',
    'Zikilia (ზიკილია)'
]

def get_delivery_price(delivery_area, village=None):
    """Получить стоимость доставки"""
    if delivery_area in DELIVERY_AREAS:
        return DELIVERY_AREAS[delivery_area]['price']
    elif delivery_area == 'village' and village:
        return 10  # Цена для деревень
    return 0

def load_users():
    if os.path.exists('users.json'):
        with open('users.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open('users.json', 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def get_user_info():
    """Get user info from session or Replit Auth headers"""
    # Проверяем сначала сессию (локальная регистрация)
    if 'user_id' in session:
        users = load_users()
        user_id = session['user_id']
        if user_id in users:
            return {
                'id': user_id,
                'name': users[user_id]['name'],
                'email': users[user_id]['email'],
                'phone': users[user_id].get('phone', ''),
                'address': users[user_id].get('address', ''),
                'is_local': True
            }
    
    # Если нет локального пользователя, проверяем Replit Auth
    user_id = request.headers.get('X-Replit-User-Id')
    user_name = request.headers.get('X-Replit-User-Name') 
    if user_id:
        return {
            'id': f'replit_{user_id}',
            'name': user_name,
            'email': '',
            'phone': '',
            'address': '',
            'is_local': False
        }
    
    return None

# Данные о цветах
FLOWERS = [
    {
        'id': 1,
        'name': 'Розы красные',
        'price': 250,
        'image': 'https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=300',
        'description': 'Букет из 11 красных роз'
    },
    {
        'id': 2,
        'name': 'Тюльпаны микс',
        'price': 180,
        'image': 'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=300',
        'description': 'Разноцветные тюльпаны, 15 штук'
    },
    {
        'id': 3,
        'name': 'Пионы белые',
        'price': 320,
        'image': 'https://images.unsplash.com/photo-1591886960571-74d43a9d4166?w=300',
        'description': 'Нежные белые пионы, 7 штук'
    },
    {
        'id': 4,
        'name': 'Герберы яркие',
        'price': 200,
        'image': 'https://images.unsplash.com/photo-1563241527-3004b7be0ffd?w=300',
        'description': 'Яркий букет гербер, 9 штук'
    },
    {
        'id': 5,
        'name': 'Лилии белые',
        'price': 280,
        'image': 'https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?w=300',
        'description': 'Элегантные белые лилии, 5 штук'
    },
    {
        'id': 6,
        'name': 'Подсолнухи',
        'price': 150,
        'image': 'https://images.unsplash.com/photo-1597848212624-e6d4b4d4ca7a?w=300',
        'description': 'Солнечные подсолнухи, 7 штук'
    }
]

# Данные о подарках
GIFTS = [
    {
        'id': 101,
        'name': 'Коробка конфет',
        'price': 120,
        'image': 'https://images.unsplash.com/photo-1549007953-2f2dc0b24019?w=300',
        'description': 'Ассорти шоколадных конфет в красивой упаковке'
    },
    {
        'id': 102,
        'name': 'Мягкая игрушка мишка',
        'price': 200,
        'image': 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=300',
        'description': 'Плюшевый мишка высотой 30 см'
    },
    {
        'id': 103,
        'name': 'Свечи ароматические',
        'price': 80,
        'image': 'https://images.unsplash.com/photo-1602874801006-6ad3f7ce0e14?w=300',
        'description': 'Набор из 3 ароматических свечей'
    },
    {
        'id': 104,
        'name': 'Подарочная корзина',
        'price': 350,
        'image': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=300',
        'description': 'Корзина с деликатесами и сладостями'
    }
]

def load_orders():
    if os.path.exists('orders.json'):
        with open('orders.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_order(order):
    orders = load_orders()
    orders.append(order)
    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

@app.route('/')
def index():
    user = get_user_info()
    return render_template('index.html', flowers=FLOWERS, gifts=GIFTS, user=user)

@app.route('/flower/<int:flower_id>')
def flower_detail(flower_id):
    flower = next((f for f in FLOWERS if f['id'] == flower_id), None)
    if not flower:
        flash('Товар не найден')
        return redirect(url_for('index'))
    user = get_user_info()
    return render_template('flower_detail.html', flower=flower, user=user)

@app.route('/gift/<int:gift_id>')
def gift_detail(gift_id):
    gift = next((g for g in GIFTS if g['id'] == gift_id), None)
    if not gift:
        flash('Товар не найден')
        return redirect(url_for('index'))
    user = get_user_info()
    return render_template('gift_detail.html', gift=gift, user=user)

@app.route('/add_to_cart/<int:item_id>')
def add_to_cart(item_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    # Ищем среди цветов
    item = next((f for f in FLOWERS if f['id'] == item_id), None)
    # Если не найден среди цветов, ищем среди подарков
    if not item:
        item = next((g for g in GIFTS if g['id'] == item_id), None)
    
    if item:
        if str(item_id) in session['cart']:
            session['cart'][str(item_id)] += 1
        else:
            session['cart'][str(item_id)] = 1
        session.modified = True
        flash(f'{item["name"]} добавлен в корзину!')
    
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    user = get_user_info()
    
    if 'cart' in session:
        for item_id, quantity in session['cart'].items():
            # Ищем среди цветов
            item = next((f for f in FLOWERS if f['id'] == int(item_id)), None)
            # Если не найден среди цветов, ищем среди подарков
            if not item:
                item = next((g for g in GIFTS if g['id'] == int(item_id)), None)
            
            if item:
                item_total = item['price'] * quantity
                cart_items.append({
                    'flower': item,  # Оставляем название для совместимости с шаблоном
                    'quantity': quantity,
                    'total': item_total
                })
                total += item_total
    
    return render_template('cart.html', cart_items=cart_items, total=total, user=user)

@app.route('/update_cart/<int:flower_id>/<int:quantity>')
def update_cart(flower_id, quantity):
    if 'cart' not in session:
        session['cart'] = {}
    
    if quantity <= 0:
        if str(flower_id) in session['cart']:
            del session['cart'][str(flower_id)]
            flash('Товар удален из корзины')
    else:
        session['cart'][str(flower_id)] = quantity
        flash('Количество обновлено')
    
    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:flower_id>')
def remove_from_cart(flower_id):
    if 'cart' in session and str(flower_id) in session['cart']:
        del session['cart'][str(flower_id)]
        session.modified = True
        flash('Товар удален из корзины')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Корзина пуста')
        return redirect(url_for('index'))
    
    user = get_user_info()
    
    if request.method == 'POST':
        delivery_area = request.form['delivery_area']
        village = request.form.get('village', '')
        address = request.form['address']
        
        # Формируем полный адрес
        full_address = address
        if delivery_area == 'village' and village:
            full_address = f"{village}, {address}"
        elif delivery_area in DELIVERY_AREAS:
            full_address = f"{DELIVERY_AREAS[delivery_area]['name']}, {address}"
        
        delivery_price = get_delivery_price(delivery_area, village)
        
        cart_total = 0
        for fid, qty in session['cart'].items():
            # Ищем среди цветов
            item = next((f for f in FLOWERS if f['id'] == int(fid)), None)
            # Если не найден среди цветов, ищем среди подарков
            if not item:
                item = next((g for g in GIFTS if g['id'] == int(fid)), None)
            
            if item:
                cart_total += item['price'] * qty
        
        order = {
            'id': len(load_orders()) + 1,
            'user_id': user['id'] if user else None,
            'user_name': user['name'] if user else None,
            'name': request.form['name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': full_address,
            'delivery_area': delivery_area,
            'village': village,
            'items': session['cart'],
            'cart_total': cart_total,
            'delivery_price': delivery_price,
            'total': cart_total + delivery_price,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Новый'
        }
        
        save_order(order)
        session.pop('cart', None)
        flash('Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.')
        return redirect(url_for('order_success', order_id=order['id']))
    
    cart_items = []
    cart_total = 0
    
    for item_id, quantity in session['cart'].items():
        # Ищем среди цветов
        item = next((f for f in FLOWERS if f['id'] == int(item_id)), None)
        # Если не найден среди цветов, ищем среди подарков
        if not item:
            item = next((g for g in GIFTS if g['id'] == int(item_id)), None)
        
        if item:
            item_total = item['price'] * quantity
            cart_items.append({
                'flower': item,  # Оставляем название для совместимости с шаблоном
                'quantity': quantity,
                'total': item_total
            })
            cart_total += item_total
    
    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         cart_total=cart_total, 
                         user=user,
                         delivery_areas=DELIVERY_AREAS,
                         villages=VILLAGES)

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    user = get_user_info()
    return render_template('order_success.html', order_id=order_id, user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        
        # Проверка данных
        if not all([name, email, password]):
            flash('Пожалуйста, заполните все обязательные поля')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Пароли не совпадают')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов')
            return render_template('register.html')
        
        users = load_users()
        
        # Проверка на существующий email
        for user_data in users.values():
            if user_data['email'] == email:
                flash('Пользователь с таким email уже существует')
                return render_template('register.html')
        
        # Создание нового пользователя
        user_id = str(len(users) + 1)
        users[user_id] = {
            'name': name,
            'email': email,
            'password': hash_password(password),
            'phone': phone,
            'address': address,
            'registration_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        save_users(users)
        session['user_id'] = user_id
        flash('Регистрация прошла успешно!')
        return redirect(url_for('index'))
    
    user = get_user_info()
    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not all([email, password]):
            flash('Пожалуйста, заполните все поля')
            return render_template('login.html')
        
        users = load_users()
        
        # Поиск пользователя по email
        for user_id, user_data in users.items():
            if user_data['email'] == email and user_data['password'] == hash_password(password):
                session['user_id'] = user_id
                flash(f'Добро пожаловать, {user_data["name"]}!')
                return redirect(url_for('index'))
        
        flash('Неверный email или пароль')
        user = get_user_info()
        return render_template('login.html', user=user)
    
    user = get_user_info()
    return render_template('login.html', user=user)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Вы вышли из системы')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_user_info()
    if not user:
        flash('Необходимо войти в систему')
        return redirect(url_for('login'))
    
    if not user.get('is_local', False):
        flash('Профиль доступен только для зарегистрированных пользователей')
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        users = load_users()
        user_id = session['user_id']
        
        users[user_id]['name'] = request.form['name']
        users[user_id]['phone'] = request.form['phone']
        users[user_id]['address'] = request.form['address']
        
        # Изменение пароля (если указан)
        new_password = request.form.get('new_password')
        if new_password:
            if len(new_password) < 6:
                flash('Пароль должен содержать минимум 6 символов')
                return render_template('profile.html', user=user)
            users[user_id]['password'] = hash_password(new_password)
        
        save_users(users)
        flash('Профиль обновлен успешно!')
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/my_orders')
def my_orders():
    user = get_user_info()
    if not user:
        flash('Необходимо войти в систему')
        return redirect(url_for('login'))
    
    orders = load_orders()
    user_orders = []
    
    for order in orders:
        # Для локальных пользователей проверяем user_id
        if user.get('is_local') and order.get('user_id') == session.get('user_id'):
            user_orders.append(order)
        # Для Replit пользователей проверяем имя
        elif not user.get('is_local') and order.get('user_name') == user['name']:
            user_orders.append(order)
    
    # Добавляем детали товаров к заказам
    for order in user_orders:
        order['items_details'] = []
        for item_id, quantity in order['items'].items():
            # Ищем среди цветов
            item = next((f for f in FLOWERS if f['id'] == int(item_id)), None)
            # Если не найден среди цветов, ищем среди подарков
            if not item:
                item = next((g for g in GIFTS if g['id'] == int(item_id)), None)
            
            if item:
                order['items_details'].append({
                    'flower': item,  # Оставляем название для совместимости с шаблоном
                    'quantity': quantity,
                    'total': item['price'] * quantity
                })
    
    return render_template('my_orders.html', orders=user_orders, user=user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
