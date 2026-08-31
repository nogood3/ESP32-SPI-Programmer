import serial
import time
import sys
import argparse
import os

CMD_CS_LOW       = b'\x01'
CMD_CS_HIGH      = b'\x02'
CMD_XFER         = b'\x03'
CMD_BURST_READ   = b'\x04'
CMD_SECTOR_ERASE = b'\x05'
CMD_PAGE_WRITE   = b'\x06'
RESP_ACK         = b'\x41'

class ESP32Programmer:
    def __init__(self, port):
        print(f"[*] Підключення до ESP32 на порту {port}...")
        self.ser = serial.Serial(port, 921600, timeout=10)
        time.sleep(2)
        self.ser.reset_input_buffer()
        print("[+] Підключено успішно.")

    def send_cmd(self, cmd):
        self.ser.write(cmd)
        if self.ser.read(1) != RESP_ACK:
            raise Exception("[-] Помилка пристрою: немає ACK")

    def transfer_byte(self, byte_value):
        self.ser.write(CMD_XFER)
        self.ser.write(bytes([byte_value]))
        return self.ser.read(1)

    def read_jedec_id(self):
        print("[*] Читання JEDEC ID...")
        self.send_cmd(CMD_CS_LOW)
        self.transfer_byte(0x9F)
        m_id = self.transfer_byte(0x00)
        mem_type = self.transfer_byte(0x00)
        cap = self.transfer_byte(0x00)
        self.send_cmd(CMD_CS_HIGH)
        print(f"[+] ID: {m_id.hex().upper()} {mem_type.hex().upper()} {cap.hex().upper()}")
        return m_id, mem_type, cap

    def read_flash(self, output_file, size_kb):
        size_bytes = size_kb * 1024
        print(f"[*] Зчитування дампа ({size_kb} КБ)...")
        start_time = time.time()
        
        self.send_cmd(CMD_CS_LOW)
        self.transfer_byte(0x03)
        self.transfer_byte(0x00)
        self.transfer_byte(0x00)
        self.transfer_byte(0x00)
        
        self.ser.write(CMD_BURST_READ)
        self.ser.write(bytes([(size_bytes >> 24) & 0xFF, (size_bytes >> 16) & 0xFF, (size_bytes >> 8) & 0xFF, size_bytes & 0xFF]))
        
        bytes_read = 0
        with open(output_file, 'wb') as f:
            while bytes_read < size_bytes:
                data = self.ser.read(min(65536, size_bytes - bytes_read))
                if not data: break
                f.write(data)
                bytes_read += len(data)
                print(f"\r[#] Читання: {bytes_read // 1024} КБ / {size_kb} КБ", end="")
                    
        self.send_cmd(CMD_CS_HIGH)
        print(f"\n[+] Зчитано за {round(time.time() - start_time, 2)} сек.")

    def write_flash(self, input_file):
        if not os.path.exists(input_file):
            print(f"[-] Помилка: Файл {input_file} не знайдено!")
            return
            
        file_size = os.path.getsize(input_file)
        print(f"[*] Початок запису файлу {input_file} ({file_size // 1024} КБ)...")
        start_time = time.time()

        with open(input_file, 'rb') as f:
            addr = 0
            while addr < file_size:
                # Кожні 4096 байт (4КБ) робимо стирання нового сектора флешки
                if addr % 4096 == 0:
                    self.ser.write(CMD_SECTOR_ERASE)
                    self.ser.write(bytes([(addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
                    if self.ser.read(1) != RESP_ACK:
                        raise Exception(f"[-] Помилка під час стирання сектора на адресі {hex(addr)}")

                # Записуємо дані сторінками по 256 байт
                chunk = f.read(256)
                if not chunk: break
                
                # Якщо файл не кратний 256 байтам, дописуємо нулями
                if len(chunk) < 256:
                    chunk = chunk + b'\xFF' * (256 - len(chunk))

                self.ser.write(CMD_PAGE_WRITE)
                self.ser.write(bytes([(addr >> 16) & 0xFF, (addr >> 8) & 0xFF, addr & 0xFF]))
                self.ser.write(chunk)
                
                if self.ser.read(1) != RESP_ACK:
                    raise Exception(f"[-] Помилка запису сторінки на адресі {hex(addr)}")
                
                addr += 256
                if addr % 10240 == 0 or addr == file_size:
                    print(f"\r[#] Записано: {addr // 1024} КБ / {file_size // 1024} КБ", end="")

        print(f"\n[+] Запис успішно завершено за {round(time.time() - start_time, 2)} сек!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", required=True)
    parser.add_argument("-i", "--id", action="store_true")
    parser.add_argument("-r", "--read")
    parser.add_argument("-w", "--write")
    parser.add_argument("-s", "--size", type=int, default=16384)
    args = parser.parse_args()
    
    prog = ESP32Programmer(args.port)
    if args.id: prog.read_jedec_id()
    elif args.read: prog.read_flash(args.read, args.size)
    elif args.write: prog.write_flash(args.write)
    prog.ser.close()
