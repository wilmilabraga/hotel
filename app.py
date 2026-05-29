from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
import sqlite3

app = Flask(__name__)
app.secret_key = 'vitta_resort_secret_key_2024'

def conectar():
    conn = sqlite3.connect('hotel.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reservas')
def listar_reservas():
    conn = conectar()
    reservas = conn.execute('''
        SELECT reserva.*, cliente.nome as cliente_nome, quarto.nome as quarto_nome
        FROM reserva
        JOIN cliente ON reserva.num_cliente = cliente.num_cliente
        JOIN quarto ON reserva.quarto = quarto.numero
        ORDER BY reserva.data_reserva DESC
    ''').fetchall()
    conn.close()
    return render_template('reservas.html', reservas=reservas)

@app.route('/reservas/nova', methods=['GET', 'POST'])
def nova_reserva():
    conn = conectar()
    
    if request.method == 'POST':
        try:
            # Log para debug
            print("=== Dados recebidos ===")
            print(f"Nome: {request.form.get('nome')}")
            print(f"Email: {request.form.get('email')}")
            print(f"Telefone: {request.form.get('telefone')}")
            print(f"Quarto: {request.form.get('quarto')}")
            print(f"Entrada: {request.form.get('entrada')}")
            print(f"Saída: {request.form.get('saida')}")
            print(f"Pessoas: {request.form.get('pessoas')}")
            print(f"Cama extra: {request.form.get('camaextra')}")
            
            nome = request.form.get('nome')
            email = request.form.get('email')
            telefone = request.form.get('telefone')
            quarto_num = int(request.form.get('quarto'))
            entrada = request.form.get('entrada')
            saida = request.form.get('saida')
            pessoas = int(request.form.get('pessoas'))
            camaextra = int(request.form.get('camaextra', 0))
            
            # Validar datas
            if not entrada or not saida:
                return jsonify({'error': 'Datas não informadas'}), 400
            
            data_entrada = datetime.strptime(entrada, '%Y-%m-%d')
            data_saida = datetime.strptime(saida, '%Y-%m-%d')
            
            if data_saida <= data_entrada:
                return jsonify({'error': 'Data de saída deve ser maior que data de entrada'}), 400
            
            # Verificar se cliente já existe
            cliente = conn.execute(
                'SELECT num_cliente FROM cliente WHERE email = ?', (email,)
            ).fetchone()
            
            if cliente:
                cliente_id = cliente['num_cliente']
            else:
                cursor = conn.execute('''
                    INSERT INTO cliente (nome, contacto, email, tipo, data_cadastro)
                    VALUES (?, ?, ?, ?, ?)
                ''', (nome, telefone, email, 'Individual', datetime.now().strftime('%Y-%m-%d')))
                cliente_id = cursor.lastrowid
            
            # Verificar disponibilidade do quarto
            conflito = conn.execute('''
                SELECT COUNT(*) as total FROM reserva
                WHERE quarto = ? AND status = 'confirmada'
                AND dia_entrada < ? AND dia_saida > ?
            ''', (quarto_num, saida, entrada)).fetchone()
            
            if conflito['total'] > 0:
                return jsonify({'error': 'Quarto não disponível para o período selecionado'}), 400
            
            # Criar reserva
            cursor = conn.execute('''
                INSERT INTO reserva (num_cliente, quarto, dia_entrada, dia_saida, camaextra, num_pessoas, data_reserva, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cliente_id, quarto_num, entrada, saida, camaextra, pessoas, 
                  datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'confirmada'))
            
            reserva_id = cursor.lastrowid
            
            # Calcular valor
            quarto_info = conn.execute('SELECT preco FROM quarto WHERE numero = ?', (quarto_num,)).fetchone()
            if not quarto_info:
                return jsonify({'error': 'Quarto não encontrado'}), 400
                
            noites = (data_saida - data_entrada).days
            valor = (quarto_info['preco'] * noites) + (camaextra * 50)
            
            # Criar fatura
            conn.execute('''
                INSERT INTO fatura (num_reserva, data, valor, pago)
                VALUES (?, ?, ?, ?)
            ''', (reserva_id, datetime.now().strftime('%Y-%m-%d'), valor, 0))
            
            conn.commit()
            conn.close()
            
            flash('✅ Reserva realizada com sucesso!', 'success')
            return redirect(url_for('listar_reservas'))
            
        except Exception as e:
            print(f"❌ Erro: {str(e)}")
            conn.close()
            return jsonify({'error': f'Erro ao processar reserva: {str(e)}'}), 500
    
    # GET - Mostrar formulário
    quartos = conn.execute('SELECT * FROM quarto').fetchall()
    conn.close()
    return render_template('index.html', quartos=quartos)

@app.route('/reservas/cancelar/<int:reserva_id>')
def cancelar_reserva(reserva_id):
    conn = conectar()
    conn.execute('UPDATE reserva SET status = ? WHERE num_reserva = ?', ('cancelada', reserva_id))
    conn.commit()
    conn.close()
    flash('❌ Reserva cancelada com sucesso!', 'warning')
    return redirect(url_for('listar_reservas'))

@app.route('/faturas')
def listar_faturas():
    conn = conectar()
    faturas = conn.execute('''
        SELECT fatura.*, cliente.nome as cliente_nome, reserva.num_reserva
        FROM fatura
        JOIN reserva ON fatura.num_reserva = reserva.num_reserva
        JOIN cliente ON reserva.num_cliente = cliente.num_cliente
        ORDER BY fatura.data DESC
    ''').fetchall()
    conn.close()
    return render_template('faturas.html', faturas=faturas)

@app.route('/faturas/pagar/<int:fatura_id>')
def pagar_fatura(fatura_id):
    conn = conectar()
    conn.execute('UPDATE fatura SET pago = 1 WHERE num_fatura = ?', (fatura_id,))
    conn.commit()
    conn.close()
    flash('💰 Fatura paga com sucesso!', 'success')
    return redirect(url_for('listar_faturas'))

@app.route('/admin')
def admin():
    conn = conectar()
    stats = {
        'total_reservas': conn.execute('SELECT COUNT(*) as total FROM reserva').fetchone()['total'],
        'total_clientes': conn.execute('SELECT COUNT(*) as total FROM cliente').fetchone()['total'],
        'faturamento_total': conn.execute('SELECT SUM(valor) as total FROM fatura WHERE pago = 1').fetchone()['total'] or 0
    }
    reservas_recentes = conn.execute('''
        SELECT reserva.*, cliente.nome as cliente_nome, quarto.nome as quarto_nome
        FROM reserva
        JOIN cliente ON reserva.num_cliente = cliente.num_cliente
        JOIN quarto ON reserva.quarto = quarto.numero
        ORDER BY reserva.data_reserva DESC LIMIT 10
    ''').fetchall()
    conn.close()
    return render_template('admin.html', stats=stats, reservas_recentes=reservas_recentes)

@app.route('/api/datas-ocupadas')
def api_datas_ocupadas():
    """Retorna as datas ocupadas para um quarto específico"""
    quarto = request.args.get('quarto')
    
    if not quarto:
        return jsonify({'datas': []})
    
    conn = conectar()
    reservas = conn.execute('''
        SELECT dia_entrada, dia_saida FROM reserva
        WHERE quarto = ? AND status = 'confirmada'
    ''', (quarto,)).fetchall()
    conn.close()
    
    datas_ocupadas = []
    for reserva in reservas:
        entrada = datetime.strptime(reserva['dia_entrada'], '%Y-%m-%d')
        saida = datetime.strptime(reserva['dia_saida'], '%Y-%m-%d')
        
        current = entrada
        while current < saida:
            datas_ocupadas.append(current.strftime('%Y-%m-%d'))
            current += timedelta(days=1)
    
    return jsonify({'datas': datas_ocupadas})

@app.route('/api/verificar-disponibilidade')
def api_verificar_disponibilidade():
    """Verifica se um quarto está disponível para um período"""
    quarto = request.args.get('quarto')
    entrada = request.args.get('entrada')
    saida = request.args.get('saida')
    
    if not all([quarto, entrada, saida]):
        return jsonify({'disponivel': False, 'motivo': 'Parâmetros inválidos'})
    
    conn = conectar()
    conflito = conn.execute('''
        SELECT COUNT(*) as total FROM reserva
        WHERE quarto = ? AND status = 'confirmada'
        AND dia_entrada < ? AND dia_saida > ?
    ''', (quarto, saida, entrada)).fetchone()
    conn.close()
    
    if conflito['total'] > 0:
        return jsonify({'disponivel': False, 'motivo': 'Período já reservado'})
    
    return jsonify({'disponivel': True})

if __name__ == '__main__':
    app.run(debug=True) 