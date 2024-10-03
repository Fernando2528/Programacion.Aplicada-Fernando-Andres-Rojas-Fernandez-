import board
import busio
import adafruit_ssd1306
import math
import time

# Configuración de la pantalla OLED
i2c = busio.I2C(board.GP1, board.GP0)
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)

# Limpiar pantalla
oled.fill(0)
oled.show()

# Función para dibujar el brazo
def dibujar_brazo(base_x, base_y, longitud1, angulo1, longitud2, angulo2):
    # Cálculo del extremo del primer segmento
    x1 = int(base_x + longitud1 * math.cos(math.radians(angulo1)))
    y1 = int(base_y + longitud1 * math.sin(math.radians(angulo1)))
    
    # Cálculo del extremo del segundo segmento, relativo al ángulo del primero
    x2 = int(x1 + longitud2 * math.cos(math.radians(angulo1 + angulo2)))
    y2 = int(y1 + longitud2 * math.sin(math.radians(angulo1 + angulo2)))

    # Limpiar pantalla
    oled.fill(0)
    
    # Dibujar primer segmento
    oled.line(base_x, base_y, x1, y1, 1)
    
    # Dibujar segundo segmento
    oled.line(x1, y1, x2, y2, 1)
    
    # Actualizar pantalla
    oled.show()

# Parámetros del brazo
# Reubicar la base en una posición más centrada
base_x, base_y = 64, 32  # Base en el centro de la pantalla
longitud1 = 30  # Longitud del primer segmento
longitud2 = 20  # Longitud del segundo segmento

# Ciclo para variar los ángulos dinámicamente
while True:
    for angulo1 in range(0, 91, 5):  # Variar el primer ángulo de 0 a 90 grados
        for angulo2 in range(-90, 91, 5):  # Variar el segundo ángulo de -90 a 90 grados
            # Dibujar el brazo con los ángulos actuales
            dibujar_brazo(base_x, base_y, longitud1, angulo1, longitud2, angulo2)
            time.sleep(0.1)  # Pausa pequeña para visualizar el movimiento
