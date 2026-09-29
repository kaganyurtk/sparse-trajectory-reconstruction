# RQ1 nihai sonuç raporu

**Tarih:** 20 Eylül 2026  
**Durum:** Outer-validation ve tek-seferlik held-out test tamamlandı. RQ1 kapatıldı.

## Araştırma sorusunun cevabı

Sınırlı gerçek Falcon 9 gözlemleri altında kullanılan kinematik eşitsizlik kısıtı,
`0 <= dh/dt <= v` ve `v >= 0`, modelin fiziksel tutarlılığını güçlü biçimde artırmış;
ancak irtifa ve hızın önceden tanımlanmış birleşik tahmin hatasını iyileştirmemiştir.

**RQ1 hipotezi desteklenmemiştir.** `%5` gözlem oranında KC-NN hem outer-validation hem
held-out test makro ortalamasında NN'den daha kötü sonuç vermiştir.

## Doğrulayıcı sonuçların özeti

| Küme | KC-NN − NN ortalama birleşik fark | Medyan | KC-NN lehine uçuş | Uçuş-bootstrap %95 aralığı |
|---|---:|---:|---:|---:|
| Outer-validation | +0.016751 | +0.015992 | 0/6 | [+0.009015, +0.024728] |
| Held-out test | +0.018634 | +0.031494 | 1/6 | [-0.020757, +0.045011] |

Negatif fark KC-NN lehinedir. Test aralığı sıfırı içermektedir; altı uçuşluk bootstrap
betimseldir. Bununla birlikte validation ve test makro ortalamalarının yönü aynıdır.

## Held-out testte `%5` uçuş sonuçları

| Uçuş | NN birleşik hata | KC-NN birleşik hata | KC-NN − NN |
|---|---:|---:|---:|
| Intelsat 35e | 0.113894 | 0.161973 | +0.048078 |
| Iridium NEXT-5 | 0.224670 | 0.149446 | -0.075225 |
| SES-9 | 0.338075 | 0.393535 | +0.055460 |
| SpaceX CRS-11 | 0.150736 | 0.171240 | +0.020504 |
| SSO-A | 0.155988 | 0.188540 | +0.032552 |
| Thaicom-8 | 0.076771 | 0.107207 | +0.030437 |

KC-NN yalnız Iridium NEXT-5'te belirgin iyileşmiştir. Diğer beş uçuşta birleşik hata
artmıştır. Bu heterojenlik gizlenmemeli ve belirli araç/görev benzerliklerine ilişkin ileri
çalışma hipotezi olarak ele alınmalıdır; mevcut örnekle nedensel açıklama yapılamaz.

## Testte gözlem oranına göre ikincil sonuçlar

| Gözlem | NN h RMSE (m) | KC-NN h RMSE (m) | NN v RMSE (m/s) | KC-NN v RMSE (m/s) | Birleşik fark |
|---:|---:|---:|---:|---:|---:|
| %100 | 1506.34 | 1360.63 | 35.65 | 39.34 | -0.000832 |
| %50 | 1465.44 | 1344.74 | 33.42 | 38.85 | +0.003014 |
| %25 | 1537.97 | 1440.71 | 37.05 | 41.43 | +0.002440 |
| %10 | 1710.03 | 1614.37 | 38.43 | 45.17 | +0.006180 |
| %5 | 2304.55 | 1920.30 | 46.77 | 69.87 | +0.018634 |

Kısıt bütün test oranlarında irtifa RMSE'sini düşürmüş ve hız RMSE'sini artırmıştır. `%5`
koşulunda irtifa yaklaşık 384 m iyileşirken hız yaklaşık 23.10 m/s kötüleşmiştir. Birleşik
ölçütte net sonuç KC-NN aleyhinedir. `%100` birleşik fark KC-NN lehine fakat ihmal edilecek
kadar küçüktür; sınırlı-veri ana hipotezini desteklemez.

Test `%5` kinematik ihlal oranı NN için `0.4262`, KC-NN için `0.0612` olmuştur. Dolayısıyla
fiziksel uygunluk kazanımı validation'dan teste taşınmış, tahmin doğruluğu kazanımı taşınmamıştır.

## Yorum

Kullanılan eşitsizlik doğru fakat kaba bir fiziksel önbilgidir. Toplam hız, düşey hız değildir;
kısıt irtifa türevini makul bölgeye iterken hız profilini doğrudan açıklamamaktadır. Sonuçlar,
fiziksel kısıt eklemenin tek başına daha yüksek öngörü doğruluğunu garanti etmediğini gösterir.
Adaptif lambda, uçuş-yolu açısı veya dinamik denklemler ancak ayrı ve açıkça keşifsel bir
çalışmada incelenebilir; mevcut doğrulayıcı RQ1 sonucunun parçası değildir.

## Denetim

- 48 inner tarama + 50 final refit tamamlandı.
- Testte yalnız dondurulmuş 50 final model değerlendirildi; yeniden eğitim veya tuning yapılmadı.
- Altı test uçuşu yalnız bir kez açıldı.
- 50 test tahmini ağırlıklardan yeniden oynatıldı; maksimum fark `0.0`.
- Birincil test analizi bağımsız yeniden hesaplamayla birebir eşleşti.
- Test manifest fingerprint'i: `89728925fd31f436dbb9438556157e7a030ce7ee881b557cdad434257b2fa64b`.
- Orijinal test summary içindeki yalnızca metinsel estimand etiketi hatası ayrı kayıtta belgelendi;
  sayısal sonuç değişmedi.

Bu sonuçlarla RQ1 bilimsel ve teknik olarak kapanmıştır. Sonraki doğrulayıcı çalışma RQ2'dir.
