# vehicle_simulator.py: Araç/Metre Simülatörü
# Sürekli olarak 'vcano0' arayüzüne "Import" (şarj) CAN mesajları gönderir.
# Terminal 2'de çalıştırılacak: sudo python3 vehicle_simulator.py

import can
import time
import sys

# vcano arayüzüne bağlan
try:
    bus = can.interface.Bus(channel='vcano0', interface='socketcan')
except OSError:
    print("vcano0 arayüzü bulunamadı.")
    print("Lütfen önce 'sudo ip link set vcano0 up' komutunu çalıştırdığınızdan emin olun.")
    sys.exit(1)

# CAN ID 0x102: [Yön (1=Import, 2=Export), Güç_High, Güç_Low, SoC_%]
# Senaryo: Araç sürekli 11kW (11000W) ile şarj oluyor (Import) ve SoC %60
power_w = 11000
soc_percent = 60
msg_data = [
    1,  # Yön: 1 = Import (Şarj)
    (power_w >> 8) & 0xFF,  # Güç Yüksek Byte
    power_w & 0xFF,         # Güç Düşük Byte
    soc_percent,            # Batarya Durumu (SoC)
    0, 0, 0, 0              # Kalan baytlar (padding)
]

# Gönderilecek CAN mesajını oluştur
msg = can.Message(
    arbitration_id=0x102,
    data=msg_data,
    is_extended_id=False
)

print("Fiziksel Katman (Araç Simülatörü) çalışıyor...")
print(f"vcano0 arayüzüne her 2 saniyede bir {msg.arbitration_id:#x} ID'li CAN mesajı gönderilecek.")

while True:
    try:
        bus.send(msg)
        print(f"CAN Gönderildi: ID={msg.arbitration_id:#x} Veri={list(msg.data)}")
        
        # Batarya SoC'yi yavaşça arttır (daha gerçekçi olması için)
        if msg_data[3] < 95:
            msg_data[3] += 1
        
        msg = can.Message(
            arbitration_id=0x102,
            data=msg_data,
            is_extended_id=False
        )
        
        time.sleep(2)  # Her 2 saniyede bir mesaj gönder
    except KeyboardInterrupt:
        print("\nDurduruluyor...")
        bus.shutdown()
        sys.exit(0)
    except Exception as e:
        print(f"Hata: {e}")
        time.sleep(5)
