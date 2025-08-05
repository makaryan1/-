from flask import Flask, render_template, request, redirect, url_for, session, flash, get_flashed_messages
import json
import os
from datetime import datetime
import hashlib
import requests
import uuid

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

def process_card_payment(amount, payment_method, customer_info, bank_id=None):
    """Обработка платежа банковской картой"""
    try:
        # Находим выбранный банк
        selected_bank = None
        if bank_id:
            selected_bank = next((bank for bank in AVAILABLE_BANKS if bank['id'] == bank_id), None)

        if not selected_bank:
            selected_bank = AVAILABLE_BANKS[0]  # По умолчанию первый банк

        # Рассчитываем комиссию банка
        processing_fee = (amount * selected_bank['processing_fee']) / 100
        total_amount = amount + processing_fee

        payment_id = str(uuid.uuid4())

        # Симуляция API банка (в реальном проекте здесь будет настоящий API)
        import random

        # Разные банки имеют разную вероятность успеха для демонстрации
        success_rates = {
            'tbc_bank': 0.85,
            'bank_of_georgia': 0.90,
            'liberty_bank': 0.80,
            'procredit_bank': 0.75
        }

        success_rate = success_rates.get(selected_bank['id'], 0.80)
        success = random.random() < success_rate

        if success:
            return {
                'success': True,
                'payment_id': payment_id,
                'status': 'paid',
                'message': f'Платеж успешно обработан через {selected_bank["name"]}',
                'bank_name': selected_bank['name'],
                'processing_fee': processing_fee,
                'total_amount': total_amount
            }
        else:
            return {
                'success': False,
                'payment_id': payment_id,
                'status': 'failed',
                'message': f'Ошибка при обработке платежа через {selected_bank["name"]}. Попробуйте другой банк.',
                'bank_name': selected_bank['name']
            }
    except Exception as e:
        return {
            'success': False,
            'payment_id': None,
            'status': 'error',
            'message': f'Техническая ошибка: {str(e)}'
        }

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
    # Проверяем системных пользователей (админ/курьер)
    if 'user_role' in session and 'admin_username' in session:
        return {
            'id': session['admin_username'],
            'name': session['admin_username'],
            'email': session['admin_username'],
            'phone': '',
            'address': '',
            'is_local': True,
            'role': session['user_role']
        }

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
        'base_price': 25,
        'image': 'https://images.unsplash.com/photo-1518895949257-7621c3c786d7?w=300',
        'description': 'Красивые красные розы',
        'variants': [
            {'count': 5, 'name': 'Мини букет (5 роз)', 'price': 125},
            {'count': 11, 'name': 'Стандарт (11 роз)', 'price': 250},
            {'count': 21, 'name': 'Романтик (21 роза)', 'price': 475},
            {'count': 51, 'name': 'Люкс (51 роза)', 'price': 1100}
        ]
    },
    {
        'id': 2,
        'name': 'Тюльпаны микс',
        'base_price': 12,
        'image': 'https://images.unsplash.com/photo-1490750967868-88aa4486c946?w=300',
        'description': 'Разноцветные тюльпаны',
        'variants': [
            {'count': 9, 'name': 'Мини букет (9 тюльпанов)', 'price': 108},
            {'count': 15, 'name': 'Стандарт (15 тюльпанов)', 'price': 180},
            {'count': 25, 'name': 'Большой (25 тюльпанов)', 'price': 300}
        ]
    },
    {
        'id': 3,
        'name': 'Пионы белые',
        'base_price': 45,
        'image': 'https://images.unsplash.com/photo-1591886960571-74d43a9d4166?w=300',
        'description': 'Нежные белые пионы',
        'variants': [
            {'count': 3, 'name': 'Мини букет (3 пиона)', 'price': 135},
            {'count': 7, 'name': 'Стандарт (7 пионов)', 'price': 315},
            {'count': 15, 'name': 'Роскошный (15 пионов)', 'price': 675}
        ]
    },
    {
        'id': 4,
        'name': 'Герберы яркие',
        'base_price': 22,
        'image': 'https://images.unsplash.com/photo-1563241527-3004b7be0ffd?w=300',
        'description': 'Яркий букет гербер',
        'variants': [
            {'count': 7, 'name': 'Мини букет (7 гербер)', 'price': 154},
            {'count': 9, 'name': 'Стандарт (9 гербер)', 'price': 198},
            {'count': 15, 'name': 'Большой (15 гербер)', 'price': 330}
        ]
    },
    {
        'id': 5,
        'name': 'Лилии белые',
        'base_price': 56,
        'image': 'https://images.unsplash.com/photo-152531007254-f49212b5ac6d?w=300',
        'description': 'Элегантные белые лилии',
        'variants': [
            {'count': 3, 'name': 'Мини букет (3 лилии)', 'price': 168},
            {'count': 5, 'name': 'Стандарт (5 лилий)', 'price': 280},
            {'count': 9, 'name': 'Роскошный (9 лилий)', 'price': 504}
        ]
    },
    {
        'id': 6,
        'name': 'Подсолнухи',
        'base_price': 21,
        'image': 'https://images.unsplash.com/photo-1597848212624-e6d4b4d4ca7a?w=300',
        'description': 'Солнечные подсолнухи',
        'variants': [
            {'count': 5, 'name': 'Мини букет (5 подсолнухов)', 'price': 105},
            {'count': 7, 'name': 'Стандарт (7 подсолнухов)', 'price': 147},
            {'count': 11, 'name': 'Большой (11 подсолнухов)', 'price': 231}
        ]
    }
]

# Данные о подарках
GIFTS = [
    {
        'id': 101,
        'name': 'Коробка конфет',
        'image': 'https://images.unsplash.com/photo-1549007953-2f2dc0b24019?w=300',
        'description': 'Ассорти шоколадных конфет в красивой упаковке',
        'variants': [
            {'size': 'small', 'name': 'Маленькая коробка', 'price': 120},
            {'size': 'medium', 'name': 'Средняя коробка', 'price': 200},
            {'size': 'large', 'name': 'Большая коробка', 'price': 350}
        ]
    },
    {
        'id': 102,
        'name': 'Мягкая игрушка мишка',
        'image': 'https://images.unsplash.com/photo-1530103862676-de8c9debad1d?w=300',
        'description': 'Плюшевый мишка',
        'variants': [
            {'size': '20cm', 'name': 'Мишка 20 см', 'price': 150},
            {'size': '30cm', 'name': 'Мишка 30 см', 'price': 200},
            {'size': '50cm', 'name': 'Мишка 50 см', 'price': 400}
        ]
    },
    {
        'id': 103,
        'name': 'Свечи ароматические',
        'image': 'https://images.unsplash.com/photo-1602874801006-6ad3f7ce0e14?w=300',
        'description': 'Ароматические свечи',
        'variants': [
            {'count': 1, 'name': '1 свеча', 'price': 30},
            {'count': 3, 'name': 'Набор из 3 свечей', 'price': 80},
            {'count': 5, 'name': 'Набор из 5 свечей', 'price': 120}
        ]
    },
    {
        'id': 104,
        'name': 'Подарочная корзина',
        'image': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=300',
        'description': 'Корзина с деликатесами и сладостями',
        'variants': [
            {'size': 'small', 'name': 'Мини корзина', 'price': 250},
            {'size': 'medium', 'name': 'Стандартная корзина', 'price': 350},
            {'size': 'large', 'name': 'Большая корзина', 'price': 500}
        ]
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
    
    # Если это курьер, перенаправляем на панель курьера
    if user and user.get('role') == 'courier':
        return redirect(url_for('courier_panel'))
    
    return render_template('index.html', flowers=FLOWERS, gifts=GIFTS, user=user)

@app.route('/flower/<int:flower_id>')
def flower_detail(flower_id):
    user = get_user_info()
    
    # Курьеры не могут просматривать товары
    if user and user.get('role') == 'courier':
        return redirect(url_for('courier_panel'))
    
    flower = next((f for f in FLOWERS if f['id'] == flower_id), None)
    if not flower:
        flash('Товар не найден')
        return redirect(url_for('index'))
    return render_template('flower_detail.html', flower=flower, user=user)

@app.route('/gift/<int:gift_id>')
def gift_detail(gift_id):
    user = get_user_info()
    
    # Курьеры не могут просматривать товары
    if user and user.get('role') == 'courier':
        return redirect(url_for('courier_panel'))
    
    gift = next((g for g in GIFTS if g['id'] == gift_id), None)
    if not gift:
        flash('Товар не найден')
        return redirect(url_for('index'))
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
        # Используем первый вариант по умолчанию
        cart_key = f"{item_id}_0"
        if cart_key in session['cart']:
            session['cart'][cart_key] += 1
        else:
            session['cart'][cart_key] = 1
        session.modified = True
        flash(f'{item["name"]} добавлен в корзину!')

    return redirect(url_for('index'))

@app.route('/add_to_cart_variant', methods=['POST'])
def add_to_cart_variant():
    from flask import jsonify

    if 'cart' not in session:
        session['cart'] = {}

    data = request.get_json()
    item_id = data['item_id']
    variant_index = data['variant_index']
    quantity = data['quantity']
    item_type = data['item_type']

    # Ищем товар
    item = None
    if item_type == 'flower':
        item = next((f for f in FLOWERS if f['id'] == item_id), None)
    else:
        item = next((g for g in GIFTS if g['id'] == item_id), None)

    if item and variant_index < len(item['variants']):
        cart_key = f"{item_id}_{variant_index}"
        if cart_key in session['cart']:
            session['cart'][cart_key] += quantity
        else:
            session['cart'][cart_key] = quantity
        session.modified = True
        return jsonify({'success': True})

    return jsonify({'success': False})

@app.route('/cart')
def cart():
    user = get_user_info()
    
    # Курьеры не могут просматривать корзину
    if user and user.get('role') == 'courier':
        return redirect(url_for('courier_panel'))
    
    cart_items = []
    total = 0

    if 'cart' in session:
        for cart_key, quantity in session['cart'].items():
            if '_' in cart_key:
                item_id, variant_index = cart_key.split('_')
                item_id = int(item_id)
                variant_index = int(variant_index)
            else:
                # Старый формат - совместимость
                item_id = int(cart_key)
                variant_index = 0

            # Ищем среди цветов
            item = next((f for f in FLOWERS if f['id'] == item_id), None)
            item_type = 'flower'
            # Если не найден среди цветов, ищем среди подарков
            if not item:
                item = next((g for g in GIFTS if g['id'] == item_id), None)
                item_type = 'gift'

            if item and variant_index < len(item['variants']):
                variant = item['variants'][variant_index]
                item_total = variant['price'] * quantity
                cart_items.append({
                    'flower': item,  # Оставляем название для совместимости с шаблоном
                    'variant': variant,
                    'quantity': quantity,
                    'total': item_total,
                    'cart_key': cart_key,
                    'item_type': item_type
                })
                total += item_total

    return render_template('cart.html', cart_items=cart_items, total=total, user=user)

@app.route('/update_cart/<cart_key>/<int:quantity>')
def update_cart(cart_key, quantity):
    if 'cart' not in session:
        session['cart'] = {}

    if quantity <= 0:
        if cart_key in session['cart']:
            del session['cart'][cart_key]
            flash('Товар удален из корзины')
    else:
        session['cart'][cart_key] = quantity
        flash('Количество обновлено')

    session.modified = True
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<cart_key>')
def remove_from_cart(cart_key):
    if 'cart' in session and cart_key in session['cart']:
        del session['cart'][cart_key]
        session.modified = True
        flash('Товар удален из корзины')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user = get_user_info()
    
    # Курьеры не могут оформлять заказы
    if user and user.get('role') == 'courier':
        return redirect(url_for('courier_panel'))
    
    if 'cart' not in session or not session['cart']:
        flash('Корзина пуста')
        return redirect(url_for('index'))

    if request.method == 'POST':
        delivery_area = request.form['delivery_area']
        village = request.form.get('village', '')
        address = request.form['address']
        payment_method = request.form['payment_method']

        # Формируем полный адрес
        full_address = address
        if delivery_area == 'village' and village:
            full_address = f"{village}, {address}"
        elif delivery_area in DELIVERY_AREAS:
            full_address = f"{DELIVERY_AREAS[delivery_area]['name']}, {address}"

        delivery_price = get_delivery_price(delivery_area, village)

        cart_total = 0
        for cart_key, qty in session['cart'].items():
            if '_' in cart_key:
                item_id, variant_index = cart_key.split('_')
                item_id = int(item_id)
                variant_index = int(variant_index)
            else:
                item_id = int(cart_key)
                variant_index = 0

            # Ищем среди цветов
            item = next((f for f in FLOWERS if f['id'] == item_id), None)
            # Если не найден среди цветов, ищем среди подарков
            if not item:
                item = next((g for g in GIFTS if g['id'] == item_id), None)

            if item and variant_index < len(item['variants']):
                variant = item['variants'][variant_index]
                cart_total += variant['price'] * qty

        # Обработка платежа
        payment_status = 'pending'
        payment_id = None
        payment_message = 'Ожидает оплаты'
        selected_bank = request.form.get('selected_bank')

        if payment_method == 'card':
            # Автоматическая обработка платежа картой
            payment_result = process_card_payment(
                cart_total + delivery_price,
                payment_method,
                {
                    'name': request.form['name'],
                    'phone': request.form['phone'],
                    'email': request.form['email']
                },
                selected_bank
            )

            if payment_result['success']:
                payment_status = 'paid'
                payment_message = 'Оплачено картой'
                payment_id = payment_result['payment_id']
            else:
                payment_status = 'failed'
                payment_message = payment_result['message']
                flash(f'Ошибка оплаты: {payment_result["message"]}')
                return render_template('checkout.html', 
                                     cart_items=cart_items, 
                                     cart_total=cart_total, 
                                     user=user,
                                     delivery_areas=DELIVERY_AREAS,
                                     villages=VILLAGES,
                                     payment_error=payment_result['message'])
        else:
            payment_status = 'cash_on_delivery'
            payment_message = 'Оплата наличными курьеру'

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
            'payment_method': payment_method,
            'payment_status': payment_status,
            'payment_id': payment_id,
            'payment_message': payment_message,
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

    for cart_key, quantity in session['cart'].items():
        if '_' in cart_key:
            item_id, variant_index = cart_key.split('_')
            item_id = int(item_id)
            variant_index = int(variant_index)
        else:
            item_id = int(cart_key)
            variant_index = 0

        # Ищем среди цветов
        item = next((f for f in FLOWERS if f['id'] == item_id), None)
        # Если не найден среди цветов, ищем среди подарков
        if not item:
            item = next((g for g in GIFTS if g['id'] == item_id), None)

        if item and variant_index < len(item['variants']):
            variant = item['variants'][variant_index]
            item_total = variant['price'] * quantity
            cart_items.append({
                'flower': item,  # Оставляем название для совместимости с шаблоном
                'variant': variant,
                'quantity': quantity,
                'total': item_total
            })
            cart_total += item_total

    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         cart_total=cart_total, 
                         user=user,
                         delivery_areas=DELIVERY_AREAS,
                         villages=VILLAGES,
                         available_banks=AVAILABLE_BANKS)

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

        # Проверяем системных пользователей (админ/курьер)
        if email in USER_ROLES and USER_ROLES[email]['password'] == password:
            user_role = USER_ROLES[email]['role']
            session['user_role'] = user_role
            session['admin_username'] = email

            if user_role == 'admin':
                flash(f'Добро пожаловать, {email}!')
                return redirect(url_for('admin_panel'))
            elif user_role == 'courier':
                flash(f'Добро пожаловать, курьер {email}!')
                return redirect(url_for('courier_panel'))

        users = load_users()

        # Поиск обычного пользователя по email
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
    session.pop('user_role', None)
    session.pop('admin_username', None)
    session.pop('courier_username', None)
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

# Роли пользователей
USER_ROLES = {
    "admin@flowershop.com": {"password": "admin123", "role": "admin"},
    "courier@flowershop.com": {"password": "courier123", "role": "courier"},
    "manager@flowershop.com": {"password": "manager456", "role": "admin"}
}

# Доступные банки для оплаты
AVAILABLE_BANKS = [
    {
        'id': 'tbc_bank',
        'name': 'TBC Bank',
        'logo': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=100&h=50&fit=crop',
        'processing_fee': 2.5  # процент комиссии
    },
    {
        'id': 'bank_of_georgia',
        'name': 'Bank of Georgia',
        'logo': 'https://images.unsplash.com/photo-1541354329998-f4d9a9f9297f?w=100&h=50&fit=crop',
        'processing_fee': 2.0
    },
    {
        'id': 'liberty_bank',
        'name': 'Liberty Bank',
        'logo': 'https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=100&h=50&fit=crop',
        'processing_fee': 2.2
    },
    {
        'id': 'procredit_bank',
        'name': 'ProCredit Bank',
        'logo': 'https://images.unsplash.com/photo-1559526324-593bc0f36f38?w=100&h=50&fit=crop',
        'processing_fee': 2.8
    }
]

def get_user_role():
    """Получить роль текущего пользователя"""
    return session.get('user_role', None)

def is_admin():
    """Проверка админских прав"""
    return session.get('user_role') == 'admin'

def is_courier():
    """Проверка прав курьера"""
    return session.get('user_role') == 'courier'

def save_flowers():
    """Сохранить данные о цветах в файл"""
    with open('flowers.json', 'w', encoding='utf-8') as f:
        json.dump(FLOWERS, f, ensure_ascii=False, indent=2)

def save_gifts():
    """Сохранить данные о подарках в файл"""
    with open('gifts.json', 'w', encoding='utf-8') as f:
        json.dump(GIFTS, f, ensure_ascii=False, indent=2)

def load_flowers():
    """Загрузить данные о цветах из файла"""
    global FLOWERS
    if os.path.exists('flowers.json'):
        with open('flowers.json', 'r', encoding='utf-8') as f:
            FLOWERS = json.load(f)

def load_gifts():
    """Загрузить данные о подарках из файла"""
    global GIFTS
    if os.path.exists('gifts.json'):
        with open('gifts.json', 'r', encoding='utf-8') as f:
            GIFTS = json.load(f)

# Загружаем данные при запуске
load_flowers()
load_gifts()

def get_admin_stats():
    """Получить статистику для админ панели"""
    orders = load_orders()
    users = load_users()

    total_orders = len(orders)
    total_revenue = sum(order.get('total', 0) for order in orders)
    total_users = len(users)
    total_products = len(FLOWERS) + len(GIFTS)

    return {
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_products': total_products
    }

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USER_ROLES and USER_ROLES[username]['password'] == password:
            user_role = USER_ROLES[username]['role']
            session['user_role'] = user_role
            session['admin_username'] = username

            if user_role == 'admin':
                flash(f'Добро пожаловать в админ панель, {username}!')
                return redirect(url_for('admin_panel'))
            elif user_role == 'courier':
                flash(f'Добро пожаловать в панель курьера, {username}!')
                return redirect(url_for('courier_panel'))
        else:
            flash('Неверный логин или пароль')

    return render_template('admin_login.html')

@app.route('/courier_login', methods=['GET', 'POST'])
def courier_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in USER_ROLES and USER_ROLES[username]['password'] == password:
            user_role = USER_ROLES[username]['role']
            if user_role == 'courier':
                session['user_role'] = user_role
                session['courier_username'] = username
                flash(f'Добро пожаловать, курьер {username}!')
                return redirect(url_for('courier_panel'))
            else:
                flash('У вас нет прав курьера')
        else:
            flash('Неверный логин или пароль')

    return render_template('courier_login.html')

@app.route('/admin')
def admin_panel():
    if not is_admin():
        return redirect(url_for('admin_login'))

    stats = get_admin_stats()
    orders = load_orders()
    users = load_users()

    return render_template('admin.html', 
                         stats=stats, 
                         orders=orders, 
                         flowers=FLOWERS, 
                         gifts=GIFTS, 
                         users=users)

@app.route('/courier_panel')
def courier_panel():
    if not is_courier() and not is_admin():
        return redirect(url_for('courier_login'))

    orders = load_orders()
    # Показываем заказы для доставки
    active_orders = [o for o in orders if o['status'] in ['Готов к доставке', 'В пути', 'Новый']]

    return render_template('courier_panel.html', orders=active_orders)

@app.route('/admin/update_order_status', methods=['POST'])
def admin_update_order_status():
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()
    order_id = data['order_id']
    new_status = data['status']

    orders = load_orders()
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            break

    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return {'success': True}

@app.route('/admin/delete_order', methods=['POST'])
def admin_delete_order():
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()
    order_id = data['order_id']

    orders = load_orders()
    orders = [order for order in orders if order['id'] != order_id]

    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return {'success': True}

@app.route('/admin/add_flower', methods=['POST'])
def admin_add_flower():
    from flask import jsonify

    if not is_admin():
        return jsonify({'success': False, 'error': 'Access denied'})

    data = request.get_json()

    # Найти максимальный ID и добавить 1
    max_id = max([f['id'] for f in FLOWERS]) if FLOWERS else 0
    new_flower = {
        'id': max_id + 1,
        'name': data['name'],
        'base_price': data['base_price'],
        'image': data['image'],
        'description': data['description'],
        'variants': [
            {'count': 5, 'name': f'Мини букет (5 {data["name"].lower()})', 'price': data['base_price'] * 5},
            {'count': 11, 'name': f'Стандарт (11 {data["name"].lower()})', 'price': data['base_price'] * 10},
            {'count': 21, 'name': f'Большой (21 {data["name"].lower()})', 'price': data['base_price'] * 19}
        ]
    }

    FLOWERS.append(new_flower)
    save_flowers()

    return jsonify({'success': True})


@app.route('/admin/delete_flower', methods=['POST'])
def admin_delete_flower():
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()
    flower_id = data['flower_id']

    global FLOWERS
    FLOWERS = [f for f in FLOWERS if f['id'] != flower_id]
    save_flowers()

    return {'success': True}

@app.route('/admin/add_gift', methods=['POST'])
def admin_add_gift():
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()

    # Найти максимальный ID и добавить 1
    max_id = max([g['id'] for g in GIFTS]) if GIFTS else 100
    new_gift = {
        'id': max_id + 1,
        'name': data['name'],
        'image': data['image'],
        'description': data['description'],
        'variants': [
            {'size': 'small', 'name': f'Маленький {data["name"].lower()}', 'price': 100},
            {'size': 'medium', 'name': f'Средний {data["name"].lower()}', 'price': 200},
            {'size': 'large', 'name': f'Большой {data["name"].lower()}', 'price': 350}
        ]
    }

    GIFTS.append(new_gift)
    save_gifts()

    return {'success': True}

@app.route('/admin/delete_gift', methods=['POST'])
def admin_delete_gift():
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()
    gift_id = data['gift_id']

    global GIFTS
    GIFTS = [g for g in GIFTS if g['id'] != gift_id]
    save_gifts()

    return {'success': True}

@app.route('/retry_payment/<int:order_id>', methods=['POST'])
def retry_payment(order_id):
    """Повторная попытка оплаты"""
    orders = load_orders()
    order = next((o for o in orders if o['id'] == order_id), None)

    if not order:
        return {'success': False, 'message': 'Заказ не найден'}

    if order['payment_method'] != 'card':
        return {'success': False, 'message': 'Повтор доступен только для картных платежей'}

    # Повторная обработка платежа
    payment_result = process_card_payment(
        order['total'],
        order['payment_method'],
        {
            'name': order['name'],
            'phone': order['phone'],
            'email': order['email']
        }
    )

    # Обновляем статус заказа
    for i, o in enumerate(orders):
        if o['id'] == order_id:
            if payment_result['success']:
                orders[i]['payment_status'] = 'paid'
                orders[i]['payment_message'] = 'Оплачено картой'
                orders[i]['payment_id'] = payment_result['payment_id']
            else:
                orders[i]['payment_status'] = 'failed'
                orders[i]['payment_message'] = payment_result['message']
            break

    # Сохраняем обновленные заказы
    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return payment_result

@app.route('/admin/order_details/<int:order_id>')
def admin_order_details(order_id):
    """Получить детали заказа для админа"""
    if not is_admin():
        return {'success': False, 'error': 'Access denied'}
    
    orders = load_orders()
    order = next((o for o in orders if o['id'] == order_id), None)
    
    if not order:
        return {'success': False, 'message': 'Заказ не найден'}
    
    # Получаем детали товаров
    items_details = []
    for cart_key, quantity in order['items'].items():
        if '_' in cart_key:
            item_id, variant_index = cart_key.split('_')
            item_id = int(item_id)
            variant_index = int(variant_index)
        else:
            item_id = int(cart_key)
            variant_index = 0

        # Ищем среди цветов
        item = next((f for f in FLOWERS if f['id'] == item_id), None)
        item_type = 'flower'
        # Если не найден среди цветов, ищем среди подарков
        if not item:
            item = next((g for g in GIFTS if g['id'] == item_id), None)
            item_type = 'gift'

        if item and variant_index < len(item['variants']):
            variant = item['variants'][variant_index]
            items_details.append({
                'name': item['name'],
                'variant_name': variant['name'],
                'price': variant['price'],
                'quantity': quantity,
                'total': variant['price'] * quantity,
                'type': item_type
            })
    
    # Формируем HTML для деталей
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <h6>Информация о клиенте</h6>
            <p><strong>Имя:</strong> {order['name']}</p>
            <p><strong>Телефон:</strong> {order['phone']}</p>
            <p><strong>Email:</strong> {order['email']}</p>
            <p><strong>Адрес:</strong> {order['address']}</p>
        </div>
        <div class="col-md-6">
            <h6>Информация о заказе</h6>
            <p><strong>Дата:</strong> {order['date']}</p>
            <p><strong>Статус:</strong> {order['status']}</p>
            <p><strong>Способ оплаты:</strong> {'Картой' if order['payment_method'] == 'card' else 'Наличными курьеру'}</p>
            <p><strong>Статус оплаты:</strong> {order.get('payment_message', 'Не указано')}</p>
        </div>
    </div>
    <hr>
    <h6>Товары в заказе</h6>
    <div class="table-responsive">
        <table class="table table-sm">
            <thead>
                <tr>
                    <th>Товар</th>
                    <th>Вариант</th>
                    <th>Цена</th>
                    <th>Кол-во</th>
                    <th>Сумма</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in items_details:
        html += f"""
                <tr>
                    <td>{item['name']}</td>
                    <td>{item['variant_name']}</td>
                    <td>{item['price']}₾</td>
                    <td>{item['quantity']}</td>
                    <td><strong>{item['total']}₾</strong></td>
                </tr>
        """
    
    html += f"""
            </tbody>
        </table>
    </div>
    <hr>
    <div class="row">
        <div class="col-md-6">
            <p><strong>Стоимость товаров:</strong> {order['cart_total']}₾</p>
            <p><strong>Доставка:</strong> {order['delivery_price']}₾</p>
        </div>
        <div class="col-md-6">
            <h5><strong>Итого: {order['total']}₾</strong></h5>
        </div>
    </div>
    """
    
    return {'success': True, 'html': html}

@app.route('/courier')
def courier_app():
    """Публичный интерфейс для курьеров"""
    return render_template('courier_public.html')

@app.route('/courier/update_status', methods=['POST'])
def courier_update_status():
    """Обновление статуса заказа курьером"""
    if not is_courier() and not is_admin():
        return {'success': False, 'error': 'Access denied'}

    data = request.get_json()
    order_id = data['order_id']
    new_status = data['status']

    orders = load_orders()
    for order in orders:
        if order['id'] == order_id:
            order['status'] = new_status
            if new_status == 'Доставлен':
                order['delivery_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break

    with open('orders.json', 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

    return {'success': True}

@app.route('/admin/logout')
def admin_logout():
    session.pop('user_role', None)
    session.pop('admin_username', None)
    flash('Вы вышли из админ панели')
    return redirect(url_for('index'))

@app.route('/courier/logout')
def courier_logout():
    session.pop('user_role', None)
    session.pop('courier_username', None)
    flash('Вы вышли из панели курьера')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)