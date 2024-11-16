from PIL import Image
import reedsolo

#convierte una cadena alfanumerica en binario
def text_to_binary(data):
    # convierte cada caracter de la cadena a su representacion binaria de 8 bits.
    binary = ''.join(format(ord(char), '08b') for char in data)
    return binary

#genera bytes de correccion de errores usando reed-solomon
def reed_solomon_correction(data, ecc_length=10):
    #crea un objeto rscodec con una longitud de codigo de correccion de errores (ecc_length).
    rs = reedsolo.RSCodec(ecc_length)
    #codifica los datos (los convierte en bytes de correccion).
    encoded_data = rs.encode(bytearray(data.encode('utf-8')))
    # devuelve los ultimos 'ecc_length' bytes de correccion de errores generados.
    return encoded_data[-ecc_length:]

#crea una matriz vacia para el qr de tamaño 21x21
def create_qr_matrix(size=21):
    # crea una matriz de tamaño 'size' por 'size' llena de ceros (representa un fondo blanco)
    return [[0 for _ in range(size)] for _ in range(size)]

# añade los tres marcadores de posicion (esquinas) en la matriz qr
# marcadores en la esquina superior izquierda, superior derecha, y esquina inferior izquierda
def add_position_markers(matrix):
    size = len(matrix)  #obtiene el tamaño de la matriz qr
    #recorre el rango de 7x7 para colocar los marcadores en la esquina superior izquierda
    for i in range(7):
        for j in range(7):
            #pone 1 en las celdas que corresponden a las regiones de los marcadores
            if (i in (0, 6) or j in (0, 6)) or (2 <= i <= 4 and 2 <= j <= 4):
                matrix[i][j] = 1  # asigna el valor 1 (negro) en las celdas de los marcadores
    #recorre el rango de 7x7 para colocar los marcadores en la esquina superior derecha
    for i in range(7):
        for j in range(size - 7, size):
            #oloca 1 en las celdas que corresponden a las regiones de los marcadores
            if (i in (0, 6) or j in (size - 7, size - 1)) or (2 <= i <= 4 and size - 5 <= j <= size - 3):
                matrix[i][j] = 1  # asigna el valor 1 (negro) en las celdas de los marcadores
    #recorre el rango de 7x7 para colocar los marcadores en la esquina inferior izquierda
    for i in range(size - 7, size):
        for j in range(7):
            #coloca 1 en las celdas que corresponden a las regiones de los marcadores
            if (i in (size - 7, size - 1) or j in (0, 6)) or (size - 5 <= i <= size - 3 and 2 <= j <= 4):
                matrix[i][j] = 1  # asigna el valor 1 (negro) en las celdas de los marcadores
    return matrix  

#añade los patrones de temporizacion a la matriz
def add_timing_patterns(matrix):
    size = len(matrix)  #obtiene el tamaño de la matriz qr
    #Añade los patrones de temporizacion horizontales en la fila 6
    for col in range(8, size - 8):  # recorre las columnas de la fila 6
        matrix[6][col] = 1 if col % 2 == 0 else 0  #alterna entre 1 y 0
    #añade los patrones de temporizacion verticales en la columna 6
    for row in range(8, size - 8):# recorre las filas de la columna 6
        matrix[row][6] = 1 if row % 2 == 0 else 0 # alterna entre 1 y 0
    return matrix  #devuelve la matriz con los patrones de temporizacion añadidos

# verifica si la celda esta ocupada por un marcador o patron de temporizacion
def is_reserved(matrix, row, col):
    size = len(matrix)  # obtiene el tamaño de la matriz qr
    #verifica si la celda esta dentro de los bordes de los marcadores de posicion o en la fila/columna de temporizacion
    if (row < 7 and col < 7) or (row < 7 and col >= size - 7) or (row >= size - 7 and col < 7):
        return True  #devuelve True si la celda esta en una de las zonas reservadas
    if (row == 6 or col == 6): #verifica si la celda esta en la fila o columna 6 (patron de temporizacion)
        return True  # devuelve True si la celda esta en el patron de temporizacion
    return False  # devuelve False si la celda no esta reservada

# añade los datos binarios y de correccion al qr
def add_data_to_qr(matrix, data):
    binary_data = text_to_binary(data)  # convierte el texto a binario
    #obtiene los bytes de correccion de errores utilizando reed-solomon
    ecc_data = reed_solomon_correction(data)
    binary_ecc = ''.join(format(byte, '08b') for byte in ecc_data)  # convierte los bytes de correccion a binario
    #combina los datos binarios y los datos de correccion de errores en una secuencia completa
    full_binary = binary_data + binary_ecc
    index = 0  # inicializa el indice para recorrer los datos
    size = len(matrix)  #obtiene el tamaño de la matriz qr
    #añade los datos a la matriz qr en las posiciones adecuadas
    for col in range(size - 1, 0, -2):  #recorre las columnas de derecha a izquierda, saltandose las celdas reservadas
        if col == 6:  #ajustamos para evitar que el patron de temporizacion (columna 6) sea sobreescrito
            col -= 1
        for row in (range(size - 1, -1, -1) if col % 4 == 1 else range(size)):  #recorre las filas
            if not is_reserved(matrix, row, col):  #verifica que la celda no sea reservada
                if index < len(full_binary):  #verifica si hay mas datos por añadir
                    matrix[row][col] = int(full_binary[index])  #asigna el bit de datos en la celda
                    index += 1  # incrementa el indice
    return matrix 

# aplica una mascara al qr para mejorar su legibilidad
def apply_mask(matrix):
    size = len(matrix)  #obtiene el tamaño de la matriz qr
    #recorre cada celda de la matriz y aplica una mascara para mejorar el contraste
    for row in range(size):  #recorre las filas de la matriz qr
        for col in range(size):  # recorre las columnas de la matriz qr
            if not is_reserved(matrix, row, col):  # verifica que la celda no sea reservada
                #invierte el bit si (row + col) % 2 == 0
                if (row + col) % 2 == 0:  #aplica la mascara en las celdas correspondientes
                    matrix[row][col] = 1 - matrix[row][col]  # invierte el valor de la celda
    return matrix  # devuelve la matriz con la mascara aplicada

#convierte la matriz qr en una imagen.
def matrix_to_image(matrix, pixel_size=10):
    size = len(matrix)
    # crea una nueva imagen de blanco (1 = blanco)
    img = Image.new('1', (size * pixel_size, size * pixel_size), 1)
    for row in range(size):
        for col in range(size):
            #si el valor es 1 (negro), coloca el pixel negro, de lo contrario blanco
            color = 255 if matrix[row][col] == 0 else 0
            for i in range(pixel_size):
                for j in range(pixel_size):
                    img.putpixel((col * pixel_size + j, row * pixel_size + i), color)
    return img

#onvierte la matriz qr en una imagen y la guarda con un nombre dado
def save_qr_image(matrix, filename="qr_code.png"):
    img = matrix_to_image(matrix)
    # guarda la imagen generada en un archivo png
    img.save(filename)

# funcion principal 
def main():
    text = input("Ingresa el texto para generar el codigo qr: ")
    #crea una matriz qr de tamaño 21x21
    qr_matrix = create_qr_matrix(21)
    #añade los marcadores de posicion a la matriz
    qr_matrix = add_position_markers(qr_matrix)
    #añade los patrones de temporizacion a la matriz
    qr_matrix = add_timing_patterns(qr_matrix)
    #añade los datos binarios y de correccion de errores a la matriz
    qr_matrix = add_data_to_qr(qr_matrix, text)
    #aplica una mascara a la matriz qr
    qr_matrix = apply_mask(qr_matrix)
    #guarda la imagen qr generada en un archivo
    save_qr_image(qr_matrix, "qr_code.png")
    print("qr generado y guardado como 'qr_code.png'")

# ejecuta la funcion principal
if __name__ == "__main__":
    main()
