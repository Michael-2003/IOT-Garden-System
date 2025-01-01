# IOT-Garden-System
---

## Project Overview  
This project focuses on developing an IoT-enabled smart irrigation system designed for efficient water management in agriculture. By integrating environmental sensors and IoT technologies, the system automates irrigation based on real-time conditions. Using the **Blynk** platform, users can monitor sensor data and control the irrigation pump remotely, ensuring optimal resource usage and flexibility.

---

## Key Features  
- **Automated Irrigation**: Uses soil moisture, rain, temperature, and humidity sensors to determine irrigation needs.  
- **Remote Monitoring & Control**: Supports real-time data visualization and remote pump control via the Blynk mobile app.  
- **Water Conservation**: Prevents overwatering by pausing irrigation during rainfall and ensures water is used only when necessary.  
- **Real-Time Monitoring**: Updates environmental conditions (soil moisture, temperature, humidity) instantly.  

---

## Hardware Components  
- **Raspberry Pi**: Central processing unit for controlling the system.  
- **Sensors**:  
  - Soil Moisture Sensor (Analog input via ADC)  
  - Rain Sensor (Digital input)  
  - DHT11 Sensor (Temperature & Humidity)  
- **Relay Module**: Controls the water pump based on sensor data.  

---

## Software Architecture  
- **Programming Language**: Python  
- **Core Libraries**:  
  - `RPi.GPIO` for GPIO control  
  - `Adafruit_DHT` for DHT11 sensor integration  
  - `Blynk` library for IoT cloud connectivity  
- **Communication Protocols**:  
  - SPI for sensor data transfer  
  - HTTP for Blynk cloud communication  
  - GPIO for relay and sensor interfacing  

---

## How It Works  
1. **Sensor Data Collection**: Sensors capture environmental parameters and send data to the Raspberry Pi.  
2. **Data Processing**: The Raspberry Pi evaluates sensor readings against predefined thresholds to decide if irrigation is necessary.  
3. **Blynk Integration**: Sensor data is sent to the Blynk app for real-time visualization, and users can control the irrigation pump remotely.  
4. **Automated Control**: If soil moisture levels are below the threshold and no rain is detected, the relay activates the water pump.  

---

## Blynk Interface  
Below is a snapshot of the Blynk app interface used for monitoring and controlling the smart irrigation system.  

**Blynk Dashboard**:  

![image](https://github.com/user-attachments/assets/e51db85b-4c1e-4055-ab5d-ab58d97a1edd)

---

## Installation Instructions  
### Hardware Setup  
- Connect sensors and the relay module to the Raspberry Pi GPIO pins.  
- Use an ADC to interface the soil moisture sensor.  
- Follow the provided circuit diagram for correct wiring.  

### Software Setup  
- Install required Python libraries:  
  ```bash
  pip install blynk-library Adafruit_DHT RPi.GPIO
  ```  
- Clone the project repository and navigate to the directory.  
- Configure your **Blynk Auth Token** in the script.  

### Run the Program  
- Start the script to initialize the system:  
  ```bash
  python smart_irrigation.py
  ```  

---

## Future Enhancements  
- **Predictive Irrigation**: Integrating AI models to forecast irrigation needs based on weather predictions.  
- **Scalability**: Expanding the system for large-scale agricultural applications.  
- **Additional Sensors**: Adding sensors for pH levels, light intensity, or wind speed.  

---

## Institution  
Nile University

