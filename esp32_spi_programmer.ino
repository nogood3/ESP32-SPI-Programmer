#include <SPI.h>

#define SPI_CS   5
#define SPI_CLK  18
#define SPI_MISO 12
#define SPI_MOSI 23

#define CMD_CS_LOW       0x01
#define CMD_CS_HIGH      0x02
#define CMD_XFER         0x03
#define CMD_BURST_READ   0x04
#define CMD_SECTOR_ERASE 0x05 // Нова команда: Стерти сектор 4КБ
#define CMD_PAGE_WRITE   0x06 // Нова команда: Записати сторінку 256 байт
#define RESP_ACK         0x41

void setup() {
    Serial.begin(921600);
    pinMode(SPI_CS, OUTPUT);
    digitalWrite(SPI_CS, HIGH);
    SPI.begin(SPI_CLK, SPI_MISO, SPI_MOSI, SPI_CS);
    SPI.beginTransaction(SPISettings(1000000, MSBFIRST, SPI_MODE3)); // 1 МГц, як перевірено
}

// Функція очікування завершення внутрішньої операції флешки (WIP - Write In Progress)
void wait_flash_ready() {
    uint8_t status = 0;
    do {
        digitalWrite(SPI_CS, LOW);
        SPI.transfer(0x05); // Команда: Read Status Register
        status = SPI.transfer(0x00);
        digitalWrite(SPI_CS, HIGH);
        delayMicroseconds(10);
    } while (status & 0x01); // Поки 0-й біт (WIP) дорівнює 1, чіп зайнятий
}

// Функція дозволу запису (Write Enable)
void write_enable() {
    digitalWrite(SPI_CS, LOW);
    SPI.transfer(0x06); // Команда: Write Enable
    digitalWrite(SPI_CS, HIGH);
}

void loop() {
    if (Serial.available() > 0) {
        uint8_t command = Serial.read();
        
        switch (command) {
            case CMD_CS_LOW:
                digitalWrite(SPI_CS, LOW);
                Serial.write(RESP_ACK);
                break;
                
            case CMD_CS_HIGH:
                digitalWrite(SPI_CS, HIGH);
                Serial.write(RESP_ACK);
                break;
                
            case CMD_XFER:
                while (Serial.available() == 0);
                Serial.write(SPI.transfer(Serial.read()));
                break;

            case CMD_BURST_READ: {
                while (Serial.available() < 4);
                uint32_t length = 0;
                length |= (uint32_t)Serial.read() << 24;
                length |= (uint32_t)Serial.read() << 16;
                length |= (uint32_t)Serial.read() << 8;
                length |= (uint32_t)Serial.read();

                uint8_t buf[64];
                while (length > 0) {
                    uint32_t chunk = (length > 64) ? 64 : length;
                    SPI.transferBytes(NULL, buf, chunk);
                    Serial.write(buf, chunk);
                    length -= chunk;
                    delayMicroseconds(5);
                }
                break;
            }

            case CMD_SECTOR_ERASE: { // Очікуємо 3 байти адреси сектора
                while (Serial.available() < 3);
                uint8_t a2 = Serial.read();
                uint8_t a1 = Serial.read();
                uint8_t a0 = Serial.read();

                wait_flash_ready();
                write_enable();

                digitalWrite(SPI_CS, LOW);
                SPI.transfer(0x20); // Команда SPI: Sector Erase (4KB)
                SPI.transfer(a2);
                SPI.transfer(a1);
                SPI.transfer(a0);
                digitalWrite(SPI_CS, HIGH);

                wait_flash_ready(); // Чекаємо, поки сектор очиститься
                Serial.write(RESP_ACK);
                break;
            }

            case CMD_PAGE_WRITE: { // Очікуємо 3 байти адреси + 256 байт даних
                while (Serial.available() < 3);
                uint8_t a2 = Serial.read();
                uint8_t a1 = Serial.read();
                uint8_t a0 = Serial.read();

                uint8_t page_buf[256];
                for (int i = 0; i < 256; i++) {
                    while (Serial.available() == 0);
                    page_buf[i] = Serial.read();
                }

                wait_flash_ready();
                write_enable();

                digitalWrite(SPI_CS, LOW);
                SPI.transfer(0x02); // Команда SPI: Page Program (256 байт)
                SPI.transfer(a2);
                SPI.transfer(a1);
                SPI.transfer(a0);
                SPI.writeBytes(page_buf, 256);
                digitalWrite(SPI_CS, HIGH);

                wait_flash_ready(); // Чекаємо фізичного запису в комірки
                Serial.write(RESP_ACK);
                break;
            }
        }
    }
}
