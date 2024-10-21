import board
import pwmio
import wifi
import socketpool
import adafruit_requests
import time

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
pwm_codo = pwmio.PWMOut(board.GP15, frequency=50)

# Definir los valores de duty cycle mínimos y máximos
min_duty = 1638  # 1 ms, 0 grados
max_duty = 8192  # 2 ms, 180 grados


def move_servo_hombro(angle):
    # Transformar el rango de -90 a 90 al rango de 0 a 180
    angle_servo = (angle + 90)  # Transforma el ángulo del slider al ángulo esperado por el servo
    
    if angle_servo < 0:
        angle_servo = 0
    elif angle_servo > 180:
        angle_servo = 180
    
    duty_cycle = int(min_duty + (angle_servo / 180) * (max_duty - min_duty))
    pwm_hombro.duty_cycle = duty_cycle
    print(f"Ángulo del hombro (slider): {angle}, Ángulo del servo: {angle_servo}, Ciclo de trabajo (bits): {duty_cycle}")


# Límites para codo: 90 a 180, que coinciden con el rango de 0 a 180 del servo
# Límites para codo: 90 a 180, que coinciden con el rango de 0 a 180 del servo
def move_servo_codo(angle):
    # Invertir el ángulo, de modo que 0 en el slider se traduzca a 180 en el servo, y 180 se traduzca a 90 en el servo
    angle_servo = 180 - angle
    
    # Limitar el ángulo entre 90 y 180 grados (el rango físico del codo)
    if angle_servo < 0:
        angle_servo = 0
    elif angle_servo > 90:
        angle_servo = 90
    
    # Calcular el ciclo de trabajo basado en el ángulo invertido
    duty_cycle = int(min_duty + (angle_servo / 180) * (max_duty - min_duty))
    pwm_codo.duty_cycle = duty_cycle
    print(f"Ángulo del codo (slider): {angle}, Ángulo del servo (invertido): {angle_servo}, Ciclo de trabajo (bits): {duty_cycle}")
    
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
        h1 { color: white; text-align: center; }
    </style>
</head>
<body>
    <h1>Control de Servos del Brazo Robótico</h1>

    <script>
        function updateServo(value, type) {
            fetch('/move_' + type + '?angle=' + value)
                .then(response => response.text())
                .then(data => console.log(data))
                .catch(error => console.error('Error:', error));
        }
        
        class BrazoRobotico {
            constructor(escena) {
                this.hombro = new THREE.Group();
                this.crearBase(escena);
                this.crearBrazo();
                escena.add(this.hombro);
            }

            crearBase(escena) {
                const geometriaBase = new THREE.CylinderGeometry(3.5, 3.5, 0.5, 5);
                const materialBase = new THREE.MeshStandardMaterial({
                    color: 0xEAEAEA,
                    metalness: 0.9,
                    roughness: 0.1,
                    emissive: 0x333333,
                    emissiveIntensity: 0.3
                });
                const base = new THREE.Mesh(geometriaBase, materialBase);
                base.position.y = -0.25;
                escena.add(base);
            }

            crearBrazo() {
                const textura = new THREE.TextureLoader().load('https://threejsfundamentals.org/threejs/resources/images/wall.jpg');

                const materialBrazo = new THREE.MeshStandardMaterial({
                    map: textura,
                    metalness: 0.8,
                    roughness: 0.3,
                    emissive: 0xFF4500,
                    emissiveIntensity: 0.6
                });

                const materialCodo = new THREE.MeshStandardMaterial({
                    color: 0x87CEEB,
                    metalness: 0.9,
                    roughness: 0.2,
                    emissive: 0x4682B4,
                    emissiveIntensity: 0.6
                });

                const materialMagneto = new THREE.MeshStandardMaterial({
                    color: 0xEAEAEA,
                    metalness: 0.7,
                    roughness: 0.1,
                    emissive: 0xFFFFFF,
                    emissiveIntensity: 0.8
                });

                // Brazo
                const brazo = new THREE.Mesh(new THREE.BoxGeometry(1.3, 4, 1.3), materialBrazo);
                brazo.position.y = 2;
                this.hombro.add(brazo);

                // Codo
                const articulacionHombro = new THREE.Mesh(new THREE.SphereGeometry(0.80, 32, 32), materialCodo);
                articulacionHombro.position.y = 4;
                this.hombro.add(articulacionHombro);

                const codo = new THREE.Mesh(new THREE.BoxGeometry(1.5, 1.5, 1.5), materialCodo);
                codo.position.set(0, 4, 0);
                this.hombro.add(codo);

                const antebrazo = new THREE.Mesh(new THREE.BoxGeometry(0.8, 5, 0.8), materialBrazo);
                antebrazo.position.set(0, 2.5, 0);
                codo.add(antebrazo);

                const geometriaMagneto = new THREE.DodecahedronGeometry(1);
                const magneto = new THREE.Mesh(geometriaMagneto, materialMagneto);
                magneto.position.set(0, 3.5, 0);
                antebrazo.add(magneto);

                this.brazo = brazo;
                this.codo = codo;
            }

            rotarHombro(angulo) {
                this.hombro.rotation.z = THREE.MathUtils.degToRad(-angulo);
            }

            rotarCodo(angulo) {
                this.codo.rotation.z = THREE.MathUtils.degToRad(-angulo);
            }
        }

        const escena = new THREE.Scene();
        const camara = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderizador = new THREE.WebGLRenderer({ antialias: true });
        renderizador.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderizador.domElement);
        renderizador.setClearColor(0x000000);

        const brazo = new BrazoRobotico(escena);

        camara.position.set(0, 5, 10);
        camara.lookAt(0, 3, 0);

        const luzAmbiente = new THREE.AmbientLight(0x404040, 2);
        escena.add(luzAmbiente);

        const luzPuntual = new THREE.PointLight(0xFFFFFF, 2);
        luzPuntual.position.set(10, 10, 10);
        escena.add(luzPuntual);

        function animar() {
            requestAnimationFrame(animar);
            renderizador.render(escena, camara);
        }
        animar();

        // Crear controles de sliders
        const contenedorControles = document.createElement('div');
        contenedorControles.className = 'controls';
        document.body.appendChild(contenedorControles);

        const deslizadorHombro = document.createElement('input');
        deslizadorHombro.type = 'range';
        deslizadorHombro.min = -90;
        deslizadorHombro.max = 90;
        deslizadorHombro.step = 1;
        deslizadorHombro.value = 0;  // Ángulo inicial del hombro

        deslizadorHombro.oninput = function () {
            const angulo = parseFloat(this.value);
            brazo.rotarHombro(angulo);
            updateServo(angulo, 'hombro');
        };

        const deslizadorCodo = document.createElement('input');
        deslizadorCodo.type = 'range';
        deslizadorCodo.min = 0;
        deslizadorCodo.max = 90;
        deslizadorCodo.step = 1;
        deslizadorCodo.value = 0;  // Ángulo inicial del codo

        deslizadorCodo.oninput = function () {
            const angulo = 180 - parseFloat(this.value);  // Invertir el ángulo (0 se convierte en 180 y 180 en 0)
            brazo.rotarCodo(angulo);
            updateServo(angulo, 'codo');
        };

        const etiquetaHombro = document.createElement('label');
        etiquetaHombro.innerText = 'Hombro: ';
        const etiquetaCodo = document.createElement('label');
        etiquetaCodo.innerText = 'Codo: ';

        contenedorControles.appendChild(etiquetaHombro);
        contenedorControles.appendChild(deslizadorHombro);
        contenedorControles.appendChild(document.createElement('br'));
        contenedorControles.appendChild(etiquetaCodo);
        contenedorControles.appendChild(deslizadorCodo);

        // Rotación inicial del brazo y codo
        brazo.rotarHombro(0);  // Ángulo inicial de 45 grados para el hombro
        brazo.rotarCodo(90);   // Ángulo inicial de 120 grados para el codo
    </script>
</body>
</html>

"""

# Iniciar el servidor
def start_server():
    addr = (str(wifi.radio.ipv4_address), 80)
    server = pool.socket(pool.AF_INET, pool.SOCK_STREAM)
    server.bind(addr)
    server.listen(1)
    print("Servidor iniciado en http://{}:80".format(wifi.radio.ipv4_address))

    while True:
        client, addr = server.accept()
        print('Cliente conectado desde', addr)

        buffer = bytearray(1024)
        num_bytes = client.recv_into(buffer)

        if num_bytes > 0:
            request = buffer[:num_bytes].decode('utf-8')
            print("Solicitud:", request)

            if 'GET / ' in request:
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/html\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(html.encode('utf-8'))

            elif 'GET /move_hombro' in request:
                
                
                # Convertir el rango de -90 a 90 en 0 a 180
                
                angle = int(request.split('angle=')[1].split()[0])
                move_servo_hombro(angle)
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del hombro movido\n")
                
                
                
            elif 'GET /move_codo' in request:
                
                
                # Extraer el ángulo de la solicitud
                angle = int(request.split('angle=')[1].split()[0])
                
                move_servo_codo(angle)
                client.send("HTTP/1.1 200 OK\r\n")
                client.send("Content-Type: text/plain\r\n")
                client.send("Connection: close\r\n\r\n")
                client.sendall(b"Servo del codo movido\n")

            client.close()

# Iniciar el servidor web
start_server()
