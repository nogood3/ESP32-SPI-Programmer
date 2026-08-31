# ESP32-SPI-Programmer
ESP32 software programmer FOR BIOS flash

# ESP32-1.8V-SPI-Flash-Programmer

A fast, reliable, open-source DIY SPI flash programmer built using an **ESP32** and a custom **Python client**. Specifically designed and proven to unbrick motherboards utilizing low-voltage 1.8V SPI flash chips (such as the **Macronix MX25U12873F** found on the popular **Gigabyte B450M S2H**), without requiring expensive specialized hardware.

## The Problem with Standard Programmers (CH341A)
Many modern motherboards use 1.8V SPI chips. Popular cheap programmers like the CH341A supply 3.3V/5V logic, which overloads the 1.8V flash chip's protective diodes, causes signal corruption, or permanently damages the chip. Using simple resistor dividers often fails due to high parasitic capacitance which distorts high-frequency SPI waveforms, leading to `md5sum` verification mismatches.

## The Solution
This project uses **ESP32's hardware SPI (VSPI)** configured in `SPI_MODE3` with custom burst-block data streaming. It features an over-voltage hardware workaround by slightly boosting the flash chip's VCC using an **LM317** regulator to **2.35V** (safely within the chip's absolute maximum of 2.5V). This raises the logic thresholds and enables clean, error-free communication with the ESP32 without any logic level shifters.

---

## 🛠️ Features
- **High-Speed Burst Read:** Dumps 16MB BIOS in less than a minute.
- **Reliable Page Programming:** Implements safe 4KB Sector Erasing before 256-byte page writes.
- **Hardware Agnostic:** Works flawlessly on Linux (proven on Ubuntu/Debian environments).
- **100% Verified:** Ensures flawless 1-to-1 matching `md5sum` verification.

---

## 🔌 Hardware Wiring Diagram


Connect your 1.8V Flash Chip (`MX25U12873F` / SOIC-8) to the ESP32 as follows:

| SPI Function | ESP32 GPIO Pin | Flash Chip Pin (SOIC-8) | Notes |
| :--- | :--- | :--- | :--- |
| **GND** | **GND** | **Pin 4 (GND)** | Shared common ground between PC, ESP32, and LM317 |
| **VCC** | *Do NOT connect to ESP32!* | **Pin 8 (VCC)** | **Connect to LM317 output adjusted to ~2.35V** |
| **CS / CE** | **GPIO 5** | **Pin 1 (CS#)** |  Voltage divider  |
| **MISO / DO** | **GPIO 19** | **Pin 2 (DO)** | Direct connection (Input to ESP32) |
| **WP#** | *Do NOT connect to ESP32!* | **Pin 3 (WP#)** | Connect to LM317 output (~2.35V) |
| **CLK / SCLK**| **GPIO 18** | **Pin 6 (CLK)** |  Voltage divider  |
| **HOLD#** | *Do NOT connect to ESP32!* | **Pin 7 (HOLD#)**| Connect to LM317 output (~2.35V) |
| **MOSI / DI** | **GPIO 23** | **Pin 5 (DI)** |  Voltage divider  |

---

## 💻 Quick Start Guide

### 1. Flash the ESP32 Firmware
1. Open the Arduino IDE.
2. Install the ESP32 board package (version 3.0.x supported).
3. Open `esp32_spi_programmer.ino` from the firmware directory.
4. Select your ESP32 board model and port (e.g., `/dev/ttyUSB0`).
5. Set the Upload Speed to `921600` and hit **Upload**.

### 2. Setup the Python Client (Linux)
Ensure you have Python 3 and `pyserial` installed:
```bash
pip install pyserial
```

### 3. Usage Commands

#### Read JEDEC ID (Connection Test)
Verify if the ESP32 successfully detects the Macronix chip. You should see `C2 25 38` for a 16MB Macronix chip:
```bash
python3 programmer.py -p /dev/ttyUSB0 -i
```

#### Read / Dump BIOS
Extract the current flash memory content into a file (16384 KB = 16MB):
```bash
python3 programmer.py -p /dev/ttyUSB0 -r original_backup.bin -s 16384
```
*Tip: Run this twice with different filenames and verify using `md5sum original_backup.bin original_backup2.bin` to ensure 100% integrity.*

#### Write / Flash BIOS
Erase and write a new, clean BIOS image file (`new_bios.bin`):
```bash
python3 programmer.py -p /dev/ttyUSB0 -w new_bios.bin
```

---

## 📄 License & Credits
- **Firmware & Software Author:** AI Assistant (OpenAI / Anthropic / Google Model Suite)
- **Hardware Validation, Testing & Workaround Pioneer:** Nogood3 (Alexander Dragan)
- **License:** MIT License. Feel free to use, modify, and distribute!
