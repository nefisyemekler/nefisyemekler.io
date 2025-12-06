from app import app, db
from models import User, Category

def seed_database():
    """Veritabanına temel verileri ekle"""
    
    with app.app_context():
        # Tabloları oluştur (zaten varsa hata vermez)
        db.create_all()
        print("✓ Veritabanı tabloları hazır")
        
        # Admin kullanıcı (yoksa)
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print("✓ Admin kullanıcısı oluşturuldu (username: admin, password: admin123)")
        
        # Kategoriler (yoksa)
        categories_data = [
            {'name': 'Kahvaltı', 'slug': 'kahvalti', 'description': 'Güne enerjik başlamak için lezzetli kahvaltı tarifleri'},
            {'name': 'Ana Yemekler', 'slug': 'ana-yemekler', 'description': 'Doyurucu ve lezzetli ana yemek tarifleri'},
            {'name': 'Tatlılar', 'slug': 'tatlilar', 'description': 'Damak tadınıza uygun tatlı tarifleri'},
            {'name': 'Çorbalar', 'slug': 'corbalar', 'description': 'Sıcacık ve doyurucu çorba tarifleri'},
            {'name': 'Salatalar', 'slug': 'salatalar', 'description': 'Sağlıklı ve ferahlatıcı salata tarifleri'},
        ]
        
        for cat_data in categories_data:
            existing = Category.query.filter_by(slug=cat_data['slug']).first()
            if not existing:
                cat = Category(**cat_data)
                db.session.add(cat)
                print(f"✓ Kategori eklendi: {cat_data['name']}")
        
        db.session.commit()
        print("✓ Seed tamamlandı!")

if __name__ == '__main__':
    seed_database()
