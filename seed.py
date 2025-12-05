from app import app, db
from models import User, Category, Recipe, Comment, Page
from datetime import datetime

def seed_database():
    """Veritabanına örnek veriler ekle"""
    
    with app.app_context():
        # Önce tüm tabloları temizle
        db.drop_all()
        db.create_all()
        
        print("Veritabanı tablolan oluşturuldu...")
        
        # 1. Admin kullanıcı oluştur
        admin = User(username='admin', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 2. Normal kullanıcılar oluştur
        user1 = User(username='ayse')
        user1.set_password('12345')
        db.session.add(user1)
        
        user2 = User(username='mehmet')
        user2.set_password('12345')
        db.session.add(user2)
        
        db.session.commit()
        print("Kullanıcılar eklendi...")
        
        # 3. Kategoriler oluştur
        categories_data = [
            {'name': 'Kahvaltı', 'slug': 'kahvalti', 'description': 'Güne enerjik başlamak için lezzetli kahvaltı tarifleri'},
            {'name': 'Öğle Yemeği', 'slug': 'ogle-yemegi', 'description': 'Doyurucu ve pratik öğle yemeği tarifleri'},
            {'name': 'Akşam Yemeği', 'slug': 'aksam-yemegi', 'description': 'Ailenizle paylaşabileceğiniz özel akşam yemeği tarifleri'},
            {'name': 'Tatlılar', 'slug': 'tatlilar', 'description': 'Damak tadınıza uygun tatlı tarifleri'},
            {'name': 'Çorbalar', 'slug': 'corbalar', 'description': 'Sıcacık ve doyurucu çorba tarifleri'},
            {'name': 'Salatalar', 'slug': 'salatalar', 'description': 'Sağlıklı ve ferahlatıcı salata tarifleri'},
            {'name': 'Dünya Mutfağı', 'slug': 'dunya-mutfagi', 'description': 'Dünya mutfaklarından özel tarifler'}
        ]
        
        categories = []
        for cat_data in categories_data:
            cat = Category(**cat_data)
            db.session.add(cat)
            categories.append(cat)
        
        db.session.commit()
        print("Kategoriler eklendi...")
        
        # 4. Tarifler oluştur
        recipes_data = [
            {
                'title': 'Menemen',
                'content': 'Geleneksel Türk kahvaltısının vazgeçilmez lezzeti menemen',
                'ingredients': '''4 adet yumurta
2 adet domates
2 adet sivri biber
1 soğan
3 yemek kaşığı sıvı yağ
Tuz, karabiber''',
                'instructions': '''1. Soğanları doğrayıp yağda kavurun
2. Biberleri ekleyip kavurmaya devam edin
3. Domatesleri ekleyin ve suyunu çekene kadar pişirin
4. Yumurtaları çırpıp ekleyin
5. Karıştırarak pişirin''',
                'category_id': 1,  # Kahvaltı
                'user_id': 1,  # admin
                'prep_time': 10,
                'cook_time': 15,
                'servings': 2
            },
            {
                'title': 'Mercimek Çorbası',
                'content': 'Sıcacık ve doyurucu klasik mercimek çorbası tarifi',
                'ingredients': '''1 su bardağı kırmızı mercimek
1 adet soğan
1 adet havuç
1 yemek kaşığı salça
6 su bardağı su
Tuz, karabiber, kimyon''',
                'instructions': '''1. Mercimeği yıkayın
2. Soğan ve havucu doğrayın
3. Tüm malzemeleri tencereye atın
4. Mercimekler yumuşayana kadar pişirin
5. Blenderdan geçirin''',
                'category_id': 5,  # Çorbalar
                'user_id': 2,  # ayse
                'prep_time': 10,
                'cook_time': 30,
                'servings': 4
            },
            {
                'title': 'Karnıyarık',
                'content': 'Enfes Türk mutfağı klasiği karnıyarık tarifi',
                'ingredients': '''4 adet patlıcan
300g kıyma
2 adet domates
2 adet sivri biber
1 soğan
3 diş sarımsak
Salça, baharatlar''',
                'instructions': '''1. Patlıcanları soyun ve kızartın
2. Kıymayı soğanla kavurun
3. Patlıcanları ortasından yırıp içini doldurun
4. Fırında pişirin''',
                'category_id': 3,  # Akşam Yemeği
                'user_id': 1,  # admin
                'prep_time': 30,
                'cook_time': 45,
                'servings': 4
            },
            {
                'title': 'Sütlaç',
                'content': 'Fırında karamelize olmuş sütlaç',
                'ingredients': '''1 litre süt
1/2 su bardağı pirinç
1 su bardağı şeker
1 yemek kaşığı un
Vanilya''',
                'instructions': '''1. Pirinci haşlayın
2. Sütü ekleyip kaynatın
3. Şeker ve unu ekleyin
4. Kıvam alınca kaselere alın
5. Fırında üstünü karamelize edin''',
                'category_id': 4,  # Tatlılar
                'user_id': 3,  # mehmet
                'prep_time': 15,
                'cook_time': 40,
                'servings': 6
            },
            {
                'title': 'Çoban Salata',
                'content': 'Ferahlatıcı ve sağlıklı çoban salata',
                'ingredients': '''3 adet domates
2 adet salatalık
1 adet yeşil biber
1 soğan
Maydanoz
Zeytinyağı, limon, tuz''',
                'instructions': '''1. Tüm sebzeleri küp küp doğrayın
2. Maydanozu ince kıyın
3. Zeytinyağı, limon ve tuzla karıştırın''',
                'category_id': 6,  # Salatalar
                'user_id': 2,  # ayse
                'prep_time': 15,
                'cook_time': 0,
                'servings': 4
            },
            {
                'title': 'Tavuklu Pilav',
                'content': 'Pratik ve lezzetli tavuklu pilav tarifi',
                'ingredients': '''2 su bardağı pirinç
300g tavuk göğsü
1 soğan
3 su bardağı tavuk suyu
Tereyağı, tuz, karabiber''',
                'instructions': '''1. Tavukları haşlayın ve didikleyin
2. Pirinci yıkayın
3. Soğanı kavurun, pirinci ekleyin
4. Tavuk ve suyu ekleyip pişirin''',
                'category_id': 2,  # Öğle Yemeği
                'user_id': 1,  # admin
                'prep_time': 20,
                'cook_time': 25,
                'servings': 4
            },
            # Kahvaltı kategorisi için 3 tarif daha
            {
                'title': 'Pankek',
                'content': 'Yumuşacık ve hafif pankek tarifi',
                'ingredients': '''2 su bardağı un
2 yumurta
1.5 su bardağı süt
2 yemek kaşığı şeker
1 paket kabartma tozu
Tereyağı''',
                'instructions': '''1. Kuru malzemeleri karıştırın
2. Yumurta ve sütü ekleyin
3. Pürüzsüz bir hamur elde edin
4. Tavada pişirin''',
                'category_id': 1,  # Kahvaltı
                'user_id': 2,
                'prep_time': 10,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'Sigara Böreği',
                'content': 'Çıtır çıtır sigara böreği tarifi',
                'ingredients': '''1 paket yufka
200g beyaz peynir
Maydanoz
1 yumurta
Kızartma yağı''',
                'instructions': '''1. Peyniri ezin, maydanozu ekleyin
2. Yufkaları kesin ve iç harcı koyun
3. Rulo şeklinde sarın
4. Kızgın yağda kızartın''',
                'category_id': 1,  # Kahvaltı
                'user_id': 3,
                'prep_time': 20,
                'cook_time': 15,
                'servings': 6
            },
            {
                'title': 'Yumurtalı Sandviç',
                'content': 'Pratik ve doyurucu kahvaltılık sandviç',
                'ingredients': '''4 dilim ekmek
2 yumurta
2 dilim kaşar
Domates, salatalık
Tereyağı''',
                'instructions': '''1. Yumurtaları omlet yapın
2. Ekmeği tavada kızartın
3. Malzemeleri araya yerleştirin
4. Sıcak servis yapın''',
                'category_id': 1,  # Kahvaltı
                'user_id': 1,
                'prep_time': 10,
                'cook_time': 10,
                'servings': 2
            },
            # Öğle Yemeği kategorisi için 3 tarif daha
            {
                'title': 'Makarna',
                'content': 'Kremalı tavuklu makarna',
                'ingredients': '''400g makarna
300g tavuk göğsü
200ml krema
1 soğan
Sarımsak, parmesan''',
                'instructions': '''1. Makarnayı haşlayın
2. Tavukları soteleyin
3. Krema ve baharatları ekleyin
4. Makarna ile karıştırın''',
                'category_id': 2,  # Öğle Yemeği
                'user_id': 2,
                'prep_time': 15,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'Köfte',
                'content': 'Yumuşacık ev yapımı köfte',
                'ingredients': '''500g kıyma
1 yumurta
1 dilim bayat ekmek
Soğan, sarımsak
Baharatlar''',
                'instructions': '''1. Tüm malzemeleri yoğurun
2. Köfte şekli verin
3. Tavada veya fırında pişirin
4. Sıcak servis yapın''',
                'category_id': 2,  # Öğle Yemeği
                'user_id': 3,
                'prep_time': 20,
                'cook_time': 15,
                'servings': 4
            },
            {
                'title': 'Mantı',
                'content': 'El açması klasik mantı',
                'ingredients': '''500g un
2 yumurta
300g kıyma
Yoğurt, sarımsak
Tereyağı, salça''',
                'instructions': '''1. Hamuru yoğurun ve açın
2. Küçük kareler kesin
3. İç harcı koyup kapatın
4. Haşlayıp yoğurtla servis yapın''',
                'category_id': 2,  # Öğle Yemeği
                'user_id': 1,
                'prep_time': 60,
                'cook_time': 30,
                'servings': 6
            },
            # Akşam Yemeği kategorisi için 3 tarif daha
            {
                'title': 'İmam Bayıldı',
                'content': 'Zeytinyağlı imam bayıldı',
                'ingredients': '''4 adet patlıcan
3 soğan
4 domates
1 su bardağı zeytinyağı
Sarımsak, maydanoz''',
                'instructions': '''1. Patlıcanları soyun
2. Soğanları soteleyip iç harcı hazırlayın
3. Patlıcanları doldurun
4. Fırında pişirin''',
                'category_id': 3,  # Akşam Yemeği
                'user_id': 2,
                'prep_time': 30,
                'cook_time': 40,
                'servings': 4
            },
            {
                'title': 'Etli Nohut',
                'content': 'Doyurucu etli nohut yemeği',
                'ingredients': '''500g kuşbaşı et
2 su bardağı nohut
2 soğan
2 yemek kaşığı salça
Baharatlar''',
                'instructions': '''1. Nohutu haşlayın
2. Eti kavurun
3. Salçayı ekleyin
4. Nohutu ekleyip pişirin''',
                'category_id': 3,  # Akşam Yemeği
                'user_id': 3,
                'prep_time': 20,
                'cook_time': 60,
                'servings': 6
            },
            {
                'title': 'Fırın Tavuk',
                'content': 'Baharatlı fırın tavuk',
                'ingredients': '''1 bütün tavuk
3 patates
2 havuç
Zeytinyağı, baharatlar''',
                'instructions': '''1. Tavuğu baharatlarla marine edin
2. Sebzeleri doğrayın
3. Fırın tepsisine dizin
4. 180 derecede pişirin''',
                'category_id': 3,  # Akşam Yemeği
                'user_id': 1,
                'prep_time': 20,
                'cook_time': 90,
                'servings': 6
            },
            # Tatlılar kategorisi için 3 tarif daha
            {
                'title': 'Revani',
                'content': 'Şerbetli nefis revani',
                'ingredients': '''4 yumurta
1 su bardağı şeker
1 su bardağı irmik
1 su bardağı un
1 paket kabartma tozu
Şerbet için şeker ve su''',
                'instructions': '''1. Malzemeleri karıştırın
2. Fırın tepsisine dökün
3. Pişirin ve dilimlendirin
4. Şerbeti döküp bekletin''',
                'category_id': 4,  # Tatlılar
                'user_id': 2,
                'prep_time': 15,
                'cook_time': 30,
                'servings': 12
            },
            {
                'title': 'Tiramisu',
                'content': 'İtalyan klasiği tiramisu',
                'ingredients': '''250g maskarpone
3 yumurta
1 paket kedi dili
1 fincan espresso
Kakao''',
                'instructions': '''1. Krema karışımını hazırlayın
2. Kedi dillerini kahveye batırın
3. Katmanlar halinde dizin
4. Buzdolabında dinlendirin''',
                'category_id': 4,  # Tatlılar
                'user_id': 3,
                'prep_time': 30,
                'cook_time': 0,
                'servings': 6
            },
            {
                'title': 'Kazandibi',
                'content': 'Geleneksel kazandibi tatlısı',
                'ingredients': '''1 litre süt
1 su bardağı şeker
3 yemek kaşığı nişasta
1 yumurta sarısı
Vanilya''',
                'instructions': '''1. Sütü kaynatın
2. Nişasta ve şekeri ekleyin
3. Koyulaşana kadar pişirin
4. Tavada altını yakın''',
                'category_id': 4,  # Tatlılar
                'user_id': 1,
                'prep_time': 15,
                'cook_time': 30,
                'servings': 6
            },
            # Çorbalar kategorisi için 3 tarif daha
            {
                'title': 'Ezogelin Çorbası',
                'content': 'Nefis ezogelin çorbası',
                'ingredients': '''1 su bardağı kırmızı mercimek
1/2 su bardağı bulgur
1 soğan
2 yemek kaşığı salça
Baharatlar''',
                'instructions': '''1. Mercimek ve bulguru haşlayın
2. Soğan ve salçayı kavurun
3. Tüm malzemeleri birleştirin
4. Blenderdan geçirin''',
                'category_id': 5,  # Çorbalar
                'user_id': 2,
                'prep_time': 10,
                'cook_time': 25,
                'servings': 4
            },
            {
                'title': 'Tavuk Çorbası',
                'content': 'Sıcacık tavuk çorbası',
                'ingredients': '''2 tavuk budu
1 havuç
1 patates
1 soğan
Un, yumurta''',
                'instructions': '''1. Tavukları haşlayın
2. Sebzeleri ekleyin
3. Un ve yumurta ile koyulaştırın
4. Limon ekleyip servis yapın''',
                'category_id': 5,  # Çorbalar
                'user_id': 3,
                'prep_time': 15,
                'cook_time': 40,
                'servings': 6
            },
            {
                'title': 'Domates Çorbası',
                'content': 'Kremalı domates çorbası',
                'ingredients': '''6 adet domates
1 soğan
2 yemek kaşığı un
200ml krema
Fesleğen''',
                'instructions': '''1. Domatesleri haşlayıp soyun
2. Soğanla soteleyip blenderdan geçirin
3. Un ekleyip koyulaştırın
4. Krema ekleyin''',
                'category_id': 5,  # Çorbalar
                'user_id': 1,
                'prep_time': 15,
                'cook_time': 25,
                'servings': 4
            },
            # Salatalar kategorisi için 3 tarif daha
            {
                'title': 'Mevsim Salata',
                'content': 'Renkli ve sağlıklı mevsim salata',
                'ingredients': '''Marul
Roka
Havuç
Kırmızı lahana
Zeytinyağı, limon''',
                'instructions': '''1. Sebzeleri yıkayın
2. Doğrayın veya rendeleyin
3. Sos hazırlayın
4. Karıştırıp servis yapın''',
                'category_id': 6,  # Salatalar
                'user_id': 2,
                'prep_time': 15,
                'cook_time': 0,
                'servings': 4
            },
            {
                'title': 'Tavuklu Sezar Salata',
                'content': 'Protein deposu sezar salata',
                'ingredients': '''2 tavuk göğsü
Marul
Kruton
Parmesan
Sezar sos''',
                'instructions': '''1. Tavukları ızgara yapın
2. Marulu yıkayıp parçalayın
3. Tüm malzemeleri karıştırın
4. Sos ile servis yapın''',
                'category_id': 6,  # Salatalar
                'user_id': 3,
                'prep_time': 20,
                'cook_time': 15,
                'servings': 2
            },
            {
                'title': 'Kısır',
                'content': 'Geleneksel lezzetli kısır',
                'ingredients': '''2 su bardağı ince bulgur
3 yemek kaşığı salça
2 domates
Maydanoz, nane
Zeytinyağı, limon''',
                'instructions': '''1. Bulguru demleyin
2. Salça ve limon suyu ekleyin
3. Domates ve yeşillikleri ekleyin
4. Yoğurup servis yapın''',
                'category_id': 6,  # Salatalar
                'user_id': 1,
                'prep_time': 20,
                'cook_time': 0,
                'servings': 6
            },
            # Dünya Mutfağı kategorisi için 3 tarif
            {
                'title': 'Sushi',
                'content': 'Japon mutfağından sushi',
                'ingredients': '''2 su bardağı sushi pirinci
Nori yaprağı
Somon
Avokado
Pirinç sirkesi''',
                'instructions': '''1. Pirinci pişirin ve soğutun
2. Nori yaprağına pirinci yayın
3. Malzemeleri dizin
4. Rulo yapıp kesin''',
                'category_id': 7,  # Dünya Mutfağı
                'user_id': 1,
                'prep_time': 40,
                'cook_time': 20,
                'servings': 4
            },
            {
                'title': 'Tacos',
                'content': 'Meksika mutfağından tacos',
                'ingredients': '''Tortilla
500g kıyma
Domates, marul
Cheddar peyniri
Acı sos''',
                'instructions': '''1. Kıymayı baharatlarla kavurun
2. Tortillaları ısıtın
3. Malzemeleri dizin
4. Dilediğiniz gibi süsleyin''',
                'category_id': 7,  # Dünya Mutfağı
                'user_id': 2,
                'prep_time': 15,
                'cook_time': 15,
                'servings': 4
            },
            {
                'title': 'Pizza Margherita',
                'content': 'İtalyan klasiği pizza margherita',
                'ingredients': '''Pizza hamuru
Domates sosu
Mozzarella
Taze fesleğen
Zeytinyağı''',
                'instructions': '''1. Hamuru açın
2. Sos sürün
3. Peynir ve malzemeleri dizin
4. Fırında pişirin''',
                'category_id': 7,  # Dünya Mutfağı
                'user_id': 3,
                'prep_time': 20,
                'cook_time': 15,
                'servings': 4
            }
        ]
        
        recipes = []
        for recipe_data in recipes_data:
            recipe = Recipe(**recipe_data)
            db.session.add(recipe)
            recipes.append(recipe)
        
        db.session.commit()
        print("Tarifler eklendi...")
        
        # 5. Yorumlar oluştur
        comments_data = [
            {
                'recipe_id': 1,
                'user_id': 2,
                'body': 'Çok lezzetli oldu, teşekkürler!',
                'rating': 5
            },
            {
                'recipe_id': 1,
                'user_id': 3,
                'body': 'Ailem çok beğendi, kesinlikle tekrar yapacağım.',
                'rating': 5
            },
            {
                'recipe_id': 2,
                'user_id': 1,
                'body': 'Klasik tarif, harika oldu.',
                'rating': 4
            },
            {
                'recipe_id': 3,
                'user_id': 2,
                'body': 'İlk defa denedim ve çok güzel oldu!',
                'rating': 5
            },
            {
                'recipe_id': 4,
                'user_id': 1,
                'body': 'Annemin tarifi gibi oldu, harika!',
                'rating': 5
            },
            {
                'recipe_id': 5,
                'user_id': 3,
                'body': 'Çok taze ve lezzetli bir salata.',
                'rating': 4
            },
            {
                'recipe_id': 6,
                'user_id': 2,
                'body': 'Pratik ve doyurucu, teşekkürler.',
                'rating': 4
            }
        ]
        
        for comment_data in comments_data:
            comment = Comment(**comment_data)
            db.session.add(comment)
        
        db.session.commit()
        print("Yorumlar eklendi...")
        
        # 6. Sayfalar oluştur
        pages_data = [
            {
                'slug': 'about',
                'title': 'Hakkımızda',
                'content': '''<h2>Nefis Yemekler'e Hoş Geldiniz!</h2>
                <p>Biz, yemek yapmanın sadece bir ihtiyaç değil, aynı zamanda bir sanat ve tutku olduğuna inanıyoruz. 
                Nefis Yemekler platformu, lezzetli tarifleri paylaşmak, yeni tatlar keşfetmek ve mutfak deneyimlerinizi 
                geliştirmek için oluşturuldu.</p>
                
                <h3>Misyonumuz</h3>
                <p>Türk mutfağının zengin lezzetlerini ve dünya mutfaklarından seçkin tarifleri bir araya getirerek, 
                herkesin kolayca erişebileceği bir tarif platformu oluşturmak.</p>
                
                <h3>Vizyonumuz</h3>
                <p>Türkiye'nin en kapsamlı ve kullanıcı dostu yemek tarifi platformu olmak.</p>
                
                <h3>Değerlerimiz</h3>
                <ul>
                    <li>Kaliteli ve test edilmiş tarifler</li>
                    <li>Kullanıcı dostu arayüz</li>
                    <li>Topluluk odaklı yaklaşım</li>
                    <li>Sürekli gelişim ve yenilik</li>
                </ul>'''
            },
            {
                'slug': 'contact',
                'title': 'İletişim',
                'content': '''<h2>Bizimle İletişime Geçin</h2>
                <p>Sorularınız, önerileriniz veya geri bildirimleriniz için bizimle iletişime geçebilirsiniz.</p>
                
                <h3>İletişim Bilgileri</h3>
                <p><strong>E-posta:</strong> info@nefisyemekler.com</p>
                <p><strong>Telefon:</strong> +90 (212) 555 00 00</p>
                <p><strong>Adres:</strong> İstanbul, Türkiye</p>
                
                <h3>Sosyal Medya</h3>
                <p>Bizi sosyal medyada takip edin!</p>'''
            }
        ]
        
        for page_data in pages_data:
            page = Page(**page_data)
            db.session.add(page)
        
        db.session.commit()
        print("Sayfalar eklendi...")
        
        print("\n✅ Veritabanı başarıyla dolduruldu!")
        print(f"👤 Kullanıcılar: {User.query.count()}")
        print(f"📁 Kategoriler: {Category.query.count()}")
        print(f"🍳 Tarifler: {Recipe.query.count()}")
        print(f"💬 Yorumlar: {Comment.query.count()}")
        print(f"📄 Sayfalar: {Page.query.count()}")
        print("\n🔑 Admin kullanıcı: username='admin', password='admin123'")
        print("🔑 Normal kullanıcı: username='ayse', password='12345'")
        print("🔑 Normal kullanıcı: username='mehmet', password='12345'")

if __name__ == '__main__':
    seed_database()
