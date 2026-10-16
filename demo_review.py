def calcular_media(valores=[]):
    total = 0
    for v in valores:
        total += v
    return total / len(valores)


print(calcular_media())
