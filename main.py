
from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

def get_user_info():
    """Get user info from Replit Auth headers"""
    user_id = request.headers.get('X-Replit-User-Id')
    user_name = request.headers.get('X-Replit-User-Name') 
    return {'id': user_id, 'name': user_name} if user_id else None

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
    return render_template('index.html', flowers=FLOWERS, user=user)

@app.route('/flower/<int:flower_id>')
def flower_detail(flower_id):
    flower = next((f for f in FLOWERS if f['id'] == flower_id), None)
    if not flower:
        flash('Товар не найден')
        return redirect(url_for('index'))
    return render_template('flower_detail.html', flower=flower)

@app.route('/add_to_cart/<int:flower_id>')
def add_to_cart(flower_id):
    if 'cart' not in session:
        session['cart'] = {}
    
    flower = next((f for f in FLOWERS if f['id'] == flower_id), None)
    if flower:
        if str(flower_id) in session['cart']:
            session['cart'][str(flower_id)] += 1
        else:
            session['cart'][str(flower_id)] = 1
        session.modified = True
        flash(f'{flower["name"]} добавлен в корзину!')
    
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items = []
    total = 0
    user = get_user_info()
    
    if 'cart' in session:
        for flower_id, quantity in session['cart'].items():
            flower = next((f for f in FLOWERS if f['id'] == int(flower_id)), None)
            if flower:
                item_total = flower['price'] * quantity
                cart_items.append({
                    'flower': flower,
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
        order = {
            'id': len(load_orders()) + 1,
            'user_id': user['id'] if user else None,
            'user_name': user['name'] if user else None,
            'name': request.form['name'],
            'phone': request.form['phone'],
            'email': request.form['email'],
            'address': request.form['address'],
            'items': session['cart'],
            'total': sum(next((f['price'] for f in FLOWERS if f['id'] == int(fid)), 0) * qty 
                        for fid, qty in session['cart'].items()),
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'Новый'
        }
        
        save_order(order)
        session.pop('cart', None)
        flash('Заказ успешно оформлен! Мы свяжемся с вами в ближайшее время.')
        return redirect(url_for('order_success', order_id=order['id']))
    
    cart_items = []
    total = 0
    
    for flower_id, quantity in session['cart'].items():
        flower = next((f for f in FLOWERS if f['id'] == int(flower_id)), None)
        if flower:
            item_total = flower['price'] * quantity
            cart_items.append({
                'flower': flower,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('checkout.html', cart_items=cart_items, total=total, user=user)

@app.route('/order_success/<int:order_id>')
def order_success(order_id):
    return render_template('order_success.html', order_id=order_id)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
