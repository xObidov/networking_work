from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# Mahsulotlar ma'lumotlari
products = [
    {"id": 1, "name": "Erkaklar Klassik Kostyum", "category": "Erkaklar", "price": 450000, "image": "suit.jpg", "description": "Yuqori sifatli jun material, zamonaviy kesim"},
    {"id": 2, "name": "Ayollar Yozgi Ko'ylak", "category": "Ayollar", "price": 180000, "image": "dress.jpg", "description": "Yengil ip material, rangli naqshlar"},
    {"id": 3, "name": "Erkaklar Polo Futbolka", "category": "Erkaklar", "price": 95000, "image": "polo.jpg", "description": "100% paxta, nafas oladigan material"},
    {"id": 4, "name": "Ayollar Biznes Blazer", "category": "Ayollar", "price": 320000, "image": "blazer.jpg", "description": "Ofis va rasmiy uchrashuvlar uchun"},
    {"id": 5, "name": "Unisex Denim Jaket", "category": "Unisex", "price": 275000, "image": "jacket.jpg", "description": "Klassik ko'k denim, barcha yoshlar uchun"},
    {"id": 6, "name": "Erkaklar Chino Shim", "category": "Erkaklar", "price": 145000, "image": "chino.jpg", "description": "Stretch material, qulay kesim"},
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products_page():
    category = request.args.get('category', 'all')
    if category == 'all':
        filtered = products
    else:
        filtered = [p for p in products if p['category'] == category]
    return render_template('products.html', products=filtered, active_category=category)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        # Real loyihada bu yerda email yuboriladi yoki DB ga saqlanadi
        return jsonify({
            'success': True,
            'message': f"Rahmat, {name}! Xabaringiz qabul qilindi. Tez orada javob beramiz."
        })
    return render_template('contact.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
