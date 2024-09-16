import wifi
import socketpool
import board
import time
import pwmio
import adafruit_requests as requests

# Conectar a la red Wi-Fi
wifi.radio.connect("PruebaPi", "11223344")
pool = socketpool.SocketPool(wifi.radio)

# Mostrar la dirección IP asignada
print("Conectado a Wi-Fi")
print("Dirección IP:", wifi.radio.ipv4_address)

# Crear una sesión HTTP
session = requests.Session(pool)

# Configurar los servomotores en los pines PWM
servo_pins = {
    1: pwmio.PWMOut(board.GP13, frequency=50),
    2: pwmio.PWMOut(board.GP14, frequency=50),
    3: pwmio.PWMOut(board.GP15, frequency=50)
}

# Función para mover un servomotor específico
def mover_servomotor(servo_id, angle):
    if servo_id in servo_pins:
        # Calcular el ciclo de trabajo (duty cycle) para el ángulo dado
        duty_cycle = int((angle / 180) * 65535)
        servo_pins[servo_id].duty_cycle = duty_cycle
        print(f"Servomotor {servo_id} ajustado a {angle} grados")
    else:
        print(f"Servomotor {servo_id} no existe")

# Configurar el servidor de socket
PORT = 80
s = pool.socket()
s.bind(("", PORT))
s.listen(5)

print("Servidor activo en el puerto", PORT)

while True:
    try:
        conn, addr = s.accept()
        print("Conexión desde", addr)
        request = conn.recv(1024)
        request_str = str(request)
        print("Solicitud:", request_str)

        # Control de los servomotores basado en la solicitud
        if "/servo" in request_str:
            try:
                # Extraer el ID del servomotor (después de "/servo" y antes de "?")
                servo_start = request_str.find("/servo") + len("/servo")
                servo_id_str = request_str[servo_start:servo_start+1]  # Se asume que es un dígito (1, 2 o 3)
                servo_id = int(servo_id_str)

                # Extraer el valor del ángulo
                angle_start = request_str.find("angle=") + len("angle=")
                angle_end = request_str.find(" ", angle_start)
                if angle_end == -1:
                    angle_end = len(request_str)
                angle_str = request_str[angle_start:angle_end]
                angle = int(angle_str)

                # Mover el servomotor si el ángulo es válido
                if 0 <= angle <= 180:
                    mover_servomotor(servo_id, angle)
                else:
                    print("Ángulo fuera de rango")
            except (ValueError, IndexError) as e:
                print("Error al procesar el ángulo o el ID del servomotor:", e)

        # Enviar una redirección HTTP al navegador
        github_html_url = "https://fernando2528.github.io/Programacion.Aplicada-Fernando-Andres-Rojas-Fernandez-/ControlRemoto(V2).html"
        conn.send(b"HTTP/1.1 302 Found\r\n")
        conn.send(f"Location: {github_html_url}\r\n".encode('utf-8'))
        conn.send(b"Connection: close\r\n\r\n")
    except Exception as e:
        print("Error al procesar la solicitud:", e)
    finally:
        conn.close()

    time.sleep(0.1)
