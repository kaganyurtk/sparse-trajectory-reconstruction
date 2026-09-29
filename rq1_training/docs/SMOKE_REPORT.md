# RQ1 NN–KC-NN uygulama ve smoke-test raporu

**Tarih:** 20 Eylül 2026  
**Kapsam:** Kod doğrulaması; bilimsel deney sonucu değildir.

## Tamamlanan işler

- Veri-güdümlü NN ve kinematik eşitsizlik kısıtlı KC-NN aynı PyTorch kod yolunda uygulandı.
- İki model 8 girdili, 32×32 `tanh` ağ ve iki çıktı kullanıyor.
- Kinematik terim fiziksel birimlerde otomatik türevlemeyle hesaplanıyor.
- `dh/dt = v` eşitliği kullanılmıyor; `0 <= dh/dt <= v` ve `v >= 0` ihlalleri cezalandırılıyor.
- Sabit 22 inner-fit / 6 inner-validation / 6 outer-validation ayrımı uygulandı.
- Outer-validation'ın ayar, checkpoint, epoch veya kinematik ağırlık seçiminde kullanılması engellendi.
- `%5` birleşik standardize outer-validation farkı birincil sonuç olarak kodlandı; seed'ler uçuş içinde ortalanıyor ve uçuş-bazlı bootstrap kullanılıyor.
- Kinematik ağırlık yalnız inner-fit başlangıç gradyan normlarından hesaplandı: `33.6822579609781`.
- Tam 98 koşuluk inner-tarama/final-refit orkestrasyonu yazıldı fakat başlatılmadı.
- Kesilen tam çalışma, tamamlanmış `result.json` koşularını yeniden eğitmeden sürdürebilir.
- Resume öncesinde run fingerprint'i ve ağırlık SHA-256 özeti doğrulanır; çelişkili çıktı reddedilir.

## Veri sızıntısı önlemi

Deney girdisi `combined.csv` kullanmıyor. Yalnızca 28 train ve 6 validation uçuşunun
ayrı CSV dosyaları çalışma alanına alındı. Altı test uçuşu indirilmedi. Loader, adı veya
partition değeri test kümesine ait bir dosya görürse hata veriyor.

## Otomatik kontroller

On üç kontrolün tamamı geçti:

1. Otomatik türev sonlu-fark türeviyle uyuşuyor.
2. Normalize zaman için `1/120` zincir-kuralı katsayısı doğru.
3. Veri 28 train / 6 outer-validation ve toplam 34 uçuş dosyası içeriyor.
4. Ölçekleyiciler önceki dondurulmuş değerlerle uyuşuyor.
5. %100–%5 maskeleri beklenen boyutlarda ve iç içe.
6. Seyrek hedef seçimi inner-fit uçuşlarının dışına çıkmıyor.
7. Eş seed iki yöntemde aynı başlangıç ağırlıklarını üretiyor.
8. Test uçuşu loader tarafından reddediliyor.
9. Önceden ilan edilen benzersiz eğitim bütçesi tam 98 koşu olarak doğrulanıyor.
10. Kinematik ağırlık sıfırken KC-NN kod yolu NN ile aynı optimizer güncellemesini üretiyor.
11. 22/6 inner ayrımı ile altı outer-validation kimliği doğrulanıyor.
12. Train-only gradyan kalibrasyonu sonlu ve önceden tanımlı sınırlar içinde sonuç veriyor.
13. Kilitli manifest değişikliği reddediyor; birincil analiz seed'leri uçuş içinde ortalıyor.

## Smoke testi

- Maske: %5; 22 inner-fit uçuşunda 132 gözlem.
- Seed: 11.
- Süre: 5 epoch.
- Koşular: bir NN ve bir KC-NN.
- Eş başlangıç doğrulandı.
- Checkpoint/evaluation: altı inner-validation uçuşu; outer-validation seçime girmedi.
- Test trajectory girdisi: 0.
- İki kaydedilmiş model NPZ ağırlıklarından bağımsız yeniden oynatıldı.
- Maksimum yeniden oynatma tahmin farkı: 0.0.

Beş epoch'luk değerler yakınsamış model sonucu değildir ve NN–KC-NN üstünlüğü hakkında
yorumlanmamalıdır. Bu smoke testin tek amacı veri, türev, eğitim, checkpoint, kayıt ve
yeniden oynatma yollarının uçtan uca çalıştığını göstermektir.

## Sonraki kapı

Tam 98 koşu başlamadan önce kod/protokol son incelemesi yapılmalı, ardından dosya özetleri
dondurulmalıdır. Test kümesi yöntem ve ayarlar sabitlenene kadar kapalı kalacaktır.
