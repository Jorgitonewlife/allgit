# Aula 02: Variáveis, tipos e entrada de dados

# --- 1. Tipos básicos ---
nome = "Jorge"       # str (texto)
idade = 25           # int (inteiro)
altura = 1.75        # float (decimal)
programando = True   # bool (True/False)

# --- 2. f-strings: o jeito moderno de juntar texto e variáveis ---
print(f"Meu nome é {nome} e tenho {idade} anos.")

# --- 3. input(): ler o que o usuário digita (sempre vem como texto!) ---
# nome_digitado = input("Qual seu nome? ")
# print(f"Olá, {nome_digitado}!")

# --- 4. Convertendo tipos ---
# numero_texto = input("Digite um número: ")  # ex: "7" (texto)
# numero = int(numero_texto)                   # vira 7 (inteiro)
# print(f"O dobro é {numero * 2}")

# Duas conversões úteis: int() para inteiro, float() para decimal.


# ============================================================
# EXERCÍCIOS (apague o 'pass' e escreva seu código abaixo)
# ============================================================

# Ex 1: crie uma variável 'cidade' com sua cidade e imprima
# "Eu moro em <cidade>." usando f-string.
cidade = "São Paulo"
print(f"Eu moro em {cidade}.")


# Ex 2: peça ao usuário dois números (input + int) e imprima
# a soma, a subtração e a multiplicação deles.
num1 = int(input("Digite o primeiro número: "))
num2 = int(input("Digite o segundo número: "))
print(f"Soma: {num1 + num2}")
print(f"Subtração: {num1 - num2}")
print(f"Multiplicação: {num1 * num2}")


# Ex 3 (desafio): peça nome, idade e altura. Imprima tudo
# em UMA frase. Converta idade para int e altura para float.
nome = input("Digite seu nome: ")
idade = int(input("Digite sua idade: "))
altura = float(input("Digite sua altura: "))
print(f"Meu nome é {nome}, tenho {idade} anos e medo {altura}m.")
