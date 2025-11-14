# V2G Anomali Simülasyonu - Ubuntu Kurulum ve Kullanım Kılavuzu

Bu proje, **V2G "Enerji Yönü Aldatmacası" senaryosunu** (V2G Deşarj Anomalisi.pdf) Ubuntu üzerinde, **vcan** ve **Python** kullanarak simüle etmek için hazırlanmıştır.

Simülasyon, birbirinden bağımsız 3 Python betiği ve 1 HTML arayüzünden oluşur:

- `app.py` : Ana sunucu. Web arayüzünü sunar, buton komutlarını alır ve diğer betiklere iletir.
- `physical_layer.py` : Araç/Enerji Metresi simülatörü. Sürekli olarak `vcano0`'a "Şarj Oluyorum" (Import) CAN mesajı gönderir.
- `gateway_ids.py` : Gateway/Saldırgan simülatörü. `vcano0`'ı dinler, saldırı emri geldiğinde veriyi manipüle eder (Aldatmaca) ve arayüze raporlar. Yapay zeka eğitimi için `ai_training_data.csv` dosyasına loglama yapar.
- `index.html` : Web tarayıcınızda kontrol paneliniz.

---

## 1. Gerekli Paketlerin Kurulumu

```bash
sudo apt update
sudo apt install can-utils python3-pip -y
pip3 install Flask flask-socketio "python-can>=4.0" "socketIO-client-nexus>=0.7.6"
```

---

## 2. Sanal CAN Arayüzü (vcan) Oluşturma

```bash
sudo modprobe vcan
sudo ip link add dev vcano0 type vcan
sudo ip link set vcano0 up
```

Doğrulama:

```bash
ip a
```

---

## 3. Simülasyonu Çalıştırma (3 Terminal)

### Terminal 1: Ana Sunucu

```bash
python3 app.py
```

### Terminal 2: Fiziksel Katman

```bash
sudo python3 physical_layer.py
```

### Terminal 3: Gateway & IDS

```bash
sudo python3 gateway_ids.py
```

---

## 4. Web Arayüzü Kullanımı

Tarayıcıda açın:

```
http://127.0.0.1:5000
```

Arayüzden:

- OCPP 1.6 veya OCPP 2.0 seçin.
- **Simülasyonu Başlat** → Veri akışı başlar.
- **Saldırı Başlat** → Manipüle edilmiş Export verisi gönderilir.
- Grafiklerde Import–Export ayrımı görünür.
- IDS paneli: **ANOMALİ TESPİT EDİLDİ!**
- Tüm loglar `ai_training_data.csv` dosyasına yazılır.
- İsterseniz "Logları İndir" butonu ile indirebilirsiniz.

---

## Özet

- `app.py` → Web sunucusu  
- `physical_layer.py` → Araç simülatörü  
- `gateway_ids.py` → Gateway + Saldırgan + IDS  
- `vcano0` → Sanal CAN  
- `ai_training_data.csv` → Yapay zekâ veri seti  
