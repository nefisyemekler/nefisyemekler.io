# Render.com'da Deploy - Adım Adım Kılavuz

## 1. GitHub'a Yükleyin

Önce kodlarınızı GitHub'a push edin:

```bash
git add .
git commit -m "Render.com için hazırlık"
git push origin main
```

## 2. Render.com Hesabı Oluşturun

1. **render.com** adresine gidin
2. **Get Started** butonuna tıklayın
3. **GitHub hesabınızla giriş yapın**

## 3. Yeni Web Service Oluşturun

1. Dashboard'da **"New +"** butonuna tıklayın
2. **"Web Service"** seçin
3. **GitHub repository'nizi** seçin: `nefisyemekler/nefisyemekler.io`
4. **Connect** butonuna tıklayın

## 4. Web Service Ayarlarını Yapın

Aşağıdaki ayarları yapın:

- **Name**: `nefisyemekler` (veya istediğiniz isim)
- **Region**: `Frankfurt (EU Central)` (Türkiye'ye en yakın)
- **Branch**: `main`
- **Root Directory**: boş bırakın
- **Runtime**: `Python 3`
- **Build Command**: `./build.sh`
- **Start Command**: `gunicorn app:app`
- **Instance Type**: `Free`

## 5. Environment Variables Ekleyin

**Advanced** kısmında **Add Environment Variable** butonuna tıklayın ve şunları ekleyin:

```
SECRET_KEY = [buraya-güçlü-bir-key-girin-örnek: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6]
PYTHON_VERSION = 3.11.0
GEMINI_API_KEY = [varsa-gemini-api-keyiniz]
```

**ÖNEMLİ**: `SECRET_KEY` için güçlü bir şifre oluşturun (en az 32 karakter)

## 6. PostgreSQL Database Oluşturun

1. Dashboard'da tekrar **"New +"** butonuna tıklayın
2. **"PostgreSQL"** seçin
3. **Name**: `nefisyemekler-db`
4. **Database**: `nefisyemekler`
5. **User**: `nefisyemekler`
6. **Region**: `Frankfurt (EU Central)` (Web service ile aynı)
7. **Instance Type**: `Free`
8. **Create Database** butonuna tıklayın

## 7. Database'i Web Service'e Bağlayın

1. Database oluştuktan sonra, **Internal Database URL** kopyalayın
2. Web Service ayarlarına geri dönün
3. **Environment** sekmesinde **Add Environment Variable** butonuna tıklayın
4. Şunu ekleyin:
   ```
   DATABASE_URL = [buraya-internal-database-url-yapıştırın]
   ```

## 8. Deploy Başlatın

1. **Create Web Service** butonuna tıklayın
2. Deploy işlemi başlayacak (2-3 dakika sürer)
3. **Logs** sekmesinden süreci takip edin

## 9. Siteniz Hazır! 🎉

Deploy tamamlandığında:
- Siteniz şu adreste yayında olacak: `https://nefisyemekler.onrender.com`
- Her GitHub'a push attığınızda otomatik deploy olacak
- SSL sertifikası otomatik aktif

## Notlar

- **İlk açılış**: Free plan'da site 15 dakika kullanılmazsa uyur, ilk açılış 30 saniye sürebilir
- **Custom Domain**: Render ayarlarından kendi domain adresinizi bağlayabilirsiniz
- **Logs**: Hata olursa Logs sekmesinden kontrol edin

## Sorun mu var?

Eğer deploy sırasında hata alırsanız:
1. **Logs** sekmesini kontrol edin
2. Build script'in çalıştığından emin olun
3. Environment variables'ların doğru girildiğini kontrol edin
