import time
import board
import pwmio
import socketpool
import wifi

# Conectar a WiFi
wifi.radio.connect("PruebaPi", "11223344")
pool = socketpool.SocketPool(wifi.radio)

print("Conectado a WiFi:", wifi.radio.hostname, wifi.radio.ipv4_address)

# Configuración de dos servomotores
pwm_servo1 = pwmio.PWMOut(board.GP15, duty_cycle=0, frequency=50)
pwm_servo2 = pwmio.PWMOut(board.GP0, duty_cycle=0, frequency=50)

# Definir los valores de mínimo y máximo
min_duty = 1638  # 5% duty cycle de 65535 (~1 ms, 0 grados)
max_duty = 8192  # 10% duty cycle de 65535 (~2 ms, 180 grados)

# Inicializar los ángulos actuales de los servos
angulo_actual_servo1 = 90
angulo_actual_servo2 = 90

# Función para calcular puntos en la curva de Bézier cúbica
def bezier_cubic(t, P0, P1, P2, P3):
    return (1 - t)**3 * P0 + 3 * (1 - t)**2 * t * P1 + 3 * (1 - t) * t**2 * P2 + t**3 * P3

# Función para mover el servo de forma suave usando la curva de Bézier
def calcular_trayectoria(servo_number, angulo_inicial, angulo_final):
    P0 = angulo_inicial
    P3 = angulo_final
    P1 = P0 + (P3 - P0) * 0.3  # Punto de control ajustado
    P2 = P0 + (P3 - P0) * 0.7  # Otro punto de control ajustado
    pasos = 50  # Número de pasos para suavizar el movimiento y que dure 2 segundos
    tiempo_total = 2.0  # Tiempo en segundos para completar el movimiento
    pausa = tiempo_total / pasos  # Tiempo de pausa entre cada paso

    for i in range(pasos + 1):
        t = i / pasos
        angulo = bezier_cubic(t, P0, P1, P2, P3)
        duty_cycle = max(min(int(min_duty + (angulo / 180) * (max_duty - min_duty)), max_duty), min_duty)

        if servo_number == 1:
            pwm_servo1.duty_cycle = duty_cycle
        elif servo_number == 2:
            pwm_servo2.duty_cycle = duty_cycle

        print(f"Servo {servo_number}: Ángulo enviado -> {angulo:.2f} grados")  # Imprimir el ángulo enviado
        time.sleep(pausa)  # Pausa para ajustar la velocidad del movimiento

# Crear un socket de servidor
s = pool.socket()
s.setsockopt(pool.SOL_SOCKET, pool.SO_REUSEADDR, 1)
s.bind(('', 80))
s.listen(5)

# Página web HTML para controlar los servos
html = """
<!DOCTYPE html>
<head>
    <title>Control de Servos</title>
</head>
<body>
    <h1>Control de Servomotores</h1>
    <p>Servo 1: <input type="range" min="0" max="180" value="90" id="servo1" oninput="sendValue(1, this.value)"></p>
    <p>Servo 2: <input type="range" min="0" max="180" value="90" id="servo2" oninput="sendValue(2, this.value)"></p>

    <script>
    function sendValue(servo, angle) {
        fetch("/set?servo=" + servo + "&angle=" + angle);
    }

    setInterval(() => {
        fetch("/status").then(response => response.json()).then(data => {
            document.getElementById("servo1").value = data.servo1;
            document.getElementById("servo2").value = data.servo2;
        });
    }, 1000);  // Actualizar cada segundo
    </script>
</body>
</html>
"""

# Bucle principal para manejar las solicitudes del cliente
while True:
    conn, addr = s.accept()
    print('Got a connection from %s' % str(addr))
    buffer = bytearray(1024)
    bytes_received = conn.recv_into(buffer)
    
    if bytes_received > 0:
        request = str(buffer[:bytes_received], 'utf-8')
    else:
        request = ""

    if "GET / " in request:
        response = "HTTP/1.1 200 OK\n\n" + html
    elif "GET /set?" in request:
        try:
            _, query = request.split("GET /set?")
            query, _ = query.split(" HTTP/1.1")
            params = query.split("&")
            servo_number = int(params[0].split("=")[1])
            angle = int(params[1].split("=")[1])

            # Mover el servo de forma suave usando curvas de Bézier
            if servo_number == 1:
                calcular_trayectoria(1, angulo_actual_servo1, angle)
                angulo_actual_servo1 = angle
            elif servo_number == 2:
                calcular_trayectoria(2, angulo_actual_servo2, angle)
                angulo_actual_servo2 = angle

            response = "HTTP/1.1 200 OK\n\nOK"
        except Exception as e:
            response = f"HTTP/1.1 400 Bad Request\n\nError: {e}"
    elif "GET /status" in request:
        # Enviar el estado actual de los servos
        status = {
            "servo1": angulo_actual_servo1,
            "servo2": angulo_actual_servo2
        }
        response = f"HTTP/1.1 200 OK\n\n{status}"
    else:
        response = "HTTP/1.1 404 Not Found\n\nPage not found"

    conn.send(response.encode('utf-8'))
    time.sleep(0.01)  # Pequeño retraso para asegurar el envío de la respuesta
    conn.close()
