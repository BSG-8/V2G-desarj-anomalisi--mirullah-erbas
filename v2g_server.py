# v2g_server.py: Ana Flask & SocketIO Sunucusu
# Tüm bileşenler arasındaki iletişimi yönetir.
# Terminal 1'de çalıştırılacak: python3 v2g_server.py

from flask import Flask, render_template, send_from_directory
from flask_socketio import SocketIO, emit
import os

# Arayüz dosyalarının bulunduğu klasörün adını 'web_interface' olarak ayarla
app = Flask(__name__, template_folder='web_interface')
app.config['SECRET_KEY'] = 'secret-key-v2g!'
socketio = SocketIO(app, cors_allowed_origins="*")

print("Ana Sunucu (v2g_server.py) başlatılıyor...")

# Ana arayüz (dashboard.html) sayfası
@app.route('/')
def index():
    print("Arayüz (web_interface/dashboard.html) sunuluyor...")
    return render_template('dashboard.html')

# Log indirme yolu (route)
@app.route('/download-logs')
def download_logs():
    """
    Kök dizinde bulunan 'v2g_training_log.csv'
    dosyasını kullanıcıya indirme olarak gönderir.
    """
    try:
        log_directory = app.root_path
        log_filename = 'v2g_training_log.csv' # DEĞİŞTİRİLDİ
        print(f"{log_filename} dosyası indirme için gönderiliyor...")
        return send_from_directory(log_directory, log_filename, as_attachment=True)
    except FileNotFoundError:
        print(f"Hata: Log dosyası '{log_filename}' bulunamadı.")
        return "Log dosyası henüz oluşturulmamış veya bulunamadı.", 404
    except Exception as e:
        print(f"Dosya gönderme hatası: {e}")
        return str(e), 500


# Arayüzden (tarayıcı) gelen simülasyon kontrol komutları
@socketio.on('control_signal')
def handle_control_signal(data):
    """
    Arayüzden gelen 'Simülasyonu Başlat/Durdur' veya 'Saldırı Başlat/Durdur'
    sinyallerini alır ve tüm bağlı istemcilere (gateway_monitor.py) yayınlar.
    """
    print(f"Arayüzden sinyal alındı: {data}")
    emit('simulation_control', data, broadcast=True)

# Protokol seçimi olayı
@socketio.on('set_protocol')
def handle_set_protocol(data):
    """
    Arayüzden gelen 'OCPP 1.6 / 2.0' seçimini alır
    ve 'gateway_monitor.py' betiğine yayınlar.
    """
    print(f"Protokol değiştirildi: {data}")
    emit('protocol_control', data, broadcast=True)


# Gateway'den (gateway_monitor.py) gelen veri
@socketio.on('gateway_data')
def handle_gateway_data(data):
    """
    gateway_monitor.py'den gelen işlenmiş veriyi alır
    ve arayüzdeki (dashboard.html) istemcilere iletir.
    """
    emit('update_data', data, broadcast=True)

@socketio.on('connect')
def on_connect():
    print('Bir istemci bağlandı (Tarayıcı veya Gateway).')

@socketio.on('disconnect')
def on_disconnect():
    print('Bir istemcinin bağlantısı kesildi.')

if __name__ == '__main__':
    print("Sunucu http://127.0.0.1:5000 adresinde çalışıyor.")
    print("Lütfen Terminal 2'de 'sudo python3 vehicle_simulator.py' çalıştırın.")
    print("Lütfen Terminal 3'de 'sudo python3 gateway_monitor.py' çalıştırın.")
    socketio.run(app, host='0.0.0.0', port=5000)
