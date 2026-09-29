# SpaceX RQ1 — Kinematik Kısıtlı Sinir Ağı Deney Protokolü

**Sürüm:** 2.0 — iç/dış doğrulama ve denetim güvenliği revizyonu  
**Tarih:** 20 Eylül 2026  
**Durum:** Bu dosya onaylandıktan ve uygulama doğrulama kapıları geçildikten sonra model eğitimi başlayabilir. Test kümesi kapalıdır.

## 1. Araştırma sorusu

Sınırlı gerçek uçuş gözlemi altında, fiziksel olarak geçerli bir kinematik kısıt Falcon 9'un 0–120 saniyelik irtifa ve hız eğrilerinin görülmemiş uçuşlara genellenmesini, aynı mimari ve aynı ayarlama bütçesine sahip veri-güdümlü bir sinir ağına göre iyileştirir mi?

Ana beklenti, kısıtın yararının gözlem oranı azaldıkça artmasıdır. Sonuç, yalnızca ortalama hata üzerinden değil, uçuş-bazlı tutarlılık üzerinden de değerlendirilecektir.

## 2. Dondurulmuş veri kapsamı

- 40 Falcon 9 uçuşu; uçuş başına T+0–T+120 s ve 1 Hz olmak üzere 121 nokta.
- Toplam 4.840 işlenmiş satır.
- Sabit ayrım: 28 train / 6 validation / 6 test.
- Eğitim gözlem oranları: %100, %50, %25, %10 ve %5.
- Oranlar mevcut iç içe maskeleri kullanır; her uçuşun başlangıç ve bitiş noktaları korunur.
- 28 train uçuşu, hedef eğrilerine veya model sonuçlarına bakılmadan metadata çeşitliliğiyle sabit 22 inner-fit / 6 inner-validation olarak ayrılmıştır. Ayrım `outputs/rq1_kinematic_experiment/inner_split.json` dosyasındadır.
- Mevcut 6 validation uçuşu **outer-validation** olarak adlandırılır; hiperparametre, checkpoint, epoch veya \(\lambda_{kin}\) seçimine girmez. Yalnızca dondurulmuş yöntemlerin değerlendirilmesinde kullanılır.
- Test uçuşlarının hedef eğrileri yöntem, kod, hiperparametreler ve raporlama şablonu dondurulana kadar hiçbir girdiye yüklenemez.
- `analysed.json`, MECO, Max-Q, mission/flight_id ve validation başlangıç irtifası model girdisi değildir.

Kaynak kayıtlar:

- `outputs/rq1_preprocessing_pipeline/split_config.json`
- `outputs/rq1_preprocessing_pipeline/processed/dataset_summary.json`
- `outputs/rq1_preprocessing_pipeline/processed/flight_metadata.csv`
- `outputs/rq1_preprocessing_pipeline/processed/fractions/`

## 3. Karşılaştırılacak yöntemler

### 3.1 Veri-güdümlü referans ağ (NN)

- Girdiler: normalize zaman + Falcon 9 Block + payload.
- Kodlama: `time_normalized`; eğitimden öğrenilen medyan ve standart sapmayla payload standardizasyonu; payload eksik göstergesi; Block 1–5 one-hot sütunları.
- Mimari: iki gizli katman, 32×32, `tanh`; iki çıktı: irtifa ve hız.
- Hedefler yalnızca train bölümünden öğrenilen ortalama ve standart sapmayla standardize edilir.

### 3.2 Kinematik kısıtlı ağ (KC-NN)

KC-NN, NN ile aynı girdileri, katmanları, aktivasyonu, çıktı parametrizasyonunu, veri kaybını, optimizer ailesini, eğitim maskesini ve seed'i kullanır. Tek yöntem farkı aşağıdaki kinematik ceza terimidir.

## 4. Fiziksel kısıtın doğru tanımı

Telemetry verisindeki `speed_m_s` düşey hız değil, hız büyüklüğüdür. Bu nedenle

\[
\frac{d h}{dt}=v
\]

eşitliği genel olarak doğru değildir. Doğru ilişki, uçuş-yolu açısı \(\gamma\) ile

\[
\frac{d h}{dt}=v\sin\gamma
\]

biçimindedir. Veri kümesinde güvenilir \(\gamma\) bulunmadığından, deneyde yanlış eşitlik dayatılmayacaktır. Erken yükseliş penceresi için kullanılacak fiziksel olarak güvenli kısıt:

\[
0 \leq \frac{d\hat h}{dt} \leq \hat v, \qquad \hat v \geq 0.
\]

Model standardize irtifa çıktısı \(\tilde h\), standardize hız çıktısı \(\tilde v\) ve normalize zaman \(\tau=t/120\) ürettiğinde fiziksel birimlerde

\[
\hat h=\mu_h+\sigma_h\tilde h,\qquad
\hat v=\mu_v+\sigma_v\tilde v,
\]

\[
q=\frac{d\hat h}{dt}=\frac{\sigma_h}{120}\frac{d\tilde h}{d\tau}
\]

hesaplanır. Türev otomatik türevleme ile alınır. Boyutsuz kinematik kayıp:

\[
L_{kin}=\operatorname{mean}\left[
\operatorname{ReLU}\left(-\frac{q}{\sigma_v}\right)^2+
\operatorname{ReLU}\left(\frac{q-\hat v}{\sigma_v}\right)^2+
\operatorname{ReLU}\left(-\frac{\hat v}{\sigma_v}\right)^2
\right].
\]

Bu tanım, gözlenmeyen bir uçuş-yolu açısını uydurmaz ve toplam hız ile düşey hızı karıştırmaz.

## 5. Kayıp fonksiyonları

Her gözlenen eğitim noktasında standardize hedefler için

\[
L_{data}=\frac{1}{2}\left[
\operatorname{MSE}(\tilde h,\tilde h_{obs})+
\operatorname{MSE}(\tilde v,\tilde v_{obs})
\right].
\]

- NN: \(L=L_{data}\).
- KC-NN: \(L=L_{data}+L_{kin}\).
- Kinematik ağırlık validation ile taranmaz. Eğitim başlamadan, %100 inner-fit verisinde seed 11, 29 ve 47 başlangıçlarında gradyan-norm dengeleme kuralıyla bir kez hesaplanır: \(r=\operatorname{median}(\|\nabla L_{kin}\|/\|\nabla L_{data}\|)\), \(\lambda_{kin}=\operatorname{clip}(1/r,0.01,100)\). \(r=0\) veya sonlu değilse \(\lambda_{kin}=1\) kullanılır ve durum işaretlenir. Sonuç görülerek değiştirilmez.
- L2/weight-decay, aşağıdaki ortak hiperparametre bütçesinin parçasıdır.

Kinematik kayıp, inner taramada 22 inner-fit; final refit aşamasında 28 train uçuşunun 121 zaman koordinatında hesaplanır. Seyrek maskede bulunmayan irtifa veya hız değerleri okunmaz; bu noktaların yalnızca zamanı ve ilgili fit bölümünün metadata girdileri kullanılır. Böylece collocation noktaları etiket sızıntısı oluşturmaz.

## 6. Uygulama eşitliği

Mevcut seçilmiş ağ scikit-learn ile eğitilmiştir; özel türev kaybını aynı estimator içinde uygulamak mümkün değildir. Bu nedenle yeni karşılaştırmada iki yöntem de tek bir otomatik-türevleme çatısında yeniden uygulanacaktır. Tarihsel scikit-learn sonucu mimari ve girdi seçiminin gerekçesidir; yeni deneyde sayısal kontrol kolu olarak doğrudan yeniden kullanılmaz.

İki yöntem için aşağıdakiler birebir aynı olacaktır:

- 32×32 `tanh` mimarisi ve parametre başlangıç kuralı,
- veri sırası ve seed,
- optimizer: Adam,
- inner taramada maksimum 1.000 epoch,
- yalnız inner-validation üzerinde her 10 epoch'ta kontrol ve 25 kontrolde iyileşme yoksa erken durdurma,
- final refit aşamasında outer-validation checkpoint için kullanılmaz; her yöntemin epoch sayısı, kazanan ayarın üç inner tarama seed'indeki en iyi epoch'larının medyanıdır,
- inner checkpoint seçim skoru,
- veri maskeleri ve hedef ölçekleyicileri,
- float hassasiyeti ve deterministik çalışma ayarları.

Bir seed içinde NN ve KC-NN aynı başlangıç ağırlıklarından başlatılır. Böylece karşılaştırma eşleştirilmiş olur.

## 7. Eşit ayarlama bütçesi

Mimari ve girdiler dondurulmuştur. Yalnızca her iki yöntemde ortak olan öğrenme hızı ve weight-decay taranır:

| Parametre | Adaylar |
|---|---|
| Öğrenme hızı | 0.0003, 0.001 |
| Weight decay | 0, 0.000001, 0.00001, 0.0001 |

Bu, yöntem başına 8 aday ayardır. Her aday yalnızca %100 maskesinde 22 inner-fit uçuşuyla eğitilir ve 6 inner-validation uçuşunda seed 11, 29 ve 47 ile seçilir:

- NN: 8 × 3 = 24 tarama eğitimi.
- KC-NN: 8 × 3 = 24 tarama eğitimi.

Her yöntemin kazanan ortak ayarı, üç seed'in ortalama inner-validation seçim skoruyla belirlenir; eşitlikte daha yüksek weight decay, ardından daha düşük öğrenme hızı seçilir. Yönteme özel ek validation araması yapılmaz. KC-NN'nin \(\lambda_{kin}\) değeri yalnız Bölüm 5'teki train-only gradyan kuralıyla belirlenir.

Seçimden sonra her yöntemin final epoch sayısı üç tarama seed'indeki kazanan checkpoint epoch'larının medyanı olarak kilitlenir. Kazanan ayarlar ve bu epoch sayılarıyla 28 train uçuşunun tamamında seed 11, 29, 47, 71 ve 97 için baştan refit yapılır. Outer-validation sonuçlarına bakılarak hiçbir ayar değiştirilmez.

Seçilmiş ayarlar ve epoch sayıları değiştirilmeden %100, %50, %25, %10 ve %5 maskelerinde beş seed'in tamamıyla final refit yapılır. Planlanan azami benzersiz eğitim sayısı:

\[
48\;\text{inner tarama}+50\;\text{final refit}=98.
\]

Başarısız/nümerik olarak taşan koşular saklanır ve başarısız olarak raporlanır; sonuç görüldükten sonra yerine yeni aday eklenmez.

## 8. Model seçimi ve metrikler

Inner checkpoint ve hiperparametre seçim skoru, eğitim hedef standart sapmalarına bölünmüş irtifa ve hız RMSE'lerinin hedefler ve altı inner-validation uçuşu üzerindeki eşit ağırlıklı ortalamasıdır. Outer-validation bu seçime girmez.

**Birincil doğrulayıcı sonuç**, %5 gözlem oranında outer-validation uçuşları için önce beş seed üzerinde ortalanan, sonra uçuşlar üzerinde makro ortalaması alınan birleşik standardize hatanın KC-NN eksi NN farkıdır. Negatif değer KC-NN lehinedir. Bu sonuç diğer oranlara bakılarak değiştirilemez.

Birincil sonuç için uçuş birimi korunur: her uçuşta beş seed ortalanır; altı eşleştirilmiş uçuş farkının ortalaması, medyanı, KC-NN lehine işaret sayısı ve 10.000 tekrar/seed 20260920 ile uçuş-bazlı bootstrap %95 aralığı verilir. Altı uçuş nedeniyle bootstrap aralığı betimseldir; seed'ler bağımsız örnek veya güven aralığı birimi değildir.

İkincil rapor metrikleri:

- Uçuş başına irtifa RMSE (m), ardından uçuşlar üzerinde makro ortalama.
- Uçuş başına hız RMSE (m/s), ardından uçuşlar üzerinde makro ortalama.
- %10–%100 oranlarında birleşik standardize hata eğrisi.
- Aynı seed için KC-NN eksi NN farkı; negatif değer KC-NN lehinedir.

İkincil metrikler:

- İrtifa ve hız MAE.
- Kinematik ihlal oranı: \(q<0\), \(q>\hat v\) veya \(\hat v<0\) olan zaman noktalarının oranı.
- İhlal büyüklüğü.
- Eğitim süresi ve seçilen epoch.

Her oran için beş seed ayrı ayrı gösterilir; yalnızca ortalama eğri veya ensemble sonucu tek modelmiş gibi sunulmaz. Çoklu ikincil sonuçlardan biri birincil sonuç gibi sunulmaz.

## 9. Uçuş-bazlı sağlamlık ve bilinen sınırlama

Outer-validation sonuçları aşağıdaki üç görünümle birlikte verilir:

1. Altı uçuşun tamamı.
2. GPS III SV01 tek başına.
3. Kalan beş validation uçuşunun makro ortalaması ve tek tek değerleri.

Önceki toplam iyileşmenin büyük kısmı GPS III SV01'den gelirken diğer beş uçuşta bozulma görülmüştür. Yeni yöntemin ortalama kazanımı yine tek bir uçuş tarafından sürüklenirse bu durum açıkça ana sonuçta yazılacaktır; dipnota gömülmeyecektir.

Outer-validation geçmiş ablation çalışmalarında görülmüş olduğundan tamamen bağımsız test değildir; ancak yeni KC-NN hiperparametre ve checkpoint seçiminden çıkarılmıştır. Seed'ler yeni uçuş değildir ve güven aralığı yerine geçmez.

## 10. Doğrulama kapıları

Herhangi bir tam deneyden önce aşağıdaki kontroller geçmelidir:

- Girdi boyutu ve parametre sayısı iki yöntemde aynıdır.
- NN ve KC-NN, aynı seed'de bit düzeyinde aynı başlangıç ağırlıklarına sahiptir.
- \(\lambda_{kin}=0\) iken KC-NN kod yolu NN ile aynı tahmini üretir.
- Analitik türev, sonlu farkla küçük bir sentetik ağ üzerinde tolerans içinde uyuşur.
- Fiziksel birim dönüşümünde \(1/120\) zincir kuralı katsayısı doğrulanır.
- Seyrek maskeler dışındaki train hedefleri eğitim kaybına girmez.
- Ölçekleyiciler yalnızca train bölümünden öğrenilir.
- Inner-validation hedefleri gradyana girmez; yalnızca inner checkpoint/metrik hesabında kullanılır.
- Outer-validation hedefleri hiperparametre, epoch, checkpoint veya \(\lambda_{kin}\) seçimine girmez.
- Başlangıçta veri ve kinematik kayıpların değerleri ile gradyan normları kaydedilir; \(\lambda_{kin}\) yalnız train-only kuralıyla hesaplanır.
- Test trajectory dosyalarının eğitim ve validation girdilerindeki sayısı sıfırdır.
- Kaydedilen ağırlıklardan bağımsız ileri geçiş, saklanan tahminlerle tolerans içinde aynıdır.
- Tahmin kaydı `flight_id`, `mission`, `time_s`, gerçek irtifa/hız ve tahminleri birlikte içerir.
- Protokol, kod, inner split, metadata ve maskelerin SHA-256 özetleri run manifestine yazılır.
- Mevcut koşu yalnız config, kod, protokol, veri, maske ve split fingerprint'i birebir eşleşir ve ağırlık hash'i doğrulanırsa resume edilir; aksi durumda çalışma hata ile durur.

## 11. Test kümesini açma kuralı

Test değerlendirmesi ancak şu koşulların tamamı sağlandıktan sonra yapılabilir:

1. 98 koşuluk inner-tarama/final-refit planı tamamlanmış veya önceden tanımlı bir teknik başarısızlıkla kapanmıştır.
2. Her iki yöntemin ayarları ve checkpoint kuralları dondurulmuştur.
3. Validation raporu; GPS III SV01 ve diğer beş uçuş ayrımı dahil tamamlanmıştır.
4. Tüm doğrulama kapıları geçmiştir.
5. Kod, protokol ve veri özetleri değişmez manifestte kayıtlıdır.

Testte altı uçuş yalnızca bir kez değerlendirilir. Test sonucu görüldükten sonra model, kısıt, hiperparametre veya ön işleme değiştirilmez. Bir hata saptanırsa test sonucu geçersiz olarak işaretlenir; düzeltme ve yeniden değerlendirme gerekçesi eksiksiz kaydedilir.

## 12. Yorum sınırları

- Çalışma yalnızca Falcon 9'un 0–120 s erken yükseliş penceresini kapsar; tam uçuş, apogee veya yörünge tahmini değildir.
- Kullanılan kısıt temel kinematik eşitsizliktir. İtki, kütle kaybı, sürükleme ve atmosfer modeli içermediği için yöntem, dar anlamda tam dinamik PINN olarak sunulmamalıdır. En doğru adlandırma **kinematik kısıtlı sinir ağı (KC-NN)** veya **physics-informed neural network with kinematic inequality constraints** ifadesidir.
- Toplam hız, düşey hız değildir. \(dh/dt=v\) eşitliği sonuç daha iyi görünsün diye kullanılmayacaktır.
- İyileşme yalnız RMSE azalmasıyla değil, uçuşlar arasında tutarlılık ve kinematik ihlal azalmasıyla birlikte yorumlanacaktır.

## 13. Deney öncesi değişiklik politikası

İlk eğitim başlamadan önce protokoldeki bilimsel veya teknik bir hata düzeltilebilir; sürüm artırılır ve değişiklik kaydı tutulur. İlk eğitimden sonra sonuçlara bakılarak yapılan hiçbir değişiklik aynı doğrulayıcı deneyin parçası sayılamaz; ayrı ve açıkça keşifsel bir deney olarak kaydedilir.
