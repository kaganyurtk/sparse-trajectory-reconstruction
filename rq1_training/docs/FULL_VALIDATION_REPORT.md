# RQ1 NN–KC-NN tam outer-validation raporu

**Tarih:** 20 Eylül 2026  
**Protokol:** 2.0  
**Durum:** 48 inner tarama + 50 final refit tamamlandı. Test kümesi kapalıdır.

## Ana sonuç

Önceden tanımlanan birincil sonuç, `%5` gözlem oranında uçuş başına önce beş seed üzerinde
ortalama alınan birleşik standardize hatanın `KC-NN − NN` farkıdır. Negatif değer KC-NN
lehinedir.

- Ortalama fark: **+0.0167513**
- Medyan fark: **+0.0159916**
- Uçuş-bazlı bootstrap %95 aralığı: **[+0.0090154, +0.0247281]**
- KC-NN lehine uçuş: **0/6**

Dolayısıyla doğrulayıcı hipotez desteklenmedi. `%5` koşulunda KC-NN birleşik hata bakımından
NN'den daha kötüydü ve fark altı outer-validation uçuşunun tamamında aynı yöndeydi. Bootstrap
aralığı altı uçuş nedeniyle betimseldir; seed'ler bağımsız örnek olarak kullanılmamıştır.

## Uçuş-bazlı `%5` farkları

| Uçuş | NN | KC-NN | KC-NN − NN |
|---|---:|---:|---:|
| EchoStar 23 | 0.111567 | 0.138696 | +0.027128 |
| GPS III SV01 | 0.098951 | 0.106918 | +0.007967 |
| Jason-3 | 0.514890 | 0.528352 | +0.013463 |
| SES-11 | 0.122906 | 0.153247 | +0.030341 |
| SpaceX CRS-14 | 0.182414 | 0.200935 | +0.018521 |
| SpaceX CRS-8 | 0.176660 | 0.179747 | +0.003088 |

GPS III SV01 farkı `+0.007967`; kalan beş uçuşun ortalama farkı `+0.018508` oldu. Önceki
ablation sonucundaki gibi GPS III SV01'in toplam iyileşmeyi sürüklemesi burada görülmedi;
çünkü bu deneyde hiçbir uçuşta birleşik KC-NN iyileşmesi yoktur.

## Gözlem oranına göre ikincil sonuçlar

Değerler beş seed ve altı outer-validation uçuşu üzerinde makro ortalamadır.

| Gözlem | NN irtifa RMSE (m) | KC-NN irtifa RMSE (m) | NN hız RMSE (m/s) | KC-NN hız RMSE (m/s) | Birleşik fark |
|---:|---:|---:|---:|---:|---:|
| %100 | 1247.77 | 1137.64 | 59.65 | 62.83 | -0.000013 |
| %50 | 1271.91 | 1156.97 | 59.75 | 63.28 | +0.000307 |
| %25 | 1290.57 | 1232.63 | 61.16 | 62.69 | -0.000238 |
| %10 | 1485.96 | 1421.62 | 63.90 | 67.48 | +0.002674 |
| %5 | 2148.51 | 1773.23 | 67.05 | 88.68 | +0.016751 |

KC-NN irtifa RMSE'sini bütün oranlarda düşürdü; ancak hız RMSE'sini bütün oranlarda artırdı.
Özellikle `%5` koşulunda yaklaşık 375 m irtifa kazanımı, yaklaşık 21.63 m/s hız kaybını
telafi etmedi. Bu nedenle yalnız irtifa metriğine bakarak yöntem başarılı ilan edilemez.

Kinematik ihlal oranı `%5` koşulunda NN için `0.4380`, KC-NN için `0.0672` oldu. Kısıt
fiziksel tutarlılığı belirgin biçimde artırdı, fakat önceden tanımlı tahmin doğruluğu
ölçütünü iyileştirmedi.

## Seçilen ayarlar

| Yöntem | Öğrenme hızı | Weight decay | Final epoch |
|---|---:|---:|---:|
| NN | 0.001 | 0.0001 | 560 |
| KC-NN | 0.001 | 0.0001 | 400 |

Kinematik ağırlık yalnız inner-fit başlangıç gradyanlarından hesaplandı:
`lambda_kin = 33.6822579609781`.

## Denetim sonucu

- 98/98 benzersiz koşu tamamlandı.
- 98 ağırlık dosyası ve 98 tahmin dosyası doğrulandı.
- 98 model kaydedilmiş ağırlıklardan yeniden oynatıldı; maksimum tahmin farkı `0.0`.
- 45 dondurulmuş girdi dosyasının boyutu ve SHA-256 özeti doğrulandı.
- Birincil analiz bağımsız yeniden hesaplamayla birebir eşleşti.
- Outer-validation seçim amacıyla kullanılmadı.
- Test trajectory girdisi: `0`.

Bu rapor test sonucu değildir. Protokoldeki test-açma kapısının diğer raporlama ve dondurma
koşulları ayrıca değerlendirilmeden test kümesi açılmamalıdır.
