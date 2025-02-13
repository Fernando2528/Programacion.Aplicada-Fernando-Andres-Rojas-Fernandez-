from ov7670 import OV7670_30x40_RGB565 as CAM
import board
import time
import pwmio
from adafruit_motor import servo
import digitalio

# Configuración del relé (electroimán) en GP12
rele = digitalio.DigitalInOut(board.GP16)
rele.direction = digitalio.Direction.OUTPUT

# ==================== CONFIGURACIÓN DE LA CÁMARA ====================
cam1 = CAM(
    d0_d7pinslist=[
        board.GP0, board.GP1, board.GP2, board.GP3,
        board.GP4, board.GP5, board.GP6, board.GP7,
    ],
    plk=board.GP8,
    xlk=board.GP9,
    sda=board.GP20,
    scl=board.GP21,
    hs=board.GP12,
    vs=board.GP13,
    ret=board.GP14,
    pwdn=board.GP15
)

# ==================== CONFIGURACIÓN DE SERVOMOTORES ====================
# Hombro (0° a 180°)
pwm_hombro = pwmio.PWMOut(board.GP22, frequency=50)
servo_hombro = servo.Servo(pwm_hombro, min_pulse=500, max_pulse=2500)

# Codo (0° a 180°)
pwm_codo = pwmio.PWMOut(board.GP10, frequency=50)
servo_codo = servo.Servo(pwm_codo, min_pulse=500, max_pulse=2500)

# Base (0° a 180°) - Ajustamos rango
pwm_base = pwmio.PWMOut(board.GP18, frequency=50)
servo_base = servo.Servo(pwm_base, min_pulse=500, max_pulse=2500)

# ==================== POSICIONES INICIALES ====================
servo_hombro.angle =130
servo_codo.angle = 90
servo_base.angle = 0  # Iniciar en 0° correctamente

print("Posiciones iniciales establecidas. Esperando 3 segundos...")
time.sleep(3)

print("Iniciando detección de objetos...")

# ==================== FUNCIÓN PARA DETECTAR COLORES ====================
# ==================== FUNCIÓN PARA DETECTAR COLORES ====================
def detectar_color():
    """
    Captura una imagen y detecta el color predominante.
    Retorna el color identificado o None si no se detecta.
    """
    try:
        buffer = cam1()
        color_counts = {"azul": 0, "rojo": 0, "verde": 0}

        for i in range(0, len(buffer), 2):
            rgb565 = (buffer[i] << 8) | buffer[i + 1]

            # Convertir a RGB
            r = ((rgb565 >> 11) & 0x1F) * 8
            g = ((rgb565 >> 5) & 0x3F) * 4
            b = (rgb565 & 0x1F) * 8

            if b > 70 and b > (r + 3) and b > (g + 3):
                color_counts["azul"] += 1
            elif r > 140 and r > (g + 60) and r > (b + 60):
                color_counts["rojo"] += 1
            elif g > 120 and g > (r + 50) and g > (b + 50):
                color_counts["verde"] += 1

        # Imprimir los puntajes de cada color
        print(f"Puntajes de colores: Azul={color_counts['azul']}, Rojo={color_counts['rojo']}, Verde={color_counts['verde']}")

        # Determinar el color predominante
        if color_counts["azul"] > color_counts["rojo"] and color_counts["azul"] > color_counts["verde"]:
            return "azul"
        elif color_counts["rojo"] > color_counts["azul"]  and color_counts["rojo"] > color_counts["verde"]:
            return "rojo"
        elif color_counts["verde"] > color_counts["azul"] and color_counts["verde"] > color_counts["rojo"]:
            return "verde"
        else:
            return None
    except Exception as e:
        print("Error al capturar la imagen o procesar los datos:", e)
        return None

# ==================== FUNCIÓN PARA MOVIMIENTO SUAVE ====================
def mover_suavemente(servo, angulo_final, paso=1, delay=0.5):
    """
    Mueve un servomotor lentamente de su posición actual a una nueva posición.
    """
    angulo_actual = servo.angle
    if angulo_actual is None:
        angulo_actual = 0  # Valor por defecto si no se ha definido

    if angulo_actual < angulo_final:
        for angulo in range(int(angulo_actual), int(angulo_final) + 1, paso):
            servo.angle = angulo
            time.sleep(delay)
    else:
        for angulo in range(int(angulo_actual), int(angulo_final) - 1, -paso):
            servo.angle = angulo
            time.sleep(delay)

# ==================== FUNCIÓN PARA MOVER LA BASE CONTINUAMENTE ====================
def mover_base_continuamente():
    """
    Hace que la base gire lentamente en todo su rango (0° a 360°) hasta que se detecte un color.
    """
    global servo_base
    angulo = 0
    direccion = 1  # 1 para subir, -1 para bajar

    while True:
        color_detectado = detectar_color()

        if color_detectado is not None:
            print(f"Color {color_detectado} identificado")
            return  # Sale del bucle y detiene el giro

        # Mover la base lentamente
        servo_base.angle = angulo
        time.sleep(0.15)  # Aumentar el delay para mayor lentitud

        # Cambiar dirección cuando llega a los extremos
        if angulo >= 180:
            direccion = -1
        elif angulo <= 0:
            direccion = 1

        angulo += direccion * 0.5  # Reducir el paso del movimiento para más suavidad

# ==================== FUNCIÓN PARA EL MOVIMIENTO DE RECOGIDA ====================
def realizar_movimiento_preesablecido():
    """
    Realiza el movimiento preestablecido del brazo con movimientos suaves.
    """
    print("Ejecutando secuencia de decenso...")

    # Movimiento del hombro suavemente hacia abajo
    mover_suavemente(servo_hombro, 160, paso=2, delay=0.02)
    time.sleep(5)

    print("Secuencia de recogida completada.")
# ==================== FUNCIÓN PARA EL MOVIMIENTO DE RECOGIDA ====================
def movimiento_azul():
     # Movimiento del hombro suavemente hacia abajo
    mover_suavemente(servo_hombro, 160, paso=2, delay=0.02)
    time.sleep(5)
    
    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.05)  # Hombro con movimiento suave
    time.sleep(2)

    print("Moviendo a la caja")
    mover_suavemente(servo_hombro, 50, paso=1, delay=0.03)  # Movimiento suave del hombro
    mover_suavemente(servo_codo, 40, paso=1, delay=0.03)  # Movimiento suave del codo
    mover_suavemente(servo_hombro, 110, paso=1, delay=0.03)  # Movimiento suave del hombro
    time.sleep(2)
    
    print("Girando la base 90 grados")
    mover_suavemente(servo_base, 90, paso=1, delay=0.05)  # Movimiento suave de la base
    time.sleep(1)


    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)

    print("Regresando a la posición inicial")
    mover_suavemente(servo_hombro, 100, paso=1, delay=0.08)  # Hombro vuelve suavemente
    mover_suavemente(servo_codo, 140, paso=1, delay=0.08)  # Codo vuelve suavemente
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.08)  # Hombro vuelve suavemente

    time.sleep(2)
# ==================== FUNCIÓN PARA EL MOVIMIENTO DE RECOGIDA ====================
def movimiento_rojo():
    
    
    # Movimiento del hombro suavemente hacia abajo
    mover_suavemente(servo_hombro, 160, paso=2, delay=0.02)
    time.sleep(5)
    
    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.05)  # Hombro con movimiento suave
    time.sleep(2)

    print("Moviendo a la caja")
    mover_suavemente(servo_hombro, 50, paso=1, delay=0.05)  # Movimiento suave del hombro
    mover_suavemente(servo_codo, 30, paso=1, delay=0.05)  # Movimiento suave del codo
    mover_suavemente(servo_hombro, 110, paso=1, delay=0.05)  # Movimiento suave del hombro
    time.sleep(2)
    
    print("Girando la base 0 grados")
    mover_suavemente(servo_base, 0, paso=1, delay=0.05)  # Movimiento suave de la base
    time.sleep(2)


    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)

    print("Regresando a la posición inicial")
    mover_suavemente(servo_hombro, 100, paso=1, delay=0.05)  # Hombro vuelve suavemente
    mover_suavemente(servo_codo, 140, paso=1, delay=0.05)  # Codo vuelve suavemente
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.05)  # Hombro vuelve suavemente

    time.sleep(2)
# ==================== FUNCIÓN PARA EL MOVIMIENTO DE RECOGIDA ====================
def movimiento_verde():
    # Movimiento del hombro suavemente hacia abajo
    mover_suavemente(servo_hombro, 160, paso=2, delay=0.02)
    time.sleep(5)
    
    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.05)  # Hombro con movimiento suave
    time.sleep(2)

    print("Moviendo a la caja")
    mover_suavemente(servo_hombro, 50, paso=1, delay=0.05)  # Movimiento suave del hombro
    mover_suavemente(servo_codo, 40, paso=1, delay=0.05)  # Movimiento suave del codo
    mover_suavemente(servo_hombro, 110, paso=1, delay=0.05)  # Movimiento suave del hombro
    time.sleep(2)
    
    print("Girando la base 90 grados")
    mover_suavemente(servo_base, 180, paso=1, delay=0.05)  # Movimiento suave de la base
    time.sleep(1)


    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)

    print("Regresando a la posición inicial")
    mover_suavemente(servo_hombro, 100, paso=1, delay=0.05)  # Hombro vuelve suavemente
    mover_suavemente(servo_codo, 140, paso=1, delay=0.05)  # Codo vuelve suavemente
    mover_suavemente(servo_hombro, 130, paso=1, delay=0.05)  # Hombro vuelve suavemente

    time.sleep(2)

# ==================== BUCLE PRINCIPAL ====================
while True:
    print("Buscando color...")
    mover_base_continuamente()  # La base gira hasta que detecte un color

    # Ejecutar movimiento_x después de la recogida
    color_detectado = detectar_color()
    print(f"Color detectado: {color_detectado}")
    
    # Si el color se mantiene durante 3 segundos, ejecutar el movimiento correspondiente
    if color_detectado == "azul":
        print("Esperando 1 segundos para confirmar color azul...")
        time.sleep(1)
        color_confirmado = detectar_color()
        if color_confirmado == "azul":
            movimiento_azul()

    elif color_detectado == "rojo":
        print("Esperando 1 segundos para confirmar color rojo...")
        time.sleep(1)
        color_confirmado = detectar_color()
        if color_confirmado == "rojo":
            movimiento_rojo()

    elif color_detectado == "verde":
        print("Esperando 1 segundos para confirmar color verde...")
        time.sleep(1)
        color_confirmado = detectar_color()
        if color_confirmado == "verde":
            movimiento_verde()
              # Secuencia de recogida
              
    #print("Ejecutando recogida...")
    #realizar_movimiento_preesablecido()


    # Volver a buscar color y repetir el proceso
