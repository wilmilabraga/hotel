from datetime import datetime


class Cliente:
    def __init__(self, nome, tipo):
        self.nome = nome
        self.tipo = tipo


class Individual(Cliente):
    def __init__(self, nome, nif):
        super().__init__(nome, 'Individual')
        self.nif = nif


class Organizacao(Cliente):
    def __init__(self, nome, contacto, nipc):
        super().__init__(nome, 'Organizacao')
        self.contacto = contacto
        self.nipc = nipc


class Quarto:
    def __init__(self, numero, num_camas, preco):
        self.numero = numero
        self.num_camas = num_camas
        self.preco = preco


class Reserva:
    def __init__(self, entrada, saida):
        self.entrada = entrada
        self.saida = saida

    def calcular_noites(self):
        d1 = datetime.strptime(self.entrada, '%Y-%m-%d')
        d2 = datetime.strptime(self.saida, '%Y-%m-%d')
        return (d2 - d1).days


class Fatura:
    def __init__(self, valor):
        self.valor = valor