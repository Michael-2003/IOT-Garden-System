import json
import threading
import spidev
import RPi.GPIO as GPIO
import time
import board
import adafruit_dht
from BlynkLib import Blynk
from BlynkTimer import BlynkTimer
from http.server import BaseHTTPRequestHandler, HTTPServer

# Server Configuration
HOST = "192.168.137.135"  # Raspberry Pi A's IP address
PORT = 8080  # Port for HTTP server

# Initialize SPI for soil moisture and rain sensors
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000

# GPIO setup for the button and relay
button_pin = 16  # GPIO pin for button
relay_pin = 27   # GPIO pin for relay

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up button and relay pins
GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(relay_pin, GPIO.OUT)

# Initially turn off the relay
GPIO.output(relay_pin, GPIO.HIGH)

# Initialize the DHT11 sensor on GPIO D4
dht_sensor = adafruit_dht.DHT11(board.D18)

# Blynk setup
BLYNK_AUTH_TOKEN = "51WAYpuN-P-Ljcb4eBQ9W4CoicBX2VsW"
blynk = Blynk(BLYNK_AUTH_TOKEN)

# Shared state for sensor data
sensor_data = {
    "soil_moisture": None,
    "rain_sensor": None,
    "temperature_c": None,
    "temperature_f": None,
    "humidity": None,
}
sensor_data_lock = threading.Lock()

# Shared state for pump control and button state
pump_state = False
pump_state_lock = threading.Lock()
button_pressed = False
button_state_lock = threading.Lock()

# Function to read data from an SPI channel
def readChannel(channel):
    val = spi.xfer2([1, (8 + channel) << 4, 0])
    data = ((val[1] & 3) << 8) + val[2]
    return data

# Function to read soil moisture sensor data
def read_soil_moisture():
    while True:
        soil_moisture_val = readChannel(0)
        max_sensor_value = 1023  # Max ADC value for 10-bit ADC
        soil_moisture_percent = 100 - ((soil_moisture_val / max_sensor_value) * 100)
        with sensor_data_lock:
            sensor_data["soil_moisture"] = soil_moisture_percent
        time.sleep(1)

# Function to read rain sensor data
def read_rain_sensor():
    while True:
        rain_sensor_val = readChannel(1)
        max_sensor_value = 1023  # Max ADC value for 10-bit ADC
        rain_sensor_percent = 100 - ((rain_sensor_val / max_sensor_value) * 100)
        with sensor_data_lock:
            sensor_data["rain_sensor"] = rain_sensor_percent
        time.sleep(1)

# Function to read temperature and humidity from DHT sensor
def read_dht_sensor():
    retries = 3
    while retries > 0:
        try:
            temperature_c = dht_sensor.temperature
            humidity = dht_sensor.humidity

            if temperature_c is not None and humidity is not None:
                temperature_f = temperature_c * (9 / 5) + 32
                with sensor_data_lock:
                    sensor_data["temperature_c"] = temperature_c
                    sensor_data["temperature_f"] = temperature_f
                    sensor_data["humidity"] = humidity
            else:
                print("Invalid DHT sensor readings.")
        except RuntimeError as error:
            print(f"Retrying due to RuntimeError: {error}")
            time.sleep(2)
            retries -= 1
            continue
        
        time.sleep(1)

# Add Blynk virtual pin V4 handler
@blynk.on("V4")
def v4_write_handler(value):
    global pump_state
    print(f"V4 handler called with value: {value}")  # Debug print
    if int(value[0]) != 0:  # If the Blynk switch is ON
        with pump_state_lock:
            pump_state = True
            GPIO.output(relay_pin, GPIO.LOW)  # Turn pump ON
            print("Pump: ON (via Blynk)")
    else:  # If the Blynk switch is OFF
        with pump_state_lock:
            pump_state = False
            GPIO.output(relay_pin, GPIO.HIGH)  # Turn pump OFF
            print("Pump: OFF (via Blynk)")

# Function to monitor the physical button and synchronize it with the Blynk switch
def monitor_physical_button():
    global pump_state, button_pressed
    while True:
        if GPIO.input(button_pin) == GPIO.LOW:  # If the button is pressed
            with button_state_lock:
                if not button_pressed:
                    button_pressed = True
                    with pump_state_lock:
                        pump_state = True
                        GPIO.output(relay_pin, GPIO.LOW)  # Turn pump ON
                    print("Pump: ON (via Button)")
                    # Update Blynk virtual pin V4 to reflect the button press
                    blynk.virtual_write(4, 1)  # Simulate switch ON in Blynk
        else:
            with button_state_lock:
                if button_pressed:
                    button_pressed = False
                    with pump_state_lock:
                        pump_state = False
                        GPIO.output(relay_pin, GPIO.HIGH)  # Turn pump OFF
                    print("Pump: OFF (via Button)")
                    # Update Blynk virtual pin V4 to reflect the button release
                    blynk.virtual_write(4, 0)  # Simulate switch OFF in Blynk
        time.sleep(0.1)  # Poll the button every 0.1 second

# Function to update Blynk virtual pins
def update_blynk():
    print("Updating Blynk virtual pins...")  # Debug print
    with sensor_data_lock:
        soil_moisture_percent = sensor_data["soil_moisture"]
        rain_sensor_percent = sensor_data["rain_sensor"]
        temperature_c = sensor_data["temperature_c"]
        humidity = sensor_data["humidity"]

        # Send sensor data to Blynk app
        if soil_moisture_percent is not None:
            blynk.virtual_write(2, soil_moisture_percent)
        if rain_sensor_percent is not None:
            blynk.virtual_write(3, rain_sensor_percent)
        if temperature_c is not None:
            blynk.virtual_write(1, temperature_c)
        if humidity is not None:
            blynk.virtual_write(0, humidity)

# Create a BlynkTimer instance
timer = BlynkTimer()

# Add the update_blynk function to the timer to run every second
timer.set_interval(1, update_blynk)

# HTTP server handler
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            # Return sensor data as JSON
            with sensor_data_lock:
                response = json.dumps(sensor_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
        else:
            # Default message
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"Welcome to the IoT Agriculture System Server.")

    def do_POST(self):
        if self.path == "/control":
            # Parse incoming data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            # Control the pump based on the received data
            global pump_state
            if "pump" in data:
                with pump_state_lock:
                    if data["pump"] == "on":
                        pump_state = True
                        GPIO.output(relay_pin, GPIO.LOW)  # Turn pump ON
                        response = {"status": "Pump turned ON"}
                    elif data["pump"] == "off":
                        pump_state = False
                        GPIO.output(relay_pin, GPIO.HIGH)  # Turn pump OFF
                        response = {"status": "Pump turned OFF"}
                    else:
                        response = {"error": "Invalid pump command"}
            else:
                response = {"error": "No pump command provided"}

            # Send response
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

# Start the HTTP server
def start_server():
    server = HTTPServer((HOST, PORT), RequestHandler)
    print(f"Server running at http://{HOST}:{PORT}")
    server.serve_forever()

# Start the server in a separate thread
server_thread = threading.Thread(target=start_server, daemon=True)
server_thread.start()

# Start the sensor reading threads
soil_thread = threading.Thread(target=read_soil_moisture, daemon=True)
rain_thread = threading.Thread(target=read_rain_sensor, daemon=True)
dht_thread = threading.Thread(target=read_dht_sensor, daemon=True)
button_thread = threading.Thread(target=monitor_physical_button, daemon=True)

soil_thread.start()
rain_thread.start()
dht_thread.start()
button_thread.start()

# Main application loop
try:
    print("System is running. Access the server for control.")
    while True:
        blynk.run()  # Ensure Blynk event handling
        timer.run()  # Run the timer
except KeyboardInterrupt:
    print("Shutting down...")
finally:
    GPIO.cleanup()
    print("GPIO cleaned up.")