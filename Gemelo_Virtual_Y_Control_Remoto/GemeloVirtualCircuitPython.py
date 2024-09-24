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
    duty_cycle = pwm_hombro.duty_cycle  # Obtener el ciclo de trabajo actual en bits
    print(f"Ángulo del hombro: {angle}, Ciclo de trabajo (bits): {duty_cycle}")

def move_servo_codo(angle):
    servo_codo.angle = angle  # Establecer el ángulo del servo del codo
    duty_cycle = pwm_codo.duty_cycle  # Obtener el ciclo de trabajo actual en bits
    print(f"Ángulo del codo: {angle}, Ciclo de trabajo (bits): {duty_cycle}")


# Contenido HTML para la interfaz web
html = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Brazo Virtual</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        body { margin: 0; background-color: black; }
        canvas { display: block; }
        .controls {
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: rgba(220, 220, 220, 0.9);
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
    </style>
"""+"""    
</head>
<body>
    <h1>Control de Servos</h1>

    <script>
        function updateServo(value, type) {
            fetch('/move_' + type + '?angle=' + value);
        }
    </script>

    <script>
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);
        renderer.setClearColor(0x000000);

        const base = new THREE.Mesh(new THREE.BoxGeometry(3, 0.5, 3), new THREE.MeshPhongMaterial({ color: 0x8B4513 }));
        base.position.y = -0.25;
        scene.add(base);

        const shoulder = new THREE.Group();
        const armMaterial = new THREE.MeshPhongMaterial({ color: 0xF5DEB3 });
        const elbowMaterial = new THREE.MeshPhongMaterial({ color: 0xADD8E6 });

        const arm = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 4, 32), armMaterial);
        arm.position.y = 2;
        shoulder.add(arm);
"""+"""
        const elbow = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.75, 1, 32), elbowMaterial);
        elbow.position.set(0, 4, 0);
        shoulder.add(elbow);

        const forearm = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.5, 4, 32), armMaterial);
        forearm.position.set(0, 2, 0);
        elbow.add(forearm);

        scene.add(shoulder);
        camera.position.set(0, 5, 10);
        camera.lookAt(0, 3, 0);

        const ambientLight = new THREE.AmbientLight(0x404040);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        directionalLight.position.set(0, 10, 10);
        scene.add(directionalLight);

        function animate() {
            requestAnimationFrame(animate);
            renderer.render(scene, camera);
        }

        animate();

        const controlContainer = document.createElement('div');
        controlContainer.className = 'controls';
        document.body.appendChild(controlContainer);

        const shoulderSlider = document.createElement('input');
        shoulderSlider.type = 'range';
        shoulderSlider.min = 0; // Rango de 0 a 90
        shoulderSlider.max = 90;
        shoulderSlider.step = 1;
        shoulderSlider.value = 0; // Inicial en 0 grados
        
        shoulderSlider.oninput = function() {
        const angle = parseFloat(this.value);
        shoulder.rotation.z = THREE.MathUtils.degToRad(-angle);
        updateServo(angle, 'hombro'); // Llama a updateServo con el ángulo actual del slider

        };
"""+"""        
        const elbowSlider = document.createElement('input');
        elbowSlider.type = 'range';
        elbowSlider.min = 90; // Rango mínimo
        elbowSlider.max = 180; // Rango máximo
        elbowSlider.step = 1;
        elbowSlider.value = 0; // Inicial en 0 grados
        elbow.rotation.z = THREE.MathUtils.degToRad(270); // Inicial en 0 grados

        elbowSlider.oninput = function() {
        const angle = parseFloat(this.value);
        elbow.rotation.z = THREE.MathUtils.degToRad(-angle); // Actualiza la rotación del codo
        updateServo(angle, 'codo'); // Envía el valor del ángulo al servidor
        };
        
        controlContainer.appendChild(document.createTextNode('Hombro (0 a 90°): '));
        controlContainer.appendChild(shoulderSlider);
        
        controlContainer.appendChild(document.createElement('br'));
        controlContainer.appendChild(document.createTextNode('Codo (0 a 90°): '));
        controlContainer.appendChild(elbowSlider);
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
                angle = min(max(angle, 0), 90)  # Limitar el ángulo entre 0 y 90
                move_servo_hombro(angle)
                
                
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del hombro movido\n")

            elif 'GET /move_codo' in request:
               
                angle = int(request.split('angle=')[1].split()[0])
    
                # Transformar el ángulo para que 90 sea 0 y 180 sea 90
                adjusted_angle = angle - 90
                adjusted_angle = min(max(adjusted_angle, 0), 90)  # Limitar el ángulo entre 0 y 90
                move_servo_codo(adjusted_angle)
                
                
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del codo movido\n")

        client.close()

# Iniciar el servidor web
start_server()
