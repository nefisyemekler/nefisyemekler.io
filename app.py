import os
import json
import requests
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, User, Category, Recipe, Comment, Page, Image
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///nefisyemekler.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Lütfen giriş yapın.'

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

@app.route('/ai-recipe', methods=['GET', 'POST'])
def ai_recipe():
    """AI ile tarif önerisi - Google Gemini kullanarak"""
    if request.method == 'POST':
        ingredients = request.form.get('ingredients', '').strip()
        preferences = request.form.get('preferences', '').strip()
        
        if not ingredients:
            flash('Lütfen malzemeleri girin.', 'danger')
            return redirect(url_for('ai_recipe'))
        
        try:
            # Google Gemini API key kontrolü
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                return render_template('ai_recipe.html', 
                    error='Google Gemini API key bulunamadı. Lütfen .env dosyasına GEMINI_API_KEY ekleyin.')
            
            # Prompt hazırla
            prompt = f"""Sen bir uzman aşçısın. Aşağıdaki malzemeler ile yapılabilecek lezzetli bir Türk yemeği tarifi öner.

Malzemeler: {ingredients}
"""
            if preferences:
                prompt += f"Tercihler: {preferences}\n"
            
            prompt += """
Lütfen aşağıdaki JSON formatında bir tarif öner:
{
    "title": "Tarif adı",
    "description": "Tarif hakkında kısa açıklama",
    "ingredients": ["malzeme 1", "malzeme 2", ...],
    "instructions": ["adım 1", "adım 2", ...],
    "prep_time": hazırlık süresi (dakika),
    "cook_time": pişirme süresi (dakika),
    "servings": kaç kişilik
}

Sadece JSON formatında yanıt ver, başka açıklama ekleme."""

            # Google Gemini API'ye istek gönder
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            data = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 2048
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code != 200:
                return render_template('ai_recipe.html', 
                    error=f'API hatası: {response.status_code} - {response.text}')
            
            result = response.json()
            
            # Gemini yanıtını parse et
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                
                # Yanıt yapısını kontrol et
                if 'content' not in candidate:
                    return render_template('ai_recipe.html', 
                        error='AI yanıt formatı hatalı. Lütfen tekrar deneyin.')
                
                if 'parts' not in candidate['content']:
                    return render_template('ai_recipe.html', 
                        error='AI yanıt formatı eksik. Lütfen tekrar deneyin.')
                
                recipe_text = candidate['content']['parts'][0]['text'].strip()
                
                # Debug için yanıtı yazdır
                print("=== AI YANITI ===")
                print(recipe_text)
                print("=================")
                
                # JSON'u temizle (markdown kod bloklarını kaldır)
                if '```json' in recipe_text:
                    recipe_text = recipe_text.split('```json')[1].split('```')[0].strip()
                elif '```' in recipe_text:
                    recipe_text = recipe_text.split('```')[1].split('```')[0].strip()
                
                # Tek ve çift tırnakları düzelt
                recipe_text = recipe_text.replace('\n', ' ').replace('\\n', ' ')
                
                print("=== TEMİZLENMİŞ JSON ===")
                print(recipe_text)
                print("========================")
                
                try:
                    recipe_data = json.loads(recipe_text)
                except json.JSONDecodeError as json_err:
                    print(f"JSON PARSE HATASI: {json_err}")
                    # Alternatif: regex ile JSON'u çıkar
                    import re
                    json_match = re.search(r'\{.*\}', recipe_text, re.DOTALL)
                    if json_match:
                        recipe_data = json.loads(json_match.group())
                    else:
                        return render_template('ai_recipe.html', 
                            error=f'AI yanıtı düzgün JSON formatında değil. Lütfen tekrar deneyin.')
                
                return render_template('ai_recipe.html', recipe_suggestion=recipe_data)
            else:
                return render_template('ai_recipe.html', 
                    error='AI yanıt üretemedi. Lütfen tekrar deneyin.')
            
        except json.JSONDecodeError as e:
            return render_template('ai_recipe.html', 
                error=f'AI yanıtı işlenirken hata oluştu. Lütfen tekrar deneyin.')
        except requests.exceptions.RequestException as e:
            return render_template('ai_recipe.html', 
                error=f'Bağlantı hatası: {str(e)}')
        except Exception as e:
            return render_template('ai_recipe.html', 
                error=f'Bir hata oluştu: {str(e)}')
    
    return render_template('ai_recipe.html')

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
            
            # 1 haftalık yeme programı oluştur
            if request.form.get('generate_meal_plan'):
                print("=== YEME PROGRAMI OLUŞTURULUYOR ===")
                meal_plan = generate_weekly_meal_plan(result)
                if meal_plan:
                    result['meal_plan'] = meal_plan
                    print("=== YEME PROGRAMI OLUŞTURULDU ===")
                else:
                    print("=== YEME PROGRAMI OLUŞTURULAMADI ===")
                    flash('Yeme programı oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.', 'warning')
            
        except (ValueError, TypeError):
            flash('Lütfen tüm alanları doğru şekilde doldurun.', 'danger')
    
    return render_template('calorie_calculator.html', result=result)

def generate_weekly_meal_plan(result):
    """Gemini AI ile 1 haftalık yeme programı oluştur"""
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("=== API KEY BULUNAMADI ===")
            return None
        
        print(f"=== API KEY MEVCUT ===")
        
        # API endpoint - AI recipe ile aynı model
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}'
        
        # Prompt oluştur - BASİT versiyon
        prompt = f"""
{result['target_calories']} kalori hedefli 7 günlük Türk mutfağı menüsü oluştur.
Protein: {result['protein_grams']}g, Karb: {result['carb_grams']}g, Yağ: {result['fat_grams']}g

Her gün 5 öğün (Kahvaltı, Ara1, Öğle, Ara2, Akşam) KISA olarak belirt.

JSON formatı (7 GÜN MUTLAKA):
{{
  "gunler": [
    {{
      "gun": "Pazartesi",
      "ogunler": [
        {{"ogun_adi": "Kahvaltı", "yemekler": ["Menemen", "Peynir"], "kalori": 350, "protein": 25, "karbonhidrat": 30, "yag": 15}},
        {{"ogun_adi": "Ara Öğün 1", "yemekler": ["Elma"], "kalori": 80, "protein": 1, "karbonhidrat": 20, "yag": 0}},
        {{"ogun_adi": "Öğle Yemeği", "yemekler": ["Tavuk", "Pilav"], "kalori": 500, "protein": 40, "karbonhidrat": 50, "yag": 15}},
        {{"ogun_adi": "Ara Öğün 2", "yemekler": ["Yoğurt"], "kalori": 100, "protein": 10, "karbonhidrat": 12, "yag": 3}},
        {{"ogun_adi": "Akşam Yemeği", "yemekler": ["Balık", "Salata"], "kalori": 400, "protein": 35, "karbonhidrat": 20, "yag": 18}}
      ],
      "toplam_kalori": 1430, "toplam_protein": 111, "toplam_karbonhidrat": 132, "toplam_yag": 51
    }}
  ]
}}

Sadece JSON, açıklama yok. 7 günün HEPSİNİ yaz.
"""
        
        # API isteği
        headers = {'Content-Type': 'application/json'}
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': 0.5,
                'maxOutputTokens': 8192
            }
        }
        
        print("=== API'YE İSTEK GÖNDERİLİYOR ===")
        
        # Retry mekanizması - 3 deneme
        for attempt in range(3):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=60)
                response.raise_for_status()
                break
            except requests.exceptions.HTTPError as e:
                if attempt < 2:  # Son denemede değilse
                    print(f"=== DENEME {attempt + 1} BAŞARISIZ, YENİDEN DENENİYOR ===")
                    import time
                    time.sleep(2)  # 2 saniye bekle
                    continue
                else:
                    raise  # Son denemede de başarısız olursa hatayı fırlat
        
        result_data = response.json()
        print(f"=== API YANITI ALINDI ===")
        
        if 'candidates' in result_data and len(result_data['candidates']) > 0:
            meal_plan_text = result_data['candidates'][0]['content']['parts'][0]['text']
            
            print("=== AI YANITI ===")
            print(meal_plan_text[:500])
            print("=================")
            
            # JSON temizleme
            meal_plan_text = meal_plan_text.strip()
            if meal_plan_text.startswith('```json'):
                meal_plan_text = meal_plan_text[7:]
            if meal_plan_text.startswith('```'):
                meal_plan_text = meal_plan_text[3:]
            if meal_plan_text.endswith('```'):
                meal_plan_text = meal_plan_text[:-3]
            meal_plan_text = meal_plan_text.strip()
            
            # JSON parse
            try:
                meal_plan_data = json.loads(meal_plan_text)
                print("=== JSON PARSE BAŞARILI ===")
                return meal_plan_data
            except json.JSONDecodeError as e:
                print(f"=== JSON PARSE HATASI: {str(e)} ===")
                import re
                match = re.search(r'\{.*\}', meal_plan_text, re.DOTALL)
                if match:
                    meal_plan_data = json.loads(match.group(0))
                    print("=== REGEX İLE JSON PARSE BAŞARILI ===")
                    return meal_plan_data
        else:
            print("=== API YANITI BOŞ VEYA HATALI ===")
        
        return None
        
    except Exception as e:
        print(f"=== MEAL PLAN HATASI: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return None

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
        
        # Ana resmi yükle
        image_filename = None
        if 'image' in request.files:
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
        recipe.title = request.form.get('title')
        recipe.content = request.form.get('content')
        recipe.ingredients = request.form.get('ingredients')
        recipe.instructions = request.form.get('instructions')
        recipe.category_id = request.form.get('category_id', type=int)
        recipe.prep_time = request.form.get('prep_time', type=int)
        recipe.cook_time = request.form.get('cook_time', type=int)
        recipe.servings = request.form.get('servings', type=int)
        
        # Yeni resim yükleme
        if 'image' in request.files:
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
