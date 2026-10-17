import random
import sys

LEVEL_NAMES = {
    1: "Blocos de Memória",
    2: "Underline",
    3: "Ciclos de Clock",
    4: "Breakpoints",
    5: "Listras de Carregamento",
    6: "Depuração de Sistema",
    7: "Lançamento Mega",
    8: "Dithering",
    9: "Código Morse",
    10: "Linhas de Diff",
    11: "Tela Dividida",
    12: "Grade de Pixels",
    13: "Inicialização Dupla",
    14: "Ondulação",
    15: "Thread Dupla",
    16: "Código Comentado",
    17: "Lançamento Giga",
    18: "Forma de Onda",
    19: "Merge de Branches",
    20: "Trilha de Circuito",
    21: "Dobra de Código",
    22: "Poeira de Pixels",
    23: "Código Aberto",
    24: "Tabela Zebrada",
    25: "Pilha de Chamadas",
    26: "Papel Quadriculado",
    27: "Régua de Coluna",
    28: "Repo Fixado",
    29: "Lançamento Tera",
    30: "Sonar",
    31: "Cursor Piscante",
    32: "Mapa de Altura",
    33: "Par de Colchetes",
    34: "Placa-mãe",
    35: "Reexecução",
    36: "Piso de Ruído",
    37: "Acesso Beta",
    38: "Fita Zebrada",
    39: "Fluxo de Tokens",
    40: "Histórico de Commits",
    41: "Lançamento Peta",
}

TIER_NAMES = {
    (1, 6): "Kilo",
    (7, 16): "Mega",
    (17, 28): "Giga",
    (29, 40): "Tera",
    (41, 41): "Peta",
}


def tier_of(level):
    for (lo, hi), name in TIER_NAMES.items():
        if lo <= level <= hi:
            return name
    return "Peta"


class Player:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.max_hp = 100
        self.hp = 100
        self.attack = 12
        self.defense = 5
        self.potions = 3

    def heal(self):
        amount = 30 + self.level * 5
        self.hp = min(self.max_hp, self.hp + amount)
        return amount

    def level_up(self):
        self.level += 1
        self.max_hp += 20
        self.hp = self.max_hp
        self.attack += 3
        self.defense += 1
        self.potions += 1


class Enemy:
    def __init__(self, level):
        self.level = level
        self.name = f"Bug Nível {level}"
        self.hp = 40 + level * 8
        self.max_hp = self.hp
        self.attack = 6 + level * 2
        self.defense = 2 + level // 3


def clear():
    print("\n" * 2)


def header(player):
    clear()
    print("=" * 50)
    print(f"  Jogador: {player.name}  |  Nível {player.level} [{tier_of(player.level)}]")
    print(f"  HP: {player.hp}/{player.max_hp}  |  ATK: {player.attack}  |  DEF: {player.defense}  |  Poções: {player.potions}")
    print("=" * 50)


def combat(player, level_name):
    enemy = Enemy(player.level)
    print(f"\nNível {player.level}: {level_name}")
    print(f"Um {enemy.name} apareceu! (HP {enemy.hp})")

    while player.hp > 0 and enemy.hp > 0:
        print(f"\n[{player.hp}/{player.max_hp} HP]  [{enemy.hp}/{enemy.max_hp} HP]")
        print("(A) Atacar  (C) Curar  (D) Defender")
        choice = input("> ").strip().lower()

        if choice == "a":
            dmg = max(1, player.attack - enemy.defense // 2 + random.randint(-2, 4))
            enemy.hp -= dmg
            print(f"Você causou {dmg} de dano!")
            if enemy.hp <= 0:
                break
            edmg = max(1, enemy.attack - player.defense // 2 + random.randint(-2, 3))
            player.hp -= edmg
            print(f"O bug causou {edmg} de dano!")
        elif choice == "c":
            if player.potions > 0:
                healed = player.heal()
                player.potions -= 1
                print(f"Você curou {healed} HP! Poções restantes: {player.potions}")
                edmg = max(1, enemy.attack - player.defense // 2 + random.randint(-2, 3))
                player.hp -= edmg
                print(f"O bug causou {edmg} de dano enquanto você curava!")
            else:
                print("Sem poções!")
                edmg = max(1, enemy.attack - player.defense // 2 + random.randint(-2, 3))
                player.hp -= edmg
                print(f"O bug causou {edmg} de dano!")
        elif choice == "d":
            print("Você se defende e reduz o dano próximo.")
            edmg = max(1, (enemy.attack - player.defense) // 2 + random.randint(-1, 2))
            player.hp -= edmg
            print(f"O bug causou {edmg} de dano!")
        else:
            print("Ação inválida, o bug aproveita!")
            edmg = max(1, enemy.attack - player.defense // 2 + random.randint(-2, 3))
            player.hp -= edmg
            print(f"O bug causou {edmg} de dano!")

    return player.hp > 0


def main():
    clear()
    print("BEM-VINDO AO JOGO DE NÍVEIS (1 a 41)")
    print("Sem XP. Apenas progressão de nível.\n")
    nome = input("Digite seu nome: ").strip() or "Dev"
    player = Player(nome)

    while player.level <= 41:
        header(player)
        level_name = LEVEL_NAMES[player.level]
        print(f"\nDesafio atual: {level_name}")
        print("(J) Jogar nível  (S) Sair")
        choice = input("> ").strip().lower()
        if choice == "s":
            print("Até logo!")
            sys.exit(0)

        if not combat(player, level_name):
            print("\nVocê foi derrotado! Fim de jogo.")
            break

        print(f"\nVocê completou o nível {player.level}: {level_name}!")
        old_tier = tier_of(player.level - 1)
        player.level_up()
        new_tier = tier_of(player.level)
        if new_tier != old_tier:
            print(f"*** NOVO TIER: {new_tier} ***")
        input("\nPressione Enter para continuar...")

    header(player)
    print("\nPARABÉNS! Você alcançou o nível 41 (Peta)!")


if __name__ == "__main__":
    main()