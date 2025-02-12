import time
import board
import pwmio
import digitalio
from ov7670 import OV7670_30x40_RGB565 as CAM

# Configuración de los servomotores
pwm_servo1 = pwmio.PWMOut(board.GP10, duty_cycle=0, frequency=50)  # hombro
pwm_servo2 = pwmio.PWMOut(board.GP11, duty_cycle=0, frequency=50)  # codo

# Configuración del relé (electroimán) en GP12
rele = digitalio.DigitalInOut(board.GP16)
rele.direction = digitalio.Direction.OUTPUT

# Definir los valores de mínimo y máximo duty cycle para el rango de movimiento
min_duty = 1638  # ~0 grados (1 ms de pulso)
max_duty = 8192  # ~180 grados (2 ms de pulso)

# Inicialización de la cámara OV7670
cam1 = CAM(
    d0_d7pinslist=[board.GP0, board.GP1, board.GP2, board.GP3,
                   board.GP4, board.GP5, board.GP6, board.GP7],
    plk=board.GP8,
    xlk=board.GP9,
    sda=board.GP20,
    scl=board.GP21,
    hs=board.GP12,
    vs=board.GP13,
    ret=board.GP14,
    pwdn=board.GP15
)

# Función para mover un servo de manera pausada
def mover_servo_pausado(pwm, angulo_inicial, angulo_final, pasos=150, tiempo_total=1.5):
    incremento = (angulo_final - angulo_inicial) / pasos
    pausa = tiempo_total / pasos
    
    for i in range(pasos + 1):
        angulo_actual = angulo_inicial + i * incremento
        duty_cycle = max(min(int(min_duty + (angulo_actual / 180) * (max_duty - min_duty)), max_duty), min_duty)
        pwm.duty_cycle = duty_cycle
        time.sleep(pausa)

# Movimiento preestablecido: movimiento_azul
def movimiento_azul():
    print("Ejecutando movimiento azul")
    mover_servo_pausado(pwm_servo1, 90, 150)  # codo
    mover_servo_pausado(pwm_servo2, 90, 160)  # hombro
    time.sleep(1)

    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_servo_pausado(pwm_servo2, 160, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 150, 90)  # codo
    time.sleep(1)

    print("Recogiendo objeto")
    mover_servo_pausado(pwm_servo1, 90, 30)  # codo
    mover_servo_pausado(pwm_servo2, 90, 130)  # hombro
    time.sleep(1)

    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)

    print("Regresando a la posición inicial")
    mover_servo_pausado(pwm_servo2, 130, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 30, 90)  # codo
    time.sleep(1)

# Movimiento preestablecido: movimiento_rojo (puedes cambiar los valores de los ángulos según sea necesario)
def movimiento_rojo():
    print("Ejecutando movimiento rojo")
    mover_servo_pausado(pwm_servo1, 90, 150)  # codo
    mover_servo_pausado(pwm_servo2, 90, 160)  # hombro
    time.sleep(1)

    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_servo_pausado(pwm_servo2, 160, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 150, 90)  # codo
    time.sleep(1)

    print("caja 2")
    mover_servo_pausado(pwm_servo1, 90, 75)  # codo
    mover_servo_pausado(pwm_servo2, 90, 130)  # hombro
    #mover_servo_pausado(pwm_servo1, 90, 40)  # codo
    time.sleep(1)
    
    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)
    
    print("Volviendo a la posición inicial")
    #mover_servo_pausado(pwm_servo1, 40, 90)  # codo
    mover_servo_pausado(pwm_servo2, 130, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 75, 90)  # codo
    time.sleep(1)


# Movimiento preestablecido: movimiento_verde (puedes cambiar los valores de los ángulos según sea necesario)
def movimiento_verde():
    print("Ejecutando movimiento verde")
    mover_servo_pausado(pwm_servo1, 90, 150)  # codo
    mover_servo_pausado(pwm_servo2, 90, 160)  # hombro
    time.sleep(1)

    print("Activando electroimán")
    rele.value = True
    time.sleep(2)

    print("Volviendo a la posición inicial")
    mover_servo_pausado(pwm_servo2, 160, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 150, 90)  # codo
    time.sleep(1)

    print("caja1")
    mover_servo_pausado(pwm_servo2, 90, 130)  # hombro
    mover_servo_pausado(pwm_servo1, 90, 100)  # codo
    time.sleep(1)

    print("Desactivando electroimán")
    rele.value = False
    time.sleep(1)
    
    print("Volviendo a la posición inicial")
    mover_servo_pausado(pwm_servo2, 130, 90)  # hombro
    mover_servo_pausado(pwm_servo1, 100, 90)  # codo
    
# Función para detectar color
def detectar_color():
    try:
        # Captura la imagen en formato RGB565
        buffer = cam1()

        # Contadores para cada color
        azul_count = 0
        rojo_count = 0
        verde_count = 0

        # Recorre cada píxel en el buffer
        for i in range(0, len(buffer), 2):
            # Convierte el valor RGB565 a componentes RGB
            rgb565 = (buffer[i] << 8) | buffer[i + 1]
            r = ((rgb565 >> 11) & 0x1F) * 8   # Componente roja
            g = ((rgb565 >> 5) & 0x3F) * 4    # Componente verde
            b = (rgb565 & 0x1F) * 8           # Componente azul

            # Umbrales para cada color
            if b > 50 and b > (r+3) and b > (g+3):  # Azul predominante
                azul_count += 1
            elif r > 140 and r > (g + 60) and r > (b + 60):  # Rojo predominante
                rojo_count += 1
            elif g > 120 and g > (r + 50) and g > (b + 50):  # Verde predominante
                verde_count += 1

        # Determina el color predominante
        if azul_count > rojo_count and azul_count > verde_count:
            return "azul"
        elif rojo_count > azul_count and rojo_count > verde_count:
            return "rojo"
        elif verde_count > azul_count and verde_count > rojo_count:
            return "verde"
        else:
            return None
    except Exception as e:
        print("Error al capturar la imagen o procesar los datos:", e)
        return None

# Bucle principal
while True:
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

    time.sleep(1)  # Pequeña pausa antes de la siguiente detección
