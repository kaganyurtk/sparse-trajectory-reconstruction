# RQ1 tek-seferlik test değerlendirme protokolü

**Dondurma tarihi:** 20 Eylül 2026  
**Durum:** Test hedefleri okunmadan önce donduruldu.

1. Test uçuşları sabittir: `ses_9`, `thaicom_8`, `intelsat_35e`, `spacex_crs_11`,
   `iridium_next_5`, `sso_a`; her biri 0–120 s ve 121 satırdır.
2. Hiçbir model yeniden eğitilmeyecek. `full_v2` içindeki 50 final model aynen kullanılacak:
   beş gözlem oranı × iki yöntem × beş seed.
3. Encoder 28 train uçuşundan dondurulmuş `full_v2/run_manifest.json` değerleriyle birebir
   uyuşmalıdır. Model ağırlıklarının SHA-256 özetleri `result.json` kayıtlarıyla doğrulanır.
4. Birincil test sonucu `%5` gözlem oranında, her test uçuşunda önce beş seed üzerinde
   ortalanan birleşik standardize hatanın `KC-NN − NN` farkıdır. Negatif KC-NN lehinedir.
5. Altı uçuş farkının ortalaması, medyanı, KC-NN lehine işaret sayısı ve uçuş-bazlı
   10.000 tekrar/seed `20260920` bootstrap %95 aralığı raporlanır. Aralık betimseldir.
6. İkincil sonuçlar: tüm oranlarda uçuş-makro irtifa/hız RMSE ve birleşik hata; uçuş-bazlı
   sonuçlar; kinematik ihlal oranı. Seed'ler bağımsız örnek sayılmaz.
7. Testte görülen sonuca göre model, kısıt, lambda, epoch, hiperparametre, veri işleme veya
   metrik değiştirilemez. Teknik hata varsa sonuç geçersiz işaretlenir ve gerekçe kaydedilir.
8. Test girdileri, evaluator kodu, bu protokol, final summary ve kullanılan 50 ağırlığın
   hash'leri test manifestine yazılır. Tahminler kimlik, zaman, gerçek ve tahmin sütunlarıyla
   saklanır; tüm 50 model bağımsız yeniden oynatılır.
