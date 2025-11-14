# gateway_monitor.py: Gateway & IDS Simülatörü
# 'vcano0'ı dinler, veriyi işler, saldırı uygular, IDS tespiti yapar ve sunucuya (v2g_server.py) raporlar.
# Terminal 3'de çalıştırılacak: sudo python3 gateway_monitor.py

import can
import time
import sys
import csv
import socketio

# Global durum değişkenleri
simulation_active = False
attack_active = False
PROTOCOL_VERSION = '1.6'

# --- AI Veri Seti için CSV Loglama ---
log_filename = 'v2g_training_log.csv' # DEĞİŞTİRİLDİ
try:
    log_file = open(log_filename, 'w', newline='', encoding='utf-8')
    writer = csv.writer(log_file)
    writer.writerow([
        'timestamp',
        'can_direction',
        'can_power_w',
        'can_soc_percent',
        'ocpp_reported_direction',
        'ocpp_reported_power_w',
        'ids_decision',
        'label',
        'protocol'
    ])
    print(f"Yapay zeka için log dosyası '{log_filename}' oluşturuldu.")
except IOError as e:
    print(f"Log dosyası açılamadı: {e}. Lütfen izinleri kontrol edin.")
    sys.exit(1)

# --- SocketIO İstemcisi (Ana Sunucuya bağlanmak için) ---
sio = socketio.Client()

@sio.event
def connect():
    print("Ana sunucuya (v2g_server.py) başarıyla bağlandım.")

@sio.event
def connect_error(data):
    print(f"Bağlantı hatası: {data}. 'v2g_server.py' çalışıyor mu?") # DEĞİŞTİRİLDİ

@sio.event
def disconnect():
    print("Sunucuyla bağlantı kesildi.")

@sio.on('simulation_control')
def on_simulation_control(data):
    global simulation_active, attack_active
    
    if data['type'] == 'simulation':
        simulation_active = data['active']
        status = "BAŞLATILDI" if simulation_active else "DURDURULDU"
        print(f"Simülasyon durumu: {status}")
        
    elif data['type'] == 'attack':
        attack_active = data['active']
        status = "AKTİF" if attack_active else "DEAKTİF"
        print(f"!!! SALDIRI DURUMU: {status} !!!")

@sio.on('protocol_control')
def on_protocol_control(data):
    global PROTOCOL_VERSION
    if 'protocol' in data:
        PROTOCOL_VERSION = data['protocol']
        print(f"--- Simülasyon protokolü {PROTOCOL_VERSION} olarak ayarlandı. ---")


# --- CAN-bus Dinleyicisi ---
def run_gateway_listener():
    try:
        bus = can.interface.Bus(channel='vcano0', interface='socketcan')
    except OSError:
        print("vcano0 arayüzü bulunamadı.")
        print("Lütfen önce 'sudo ip link set vcano0 up' komutunu çalıştırdığınızdan emin olun.")
        return

    print("Gateway (Logger) çalışıyor... vcano0 dinleniyor.")
    
    for msg in bus:
        if not simulation_active:
            time.sleep(0.1)
            continue
            
        if msg.arbitration_id == 0x102:
            timestamp = time.time()
            
            # --- 1. Fiziksel Katman Verisini Oku (CAN) ---
            direction_code = msg.data[0]
            physical_power_w = (msg.data[1] << 8) | msg.data[2]
            physical_soc = msg.data[3]
            physical_direction = 'Import' if direction_code == 1 else 'Export'

            # --- 2. Gateway Katmanı (Saldırı Mantığı) ---
            label = 'normal'
            
            if attack_active and physical_direction == 'Import':
                reported_direction = 'Export'
                reported_power_w = 10000
                label = 'anomaly'
            else:
                reported_direction = physical_direction
                reported_power_w = physical_power_w

            # --- 3. IDS Katmanı (Tespit Mantığı) ---
            if physical_direction == 'Import' and reported_direction == 'Export':
                if PROTOCOL_VERSION == '1.6':
                    ids_decision = 'ANOMALİ (Import/Export Çakışması - 1.6 Tespiti)'
                else:
                    ids_decision = 'ANOMALİ (Güvenlik Profili İhlali - 2.0 Tespiti)'
            elif physical_direction == 'Export' and reported_direction == 'Import':
                if PROTOCOL_VERSION == '1.6':
                    ids_decision = 'ANOMALİ (Export/Import Çakışması - 1.6 Tespiti)'
                else:
                    ids_decision = 'ANOMALİ (Güvenlik Profili İhlali - 2.0 Tespiti)'
            else:
                ids_decision = 'Tutarlı (Normal)'
            
            # --- 4. Veri Paketini Hazırla ve Logla ---
            data_packet = {
                'timestamp': timestamp,
                'can': {
                    'direction': physical_direction,
                    'power_w': physical_power_w,
                    'soc': physical_soc
                },
                'ocpp': {
                    'direction': reported_direction,
                    'power_w': reported_power_w
                },
                'ids': {
                    'decision': ids_decision
                },
                'label': label,
                'protocol': PROTOCOL_VERSION
            }
            
            try:
                sio.emit('gateway_data', data_packet)
                print(f"Data paketi gönderildi, IDS: {ids_decision}")
            except Exception as e:
                print(f"Sunucuya veri gönderilemedi: {e}")

            try:
                writer.writerow([
                    timestamp,
                    physical_direction,
                    physical_power_w,
                    physical_soc,
                    reported_direction,
                    reported_power_w,
                    ids_decision,
                    label,
                    PROTOCOL_VERSION
                ])
                log_file.flush()
            except Exception as e:
                print(f"CSV dosyasına yazılamadı: {e}")

# Ana program
if __name__ == '__main__':
    try:
        sio.connect('http://localhost:5000')
        run_gateway_listener()
    except socketio.exceptions.ConnectionError as e:
        print(f"Ana sunucuya bağlanılamadı: {e}")
        print("Lütfen önce 'python3 v2g_server.py' komutunu çalıştırın.") # DEĞİŞTİRİLDİ
    except KeyboardInterrupt:
        print("\nDurduruluyor...")
    finally:
        log_file.close()
        sio.disconnect()
        print("Bağlantılar ve dosyalar kapatıldı.")
