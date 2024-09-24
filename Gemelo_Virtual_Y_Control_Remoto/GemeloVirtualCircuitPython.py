import board
import pwmio
import wifi
import socketpool
import adafruit_requests
import time
from adafruit_motor import servo

# Conectar a Wi-Fi utilizando el chip de la Raspberry Pi Pico W
ssid = 'PruebaPi'
password = '11223344'

print("Conectando a Wi-Fi...")
wifi.radio.connect(ssid, password)
print("Conectado a", ssid)
print("IP:", wifi.radio.ipv4_address)

# Crear un pool de sockets
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

# Configuración de los servos
pwm_hombro = pwmio.PWMOut(board.GP0, frequency=50)
pwm_codo = pwmio.PWMOut(board.GP1, frequency=50)

servo_hombro = servo.Servo(pwm_hombro)
servo_codo = servo.Servo(pwm_codo)

# Funciones para mover los servos
def move_servo_hombro(angle):
    servo_hombro.angle = angle  # Establecer el ángulo del servo del hombro

def move_servo_codo(angle):
    servo_codo.angle = angle  # Establecer el ángulo del servo del codo

# Contenido HTML para la interfaz web
html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Control de Servos</title>
</head>
<body>
    <h1>Control de Servos</h1>
    <label for="hombro">Hombro (0 a 180):</label>
    <input type="range" id="hombro" min="0" max="180" value="90" oninput="updateServo(this.value, 'hombro')">
    <label for="codo">Codo (0 a 180):</label>
    <input type="range" id="codo" min="0" max="180" value="90" oninput="updateServo(this.value, 'codo')">
    <script>
        function updateServo(value, type) {
            fetch('/move_' + type + '?angle=' + value);
        }
    </script>
</body>
</html>
"""

# Iniciar el servidor
def start_server():
    addr = (str(wifi.radio.ipv4_address), 80)  # Convertir la IP a cadena de texto y usar el puerto 80
    server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)  # Crear un socket TCP
    server.bind(addr)
    server.listen(1)  # Escuchar hasta 1 conexión entrante
    print("Servidor iniciado en http://{}:80".format(wifi.radio.ipv4_address))

    while True:
        client, addr = server.accept()  # Aceptar conexiones entrantes
        print('Cliente conectado desde', addr)
        
        # Crear un buffer para recibir los datos
        buffer = bytearray(1024)  # Tamaño del buffer de recepción
        num_bytes = client.recv_into(buffer)  # Leer los datos en el buffer
        
        if num_bytes > 0:
            request = buffer[:num_bytes].decode('utf-8')
            print("Solicitud:", request)

            if 'GET / ' in request:
                # Enviar la página HTML al cliente
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/html\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(html.encode('utf-8'))

            elif 'GET /move_hombro' in request:
                # Controlar el servo del hombro
                angle = int(request.split('angle=')[1].split()[0])
                move_servo_hombro(angle)
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del hombro movido\n")

            elif 'GET /move_codo' in request:
                # Controlar el servo del codo
                angle = int(request.split('angle=')[1].split()[0])
                move_servo_codo(angle)
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del codo movido\n")

        client.close()

# Iniciar el servidor web
start_server()
