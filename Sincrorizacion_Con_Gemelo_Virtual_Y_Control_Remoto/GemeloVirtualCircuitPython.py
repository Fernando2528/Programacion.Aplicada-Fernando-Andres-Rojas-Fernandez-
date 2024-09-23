import board
import digitalio
import pwmio
import adafruit_esp32spi.adafruit_esp32spi as esp32spi
import busio
import time

# Configuración de los pines para el ESP32
esp32_cs = digitalio.DigitalInOut(board.GP5)   # Pin para Chip Select
esp32_ready = digitalio.DigitalInOut(board.GP6) # Pin para Ready
esp32_reset = digitalio.DigitalInOut(board.GP7) # Pin para Reset

# Inicializar el bus SPI
spi = busio.SPI(board.GP2, board.GP3, board.GP4)  # MISO, MOSI, SCK

# Inicializar el ESP32 SPI
esp = esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Conectar a Wi-Fi
ssid = 'FLIA RUBIANO_2G-Etb'
password = '3105807039'

esp.connect(ssid, password)

print("Conectado a Wi-Fi")

# Configuración de los servos
servo_hombro = pwmio.PWMOut(board.GP0, frequency=50)  # Pin para el servo del hombro
servo_codo = pwmio.PWMOut(board.GP1, frequency=50)     # Pin para el servo del codo

def map_angle_to_duty(angle):
    return int((angle / 180) * 65535)

def move_servo_hombro(angle):
    duty = map_angle_to_duty(180 - angle)  # Invertir el ángulo para el servo
    servo_hombro.duty_cycle = duty

def move_servo_codo(angle):
    duty = map_angle_to_duty(180 - angle)  # Invertir el ángulo para el servo
    servo_codo.duty_cycle = duty

def start_server():
    addr = esp.get_host_by_name('0.0.0.0', 80)
    esp.start_server(addr)
    print("Servidor iniciado en", addr)

    while True:
        request = esp.get_request()
        
        if request:
            if 'GET /' in request:
                # Manejar la solicitud de la página HTML
                response = """HTTP/1.1 200 OK
Content-Type: text/html

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Control de Servos</title>
</head>
<body>
    <h1>Control de Servos</h1>
    <label for="hombro">Hombro (-90 a 90):</label>
    <input type="range" id="hombro" min="-90" max="90" value="0" oninput="updateServo(this.value, 'hombro')">
    <label for="codo">Codo (90 a 180):</label>
    <input type="range" id="codo" min="90" max="180" value="90" oninput="updateServo(this.value, 'codo')">
    <script>
        function updateServo(value, type) {
            fetch('/move_' + type + '?angle=' + value);
        }
    </script>
</body>
</html>
"""
                esp.send_response(request, response)
            elif 'GET /move_hombro' in request:
                angle = int(request.split('angle=')[1].split()[0])
                move_servo_hombro(angle)
                esp.send_response(request, b'HTTP/1.1 200 OK\r\n\r\n')
            elif 'GET /move_codo' in request:
                angle = int(request.split('angle=')[1].split()[0])
                move_servo_codo(angle)
                esp.send_response(request, b'HTTP/1.1 200 OK\r\n\r\n')

start_server()

