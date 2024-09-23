import time
import board
import pwmio
import wifi
import socketpool

# Wi-Fi Configuration
SSID = "Arkhe"  # Tu SSID
PASSWORD = "euler-phi"  # Tu contraseña

# Server Configuration
PORT = 5000  # Puerto usado en el transmisor

# Conexión Wi-Fi
wifi.radio.connect(SSID, PASSWORD)
print(f"Conectado a {SSID} con la IP: {wifi.radio.ipv4_address}")

# Inicializar el socket
pool = socketpool.SocketPool(wifi.radio)
server_socket = pool.socket(pool.AF_INET, pool.SOCK_STREAM)

# Bind el socket a la IP y puerto
server_socket.bind((str(wifi.radio.ipv4_address), PORT))
server_socket.listen(1)
print(f"Servidor escuchando en {wifi.radio.ipv4_address}:{PORT}")

# Esperar conexión
client_socket, client_address = server_socket.accept()
print(f"Conexión establecida desde {client_address}!")

# Configurar el PWM
pwm_servo1 = pwmio.PWMOut(board.GP15, duty_cycle=0, frequency=50)
pwm_servo2 = pwmio.PWMOut(board.GP14, duty_cycle=0, frequency=50)
pwm_servo3 = pwmio.PWMOut(board.GP13, duty_cycle=0, frequency=50)

# Definir los valores de minimos y maximos
min_duty = 1638  # 5% duty cycle de 65535 (~1 ms, 0 grados)
max_duty = 8192  # 10% duty cycle de 65535 (~2 ms, 180 grados)

try:
    while True:
        # Recibir los datos del transmisor
        buffer = bytearray(1024)
        bytes_received = client_socket.recv_into(buffer)
        request_str = buffer[:bytes_received].decode('utf-8').strip()

        # Separar los datos recibidos
        x_value_str, y_value_str, button_state_str = request_str.split(',')
        x_value = float(x_value_str)
        y_value = float(y_value_str)
        button_state = button_state_str == 'True'

        # Convertir valores recibidos a ángulos (0 a 180 grados)
        angle1 = (x_value / 3.3) * 180
        angle2 = (y_value / 3.3) * 180
        angle3 = 0 if button_state else 180  # Ejemplo para el tercer servo

        # Convertir ángulos al ciclo de trabajo
        duty_cycle1 = int(min_duty + (angle1 / 180) * (max_duty - min_duty))
        duty_cycle2 = int(min_duty + (angle2 / 180) * (max_duty - min_duty))
        duty_cycle3 = int(min_duty + (angle3 / 180) * (max_duty - min_duty))

        # Aplicar el ciclo de trabajo al PWM
        pwm_servo1.duty_cycle = duty_cycle1
        pwm_servo2.duty_cycle = duty_cycle2
        pwm_servo3.duty_cycle = duty_cycle3

        # Pequeña pausa para estabilidad
        time.sleep(0.01)

finally:
    client_socket.close()
    server_socket.close()
