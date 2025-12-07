import os
import json
import re
import requests
import time
import traceback
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, User, Category, Recipe, Comment, Page, Image
from datetime import datetime
from urllib.parse import urljoin

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

# Database configuration - support both SQLite (dev) and PostgreSQL (production)
database_url = os.getenv('DATABASE_URL', 'sqlite:///nefisyemekler.db')
# Render uses postgres:// but SQLAlchemy needs postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def resolve_image_url(candidate_url):
    """Try to resolve a possibly-short or HTML page URL to a direct image URL.
    Returns a direct image URL (possibly after redirects) or None if not found.
    """
    if not candidate_url:
        return None
    try:
        # Follow redirects and prefer HEAD for speed
        resp = requests.head(candidate_url, allow_redirects=True, timeout=5)
        ctype = resp.headers.get('Content-Type', '')
        if ctype.startswith('image'):
            return resp.url

        # If HEAD didn't return an image, GET the page and try to extract an image
        resp = requests.get(candidate_url, allow_redirects=True, timeout=6)
        ctype = resp.headers.get('Content-Type', '')
        if ctype.startswith('image'):
            return resp.url

        html = resp.text or ''
        # Try common meta tags
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if not m:
            m = re.search(r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if m:
            img_url = m.group(1)
            return urljoin(resp.url, img_url)

        # Fallback: first <img> tag
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
        if m:
            img_url = m.group(1)
            return urljoin(resp.url, img_url)

    except Exception:
        # Don't crash on network errors; caller can fallback to original URL
        return None
    return None

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Lütfen giriş yapın.'

# Create tables on startup (for production)
with app.app_context():
    try:
        db.create_all()
        print('✓ Database tables created/verified')
        
        # Seed database with initial data
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print('✓ Admin user created (username: admin, password: admin123)')
        
        # Add categories if not exist
        categories_data = [
            {'name': 'Kahvaltı', 'slug': 'kahvalti', 'description': 'Güne enerjik başlamak için lezzetli kahvaltı tarifleri'},
            {'name': 'Ana Yemekler', 'slug': 'ana-yemekler', 'description': 'Doyurucu ve lezzetli ana yemek tarifleri'},
            {'name': 'Tatlılar', 'slug': 'tatlilar', 'description': 'Damak tadınıza uygun tatlı tarifleri'},
            {'name': 'Çorbalar', 'slug': 'corbalar', 'description': 'Sıcacık ve doyurucu çorba tarifleri'},
            {'name': 'Salatalar', 'slug': 'salatalar', 'description': 'Sağlıklı ve ferahlatıcı salata tarifleri'},
            {'name': 'Dünya Mutfağı', 'slug': 'dunya-mutfagi', 'description': 'Dünyanın farklı ülkelerinden lezzetli tarifler'},
        ]
        
        for cat_data in categories_data:
            existing = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                cat = Category(**cat_data)
                db.session.add(cat)
                print(f'✓ Category added: {cat_data["name"]}')
        
        db.session.commit()
        
        # Add sample recipes for each category (3 per category)
        sample_recipes = [
            # Kahvaltı
            {
                'title': 'Menemen',
                'content': 'Kahvaltının vazgeçilmez lezzeti menemen. Domates, biber ve yumurtayla hazırlanan bu enfes tarif sofranızı şenlendirecek.',
                'ingredients': '4 adet yumurta\n2 adet domates\n2 adet sivri biber\n1 yemek kaşığı tereyağı\nTuz, karabiber',
                'instructions': '1. Biberleri ve domatesleri küp küp doğrayın\n2. Tereyağını tavada eritin\n3. Biberleri ekleyip kavurun\n4. Domatesleri ekleyin ve suyunu çekene kadar pişirin\n5. Yumurtaları kırıp karıştırın\n6. Baharatları ekleyip servise hazır hale getirin',
                'category_slug': 'kahvalti',
                'prep_time': 10,
                'cook_time': 15,
                'servings': 2
            },
            {
                'title': 'Gözleme',
                'content': 'El açması hamuruyla yapılan geleneksel Türk böreği. Peynirli, patatesli veya kıymalı olarak hazırlayabilirsiniz.',
                'ingredients': '3 su bardağı un\n1 su bardağı ılık su\n1 çay kaşığı tuz\n200g beyaz peynir\nMaydanoz',
                'instructions': '1. Unu ve tuzu karıştırın\n2. Suyu ekleyip yoğurun\n3. Bezelyeleri hazırlayın\n4. Hamuru açıp iç malzemeyi yerleştirin\n5. Sacda veya tavada pişirin',
                'category_slug': 'kahvalti',
                'prep_time': 30,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'Simit',
                'content': 'Tahinli susam kaplı geleneksel Türk simidi. Evde kolayca yapabileceğiniz nefis bir tarif.',
                'ingredients': '500g un\n10g yaş maya\n1 su bardağı ılık süt\n1 yemek kaşığı şeker\n1 çay kaşığı tuz\nTahin\nSusam',
                'instructions': '1. Mayalı hamuru hazırlayın\n2. Dinlendirin\n3. Simit şekli verin\n4. Tahin ve susamla kaplayın\n5. Fırında pişirin',
                'category_slug': 'kahvalti',
                'prep_time': 45,
                'cook_time': 25,
                'servings': 6
            },
            # Ana Yemekler
            {
                'title': 'Karnıyarık',
                'content': 'Patlıcanın kıymayla buluştuğu muhteşem Türk yemeği. Fırında pişen bu lezzet sofranızın yıldızı olacak.',
                'ingredients': '6 adet patlıcan\n300g kıyma\n2 adet soğan\n3 adet domates\n2 adet sivri biber\nSalça, baharat',
                'instructions': '1. Patlıcanları kızartın\n2. İç harcı hazırlayın\n3. Patlıcanları yarmadan ortasını açın\n4. İç harcı doldurun\n5. Fırında pişirin',
                'category_slug': 'ana-yemekler',
                'prep_time': 30,
                'cook_time': 45,
                'servings': 6
            },
            {
                'title': 'Mantı',
                'content': 'Kayseri\'nin meşhur mantısı. El açması hamurdan yapılan mini börekler yoğurt ve tereyağı sosuyla servis edilir.',
                'ingredients': '500g un\n2 adet yumurta\n250g kıyma\nSoğan, tuz\nYoğurt\nTereyağı\nPul biber',
                'instructions': '1. Hamuru hazırlayın ve incecik açın\n2. Küçük kareler kesin\n3. İç harcı yerleştirin ve kapatın\n4. Haşlayın\n5. Yoğurt ve tereyağı sosuyla servis edin',
                'category_slug': 'ana-yemekler',
                'prep_time': 60,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'İskender Kebap',
                'content': 'Bursa\'nın dünyaca ünlü kebabı. Döner eti, pide, domates sosu ve tereyağıyla hazırlanan muhteşem lezzet.',
                'ingredients': '500g döner eti\n4 adet pide\n4 yemek kaşığı tereyağı\n2 su bardağı domates sosu\nYoğurt',
                'instructions': '1. Döner etini dilimleyin\n2. Pideleri kesin ve yerleştirin\n3. Üzerine döner ekleyin\n4. Domates sosu dökün\n5. Tereyağını eritip gezdirin\n6. Yoğurtla servis edin',
                'category_slug': 'ana-yemekler',
                'prep_time': 20,
                'cook_time': 30,
                'servings': 4
            },
            # Tatlılar
            {
                'title': 'Baklava',
                'content': 'Fıstıklı, cevizli veya fındıklı olarak hazırlayabileceğiniz geleneksel Türk tatlısı.',
                'ingredients': '1 paket baklavalık yufka\n300g tereyağı\n400g antep fıstığı\n2 su bardağı şeker\n2 su bardağı su',
                'instructions': '1. Yufkaları yağlayın ve dizin\n2. Fıstıkları serpin\n3. Dilimleyin\n4. Fırında pişirin\n5. Şerbeti dökün',
                'category_slug': 'tatlilar',
                'prep_time': 45,
                'cook_time': 50,
                'servings': 12
            },
            {
                'title': 'Sütlaç',
                'content': 'Fırında pişen geleneksel Türk sütlü tatlısı. Yumuşacık pirinç taneleriyle hazırlanan harika bir lezzet.',
                'ingredients': '1 litre süt\n1/2 su bardağı pirinç\n1 su bardağı şeker\n1 yemek kaşığı un\nVanilya',
                'instructions': '1. Pirinci haşlayın\n2. Sütü ekleyin\n3. Şeker ve unu ekleyin\n4. Kıvam alana kadar pişirin\n5. Fırında üzerini kızartın',
                'category_slug': 'tatlilar',
                'prep_time': 15,
                'cook_time': 60,
                'servings': 6
            },
            {
                'title': 'Kazandibi',
                'content': 'Tavuk göğsüyle yapılan geleneksel Osmanlı tatlısı. Alt tarafı karamelize edilmiş sütlü tatlı.',
                'ingredients': '1 litre süt\n150g tavuk göğsü\n1 su bardağı şeker\n2 yemek kaşığı un\nVanilya',
                'instructions': '1. Tavuk göğsünü haşlayıp didikleyin\n2. Sütü kaynatın\n3. Malzemeleri ekleyip pişirin\n4. Tepsiye döküp altını kızartın\n5. Rulo yapıp servis edin',
                'category_slug': 'tatlilar',
                'prep_time': 30,
                'cook_time': 45,
                'servings': 8
            },
            # Çorbalar
            {
                'title': 'Mercimek Çorbası',
                'content': 'Türk mutfağının vazgeçilmez çorbası. Kırmızı mercimek ve sebzelerle hazırlanan sağlıklı ve doyurucu tarif.',
                'ingredients': '1 su bardağı kırmızı mercimek\n1 adet soğan\n1 adet havuç\n1 yemek kaşığı salça\nTuz, karabiber\nLimon',
                'instructions': '1. Mercimeği yıkayın\n2. Sebzeleri doğrayın ve kavurun\n3. Mercimek ve suyu ekleyin\n4. Pişirin ve blenderdan geçirin\n5. Baharatları ekleyin',
                'category_slug': 'corbalar',
                'prep_time': 10,
                'cook_time': 30,
                'servings': 4
            },
            {
                'title': 'Ezogelin Çorbası',
                'content': 'Gaziantep\'in meşhur çorbası. Kırmızı mercimek, bulgur ve pirinçle hazırlanan nefis bir tarif.',
                'ingredients': '1 su bardağı kırmızı mercimek\n1/2 su bardağı bulgur\n1/4 su bardağı pirinç\n1 yemek kaşığı salça\nNane, kırmızı biber',
                'instructions': '1. Mercimek, bulgur ve pirinci kaynatın\n2. Salçayı kavurun\n3. Karıştırıp pişirin\n4. Baharat ekleyin\n5. Sıcak servis edin',
                'category_slug': 'corbalar',
                'prep_time': 10,
                'cook_time': 35,
                'servings': 6
            },
            {
                'title': 'Yayla Çorbası',
                'content': 'Yoğurtlu ve nane aromalı geleneksel Türk çorbası. Yaz aylarında ferahlatıcı, kış aylarında ısıtıcı.',
                'ingredients': '2 su bardağı yoğurt\n1/2 su bardağı pirinç\n1 yemek kaşığı un\nTuz\nNane, tereyağı',
                'instructions': '1. Pirinci haşlayın\n2. Yoğurt ve unu çırpın\n3. Pirinç suyuna ekleyin\n4. Pişirin\n5. Naneli tereyağıyla servis edin',
                'category_slug': 'corbalar',
                'prep_time': 10,
                'cook_time': 25,
                'servings': 4
            },
            # Salatalar
            {
                'title': 'Çoban Salatası',
                'content': 'Taze sebzelerle hazırlanan klasik Türk salatası. Yaz aylarının vazgeçilmez tariflerinden.',
                'ingredients': '4 adet domates\n2 adet salatalık\n2 adet sivri biber\n1 adet soğan\nMaydanoz\nZeytinyağı, limon, nar ekşisi',
                'instructions': '1. Tüm sebzeleri küp küp doğrayın\n2. Maydanozu ince kıyın\n3. Karıştırın\n4. Zeytinyağı, limon ve nar ekşisi ekleyin\n5. Servis edin',
                'category_slug': 'salatalar',
                'prep_time': 15,
                'cook_time': 0,
                'servings': 4
            },
            {
                'title': 'Kısır',
                'content': 'Bulgurla yapılan geleneksel Türk salatası. Nar ekşisi ve salça ile tatlandırılmış nefis bir tarif.',
                'ingredients': '2 su bardağı ince bulgur\n1 su bardağı sıcak su\n2 yemek kaşığı salça\nNar ekşisi\nMaydanoz, domates, soğan\nBaharat',
                'instructions': '1. Bulguru sıcak suyla ıslatın\n2. Salçayı ekleyin\n3. Sebzeleri doğrayın\n4. Tüm malzemeleri karıştırın\n5. Dinlendirip servis edin',
                'category_slug': 'salatalar',
                'prep_time': 30,
                'cook_time': 0,
                'servings': 6
            },
            {
                'title': 'Piyaz',
                'content': 'Fasulye salatası. Antalya\'nın meşhur salatası haşlanmış fasulye, tahin ve yumurtayla hazırlanır.',
                'ingredients': '2 su bardağı kuru fasulye\n2 adet yumurta\n2 yemek kaşığı tahin\nSoğan, maydanoz\nZeytinyağı, limon',
                'instructions': '1. Fasulyeyi haşlayın\n2. Yumurtaları haşlayın\n3. Soğanları doğrayın\n4. Tahin sosunu hazırlayın\n5. Karıştırıp servis edin',
                'category_slug': 'salatalar',
                'prep_time': 20,
                'cook_time': 60,
                'servings': 4
            },
            # Dünya Mutfağı
            {
                'title': 'Spaghetti Carbonara',
                'content': 'İtalyan mutfağının klasik makarna tarifi. Yumurta, pancetta ve parmesan peyniriyle hazırlanan kremalı lezzet.',
                'ingredients': '400g spagetti\n200g pancetta\n4 adet yumurta\n100g parmesan peyniri\nTuz, karabiber',
                'instructions': '1. Makarnayı haşlayın\n2. Pancettayı kızartın\n3. Yumurta ve peyniri çırpın\n4. Makarnayı karıştırın\n5. Hemen servis edin',
                'category_slug': 'dunya-mutfagi',
                'prep_time': 10,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'Pad Thai',
                'content': 'Tayland\'ın ünlü pirinç eriştesi. Karides, yer fıstığı ve tamarind sosuyla hazırlanan egzotik tarif.',
                'ingredients': '300g pirinç eriştesi\n200g karides\nYumurta\nYer fıstığı\nTamarind, balık sosu, limon',
                'instructions': '1. Erişteyyi ıslatın\n2. Karidesi pişirin\n3. Yumurtayı karıştırın\n4. Sosları ekleyin\n5. Yer fıstığıyla servis edin',
                'category_slug': 'dunya-mutfagi',
                'prep_time': 15,
                'cook_time': 15,
                'servings': 3
            },
            {
                'title': 'Tacos',
                'content': 'Meksika mutfağının vazgeçilmez yemeği. Tortilla ekmeğinde kıyma, sebze ve soslarla hazırlanan lezzetli tarif.',
                'ingredients': '500g kıyma\n8 adet tortilla\nMarul, domates\nAvokado\nSalsa sosu, krema',
                'instructions': '1. Kıymayı baharatlarla pişirin\n2. Tortillaları ısıtın\n3. Sebzeleri doğrayın\n4. Tortillaya malzemeleri yerleştirin\n5. Soslarla servis edin',
                'category_slug': 'dunya-mutfagi',
                'prep_time': 20,
                'cook_time': 15,
                'servings': 4
            },
        ]
        
        # Get admin user for recipe creation
        admin = User.query.filter_by(username='admin').first()
        if admin:
            # Check if we need to add sample recipes (if database is empty or missing recipes)
            existing_recipe_count = Recipe.query.count()
            print(f'Current recipe count: {existing_recipe_count}')
            
            if existing_recipe_count < len(sample_recipes):
                print('Adding sample recipes...')
                for recipe_data in sample_recipes:
                    # Get category by slug
                    category = Category.query.filter_by(slug=recipe_data['category_slug']).first()
                    if category:
                        # Check if recipe already exists
                        existing_recipe = Recipe.query.filter_by(
                            title=recipe_data['title'],
                            category_id=category.id
                        ).first()
                        
                        if not existing_recipe:
                            recipe = Recipe(
                                title=recipe_data['title'],
                                content=recipe_data['content'],
                                ingredients=recipe_data['ingredients'],
                                instructions=recipe_data['instructions'],
                                category_id=category.id,
                                user_id=admin.id,
                                prep_time=recipe_data.get('prep_time'),
                                cook_time=recipe_data.get('cook_time'),
                                servings=recipe_data.get('servings')
                            )
                            db.session.add(recipe)
                            print(f'✓ Recipe added: {recipe_data["title"]}')
                
                db.session.commit()
                print(f'✓ Sample recipes added! Total: {Recipe.query.count()}')
            else:
                print('✓ Sample recipes already exist')
        
        print('✓ Database initialization complete!')
        
    except Exception as e:
        print(f'✗ Database error: {e}')
        import traceback
        traceback.print_exc()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/favicon.ico')
def favicon():
    """Favicon route"""
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ============= PUBLIC ROUTES =============

@app.route('/')
def index():
    """Ana sayfa - En yeni tarifler"""
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).limit(12).all()
    categories = Category.query.all()
    return render_template('index.html', recipes=recipes, categories=categories)

@app.route('/category/<slug>')
def category(slug):
    """Kategori sayfası"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    recipes = Recipe.query.filter_by(category_id=category.id).order_by(Recipe.created_at.desc()).all()
    categories = Category.query.all()
    return render_template('category.html', category=category, recipes=recipes, categories=categories)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Tarif detay sayfası"""
    recipe = Recipe.query.get_or_404(recipe_id)
    comments = Comment.query.filter_by(recipe_id=recipe_id).order_by(Comment.created_at.desc()).all()
    related_recipes = Recipe.query.filter(
        Recipe.category_id == recipe.category_id,
        Recipe.id != recipe_id
    ).limit(4).all()
    return render_template('recipe_detail.html', recipe=recipe, comments=comments, related_recipes=related_recipes)

@app.route('/recipe/<int:recipe_id>/comment', methods=['POST'])
@login_required
def add_comment(recipe_id):
    """Yorum ekleme"""
    recipe = Recipe.query.get_or_404(recipe_id)
    body = request.form.get('body')
    rating = request.form.get('rating', type=int)
    
    if not body:
        flash('Yorum boş olamaz.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    comment = Comment(
        recipe_id=recipe_id,
        user_id=current_user.id,
        body=body,
        rating=rating
    )
    db.session.add(comment)
    db.session.commit()
    
    flash('Yorumunuz eklendi.', 'success')
    return redirect(url_for('recipe_detail', recipe_id=recipe_id))

@app.route('/about')
def about():
    """Hakkımızda sayfası"""
    page = Page.query.filter_by(slug='about').first()
    return render_template('about.html', page=page)

@app.route('/testimonials')
def testimonials():
    """Referanslar/Yorumlar sayfası"""
    comments = Comment.query.order_by(Comment.created_at.desc()).limit(20).all()
    return render_template('testimonials.html', comments=comments)

@app.route('/contact')
def contact():
    """İletişim sayfası"""
    return render_template('contact.html')

@app.route('/search')
def search():
    """Arama sayfası"""
    query = request.args.get('q', '').strip()
    recipes = []
    
    if query:
        # Tarif adı, içerik ve malzemelerde arama yap
        search_pattern = f"%{query}%"
        recipes = Recipe.query.filter(
            db.or_(
                Recipe.title.ilike(search_pattern),
                Recipe.content.ilike(search_pattern),
                Recipe.ingredients.ilike(search_pattern)
            )
        ).order_by(Recipe.created_at.desc()).all()
    
    categories = Category.query.all()
    return render_template('search.html', recipes=recipes, query=query, categories=categories)

# AI Recipe route - Deactivated for security reasons
# @app.route('/ai-recipe', methods=['GET', 'POST'])
# def ai_recipe():
#     """AI ile tarif önerisi - Google Gemini kullanarak"""
#     pass

@app.route('/calorie-calculator', methods=['GET', 'POST'])
def calorie_calculator():
    """Kalori hesaplayıcı"""
    result = None
    
    if request.method == 'POST':
        try:
            # Kullanıcı bilgilerini al
            gender = request.form.get('gender')
            age = int(request.form.get('age', 0))
            weight = float(request.form.get('weight', 0))
            height = float(request.form.get('height', 0))
            activity_level = request.form.get('activity_level')
            goal = request.form.get('goal')
            
            # BMR hesaplama (Mifflin-St Jeor formülü)
            if gender == 'male':
                bmr = 10 * weight + 6.25 * height - 5 * age + 5
            else:  # female
                bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
            # Aktivite seviyesine göre günlük kalori ihtiyacı
            activity_multipliers = {
                'sedentary': 1.2,      # Hareketsiz (egzersiz yok)
                'light': 1.375,        # Hafif aktif (haftada 1-3 gün)
                'moderate': 1.55,      # Orta aktif (haftada 3-5 gün)
                'very_active': 1.725,  # Çok aktif (haftada 6-7 gün)
                'extra_active': 1.9    # Ekstra aktif (günde 2 kez)
            }
            
            daily_calories = bmr * activity_multipliers.get(activity_level, 1.2)
            
            # Hedefe göre kalori ayarlama
            if goal == 'lose':
                target_calories = daily_calories - 500  # Kilo vermek için
                goal_text = 'Kilo Vermek'
            elif goal == 'gain':
                target_calories = daily_calories + 500  # Kilo almak için
                goal_text = 'Kilo Almak'
            else:  # maintain
                target_calories = daily_calories
                goal_text = 'Kilonu Korumak'
            
            # BMI hesaplama
            height_m = height / 100
            bmi = weight / (height_m ** 2)
            
            # BMI kategorisi
            if bmi < 18.5:
                bmi_category = 'Zayıf'
                bmi_class = 'warning'
            elif 18.5 <= bmi < 25:
                bmi_category = 'Normal'
                bmi_class = 'success'
            elif 25 <= bmi < 30:
                bmi_category = 'Fazla Kilolu'
                bmi_class = 'warning'
            else:
                bmi_category = 'Obez'
                bmi_class = 'danger'
            
            # Makro besin önerileri (protein, karbonhidrat, yağ)
            protein_grams = weight * 2  # Günlük protein (gram)
            protein_calories = protein_grams * 4
            fat_calories = target_calories * 0.25
            fat_grams = fat_calories / 9
            carb_calories = target_calories - protein_calories - fat_calories
            carb_grams = carb_calories / 4
            
            result = {
                'bmr': round(bmr),
                'daily_calories': round(daily_calories),
                'target_calories': round(target_calories),
                'goal_text': goal_text,
                'bmi': round(bmi, 1),
                'bmi_category': bmi_category,
                'bmi_class': bmi_class,
                'protein_grams': round(protein_grams),
                'carb_grams': round(carb_grams),
                'fat_grams': round(fat_grams),
                'gender': gender,
                'age': age,
                'weight': weight,
                'height': height,
                'activity_level': activity_level,
                'goal': goal
            }
            
            # AI ile yeme programı oluşturma devre dışı bırakıldı
            # if request.form.get('generate_meal_plan'):
            #     meal_plan = generate_weekly_meal_plan(result)
            #     if meal_plan:
            #         result['meal_plan'] = meal_plan
            
        except (ValueError, TypeError):
            flash('Lütfen tüm alanları doğru şekilde doldurun.', 'danger')
    
    return render_template('calorie_calculator.html', result=result)


# ============= AUTH ROUTES =============

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Kullanıcı kaydı"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if not username or not password:
            flash('Kullanıcı adı ve şifre gerekli.', 'danger')
            return redirect(url_for('register'))
        
        if password != password_confirm:
            flash('Şifreler eşleşmiyor.', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Bu kullanıcı adı zaten alınmış.', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kullanıcı girişi"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash('Giriş başarılı!', 'success')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Kullanıcı adı veya şifre hatalı.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Çıkış"""
    logout_user()
    flash('Çıkış yapıldı.', 'info')
    return redirect(url_for('index'))

# ============= USER ROUTES =============

@app.route('/my-recipes')
@login_required
def my_recipes():
    """Kullanıcının tarifleri"""
    recipes = Recipe.query.filter_by(user_id=current_user.id).order_by(Recipe.created_at.desc()).all()
    return render_template('my_recipes.html', recipes=recipes)

@app.route('/recipe/add', methods=['GET', 'POST'])
@login_required
def add_recipe():
    """Tarif ekleme"""
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        ingredients = request.form.get('ingredients')
        instructions = request.form.get('instructions')
        category_id = request.form.get('category_id', type=int)
        prep_time = request.form.get('prep_time', type=int)
        cook_time = request.form.get('cook_time', type=int)
        servings = request.form.get('servings', type=int)
        
        if not title or not content or not category_id:
            flash('Başlık, açıklama ve kategori gerekli.', 'danger')
            return redirect(url_for('add_recipe'))
        
        # Fotoğraf - URL veya dosya yükleme
        image_filename = None
        image_url = request.form.get('image_url', '').strip()
        
        if image_url:
            # URL girilmişse önce doğrudan resim olup olmadığını çözmeyi dene
            resolved = resolve_image_url(image_url)
            if resolved:
                image_filename = resolved
            else:
                # Eğer resolver bulamadıysa kullanıcının verdiği URL'i yine kaydet (kullanıcı manuel düzeltme yapabilir)
                image_filename = image_url
        elif 'image' in request.files:
            # Dosya yüklenmişse kaydet
            file = request.files['image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                image_filename = f"{timestamp}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        recipe = Recipe(
            title=title,
            content=content,
            ingredients=ingredients,
            instructions=instructions,
            category_id=category_id,
            user_id=current_user.id,
            image=image_filename,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings
        )
        db.session.add(recipe)
        db.session.commit()
        
        flash('Tarif eklendi!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe.id))
    
    categories = Category.query.all()
    return render_template('add_recipe.html', categories=categories)

@app.route('/recipe/<int:recipe_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recipe(recipe_id):
    """Tarif düzenleme"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id and not current_user.is_admin:
        flash('Bu tarifi düzenleme yetkiniz yok.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    if request.method == 'POST':
        # DEBUG: log incoming form/files to help diagnose remove_image issue
        try:
            print('\n--- DEBUG edit_recipe POST ---')
            print('form:', dict(request.form))
            print('files:', list(request.files.keys()))
            print('remove_image raw:', request.form.get('remove_image'))
        except Exception as e:
            print('DEBUG logging error:', e)
        # also show a short flash for quick UI feedback
        flash(f"DEBUG: remove_image={request.form.get('remove_image')}", 'info')
        recipe.title = request.form.get('title')
        recipe.content = request.form.get('content')
        recipe.ingredients = request.form.get('ingredients')
        recipe.instructions = request.form.get('instructions')
        recipe.category_id = request.form.get('category_id', type=int)
        recipe.prep_time = request.form.get('prep_time', type=int)
        recipe.cook_time = request.form.get('cook_time', type=int)
        recipe.servings = request.form.get('servings', type=int)
        
        # Fotoğraf silme kontrolü (checkbox değeri kontrolü daha sağlam)
        if request.form.get('remove_image') in ('1', 'on', 'true'):
            recipe.image = None
        else:
            # Fotoğraf güncelleme - URL veya dosya yükleme
            image_url = request.form.get('image_url', '').strip()
            
            if image_url:
                # URL girilmişse önce doğrudan resim olup olmadığını çözmeyi dene
                resolved = resolve_image_url(image_url)
                if resolved:
                    recipe.image = resolved
                else:
                    recipe.image = image_url
            elif 'image' in request.files:
                # Dosya yüklenmişse kaydet
                file = request.files['image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    image_filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
                    recipe.image = image_filename
        
        db.session.commit()
        flash('Tarif güncellendi!', 'success')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    categories = Category.query.all()
    return render_template('edit_recipe.html', recipe=recipe, categories=categories)

@app.route('/recipe/<int:recipe_id>/delete', methods=['POST'])
@login_required
def delete_recipe(recipe_id):
    """Tarif silme"""
    recipe = Recipe.query.get_or_404(recipe_id)
    
    if recipe.user_id != current_user.id and not current_user.is_admin:
        flash('Bu tarifi silme yetkiniz yok.', 'danger')
        return redirect(url_for('recipe_detail', recipe_id=recipe_id))
    
    db.session.delete(recipe)
    db.session.commit()
    flash('Tarif silindi.', 'info')
    return redirect(url_for('my_recipes'))

# ============= ADMIN ROUTES =============

def admin_required(f):
    """Admin kontrolü decorator"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin panel ana sayfa"""
    stats = {
        'users': User.query.count(),
        'recipes': Recipe.query.count(),
        'categories': Category.query.count(),
        'comments': Comment.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)

# ============= ADMIN - RECIPES =============

@app.route('/admin/recipes')
@login_required
@admin_required
def admin_recipes():
    """Admin - Tarifler listesi"""
    recipes = Recipe.query.order_by(Recipe.created_at.desc()).all()
    return render_template('admin/recipes.html', recipes=recipes)

@app.route('/admin/recipes/<int:recipe_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_recipe(recipe_id):
    """Admin - Tarif silme"""
    recipe = Recipe.query.get_or_404(recipe_id)
    db.session.delete(recipe)
    db.session.commit()
    flash('Tarif silindi.', 'success')
    return redirect(url_for('admin_recipes'))

# ============= ADMIN - CATEGORIES =============

@app.route('/admin/categories')
@login_required
@admin_required
def admin_categories():
    """Admin - Kategoriler listesi"""
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_category():
    """Admin - Kategori ekleme"""
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        
        if not name or not slug:
            flash('İsim ve slug gerekli.', 'danger')
            return redirect(url_for('admin_add_category'))
        
        if Category.query.filter_by(slug=slug).first():
            flash('Bu slug zaten kullanılıyor.', 'danger')
            return redirect(url_for('admin_add_category'))
        
        category = Category(name=name, slug=slug, description=description)
        db.session.add(category)
        db.session.commit()
        
        flash('Kategori eklendi!', 'success')
        return redirect(url_for('admin_categories'))
    
    return render_template('admin/add_category.html')

@app.route('/admin/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_category(category_id):
    """Admin - Kategori düzenleme"""
    category = Category.query.get_or_404(category_id)
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.slug = request.form.get('slug')
        category.description = request.form.get('description')
        
        db.session.commit()
        flash('Kategori güncellendi!', 'success')
        return redirect(url_for('admin_categories'))
    
    return render_template('admin/edit_category.html', category=category)

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_category(category_id):
    """Admin - Kategori silme"""
    category = Category.query.get_or_404(category_id)
    
    if category.recipes:
        flash('Bu kategoriye ait tarifler var, önce onları silin veya taşıyın.', 'danger')
        return redirect(url_for('admin_categories'))
    
    db.session.delete(category)
    db.session.commit()
    flash('Kategori silindi.', 'success')
    return redirect(url_for('admin_categories'))

# ============= ADMIN - USERS =============

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """Admin - Kullanıcılar listesi"""
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>/toggle-admin', methods=['POST'])
@login_required
@admin_required
def admin_toggle_user_admin(user_id):
    """Admin - Kullanıcı admin durumunu değiştir"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Kendi admin durumunuzu değiştiremezsiniz.', 'danger')
        return redirect(url_for('admin_users'))
    
    user.is_admin = not user.is_admin
    db.session.commit()
    flash(f"Kullanıcı {'admin yapıldı' if user.is_admin else 'admin değil'}", 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Admin - Kullanıcı silme"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('Kendi hesabınızı silemezsiniz.', 'danger')
        return redirect(url_for('admin_users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Kullanıcı silindi.', 'success')
    return redirect(url_for('admin_users'))

# ============= ADMIN - COMMENTS =============

@app.route('/admin/comments')
@login_required
@admin_required
def admin_comments():
    """Admin - Yorumlar listesi"""
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments)

@app.route('/admin/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_comment(comment_id):
    """Admin - Yorum silme"""
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Yorum silindi.', 'success')
    return redirect(url_for('admin_comments'))

# ============= ADMIN - PAGES =============

@app.route('/admin/pages')
@login_required
@admin_required
def admin_pages():
    """Admin - Sayfalar listesi"""
    pages = Page.query.all()
    return render_template('admin/pages.html', pages=pages)

@app.route('/admin/pages/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_page():
    """Admin - Sayfa ekleme"""
    if request.method == 'POST':
        slug = request.form.get('slug')
        title = request.form.get('title')
        content = request.form.get('content')
        
        if not slug or not title:
            flash('Slug ve başlık gerekli.', 'danger')
            return redirect(url_for('admin_add_page'))
        
        if Page.query.filter_by(slug=slug).first():
            flash('Bu slug zaten kullanılıyor.', 'danger')
            return redirect(url_for('admin_add_page'))
        
        page = Page(slug=slug, title=title, content=content)
        db.session.add(page)
        db.session.commit()
        
        flash('Sayfa eklendi!', 'success')
        return redirect(url_for('admin_pages'))
    
    return render_template('admin/add_page.html')

@app.route('/admin/pages/<int:page_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_page(page_id):
    """Admin - Sayfa düzenleme"""
    page = Page.query.get_or_404(page_id)
    
    if request.method == 'POST':
        page.slug = request.form.get('slug')
        page.title = request.form.get('title')
        page.content = request.form.get('content')
        
        db.session.commit()
        flash('Sayfa güncellendi!', 'success')
        return redirect(url_for('admin_pages'))
    
    return render_template('admin/edit_page.html', page=page)

@app.route('/admin/pages/<int:page_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_page(page_id):
    """Admin - Sayfa silme"""
    page = Page.query.get_or_404(page_id)
    db.session.delete(page)
    db.session.commit()
    flash('Sayfa silindi.', 'success')
    return redirect(url_for('admin_pages'))

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# ============= CONTEXT PROCESSORS =============

@app.context_processor
def inject_categories():
    """Tüm template'lerde kategorileri kullanılabilir yap"""
    return dict(all_categories=Category.query.all())

# ============= CLI COMMANDS =============

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
