# Test çıktı düzeltme kaydı

`outputs/test_v2/summary.json` dosyasındaki `primary_analysis.estimand` metni, ortak analiz
fonksiyonu nedeniyle yanlışlıkla “outer-validation” olarak etiketlenmiştir. Hesaplanan satırlar,
uçuş kimlikleri ve sayısal sonuçlar altı held-out test uçuşuna aittir.

Orijinal dosya denetim izi olarak değiştirilmedi. `summary_corrected.json` yalnız bu etiketi
“held-out test” olarak düzeltir ve bir düzeltme kaydı ekler. Hiçbir sayı, model, tahmin,
hiperparametre veya analiz kuralı değiştirilmemiştir.

