import sqlite3


def conectar():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS cliente (
        num_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        tipo TEXT NOT NULL,
        nif TEXT,
        contacto TEXT,
        nipc TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS quarto (
        numero INTEGER PRIMARY KEY,
        num_camas INTEGER,
        preco REAL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reserva (
        num_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
        num_cliente INTEGER,
        quarto INTEGER,
        dia_entrada TEXT,
        dia_saida TEXT,
        camaextra INTEGER,
        num_pessoas INTEGER,
        FOREIGN KEY(num_cliente) REFERENCES cliente(num_cliente),
        FOREIGN KEY(quarto) REFERENCES quarto(numero)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fatura (
        num_fatura INTEGER PRIMARY KEY AUTOINCREMENT,
        num_reserva INTEGER,
        data TEXT,
        valor REAL,
        FOREIGN KEY(num_reserva) REFERENCES reserva(num_reserva)
    )
    ''')

    conn.commit()
    conn.close()