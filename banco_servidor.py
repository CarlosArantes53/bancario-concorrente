import socket
import threading
import json
from threading import Lock, Semaphore
import datetime

HOST = 'localhost'
PORT = 5000

semaforo = Semaphore()
contas_lock = Lock()
contas = {}

def carregar_contas():
    global contas
    try:
        with open('contas.json', 'r') as f:
            contas = json.load(f)
    except FileNotFoundError:
        contas = {}

def salvar_contas():
    with open('contas.json', 'w') as f:
        json.dump(contas, f, indent=4)

def registrar_transacao(operacao, resposta):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    transacao = {
        'timestamp': timestamp,
        'operacao': operacao,
        'resposta': resposta
    }
    
    try:
        with open('transacoes.json', 'r') as f:
            transacoes = json.load(f)
    except FileNotFoundError:
        transacoes = []

    transacoes.append(transacao)

    with open('transacoes.json', 'w') as f:
        json.dump(transacoes, f, indent=4)


def processar_cliente(conexao, endereco):
    with conexao:
        print(f'Conectado a {endereco}')
        while True:
            try:
                dados = conexao.recv(1024)
                if not dados:
                    break
                operacao = json.loads(dados.decode('utf-8'))
                resposta = processar_operacao(operacao)
                conexao.sendall(json.dumps(resposta).encode('utf-8'))
                registrar_transacao(operacao, resposta)
            except Exception as e:
                print(f"Erro {endereco}: {e}")
                break

def processar_operacao(operacao):
    tipo = operacao['tipo']
    id_conta = operacao['id_conta']

    if tipo == 'consulta':
        return consultar_saldo(id_conta)
    elif tipo == 'deposito':
        return depositar(id_conta, operacao['valor'])
    elif tipo == 'saque':
        return sacar(id_conta, operacao['valor'])
    elif tipo == 'transferencia':
        return transferir(id_conta, operacao['conta_destino'], operacao['valor'])

def consultar_saldo(id_conta):
    with contas_lock:
        saldo = contas.get(id_conta, 0)
        return {'OP': 'Consultar', 'status': 'sucesso', 'saldo': saldo}

def depositar(id_conta, valor):
    with semaforo:
        with contas_lock:
            contas[id_conta] = contas.get(id_conta, 0) + valor
            salvar_contas()
            return {'OP': 'Deposito', 'status': 'sucesso', 'valor': valor, 'saldo_atual': contas[id_conta]}

def sacar(id_conta, valor):
    with semaforo:
        with contas_lock:
            saldo = contas.get(id_conta, 0)
            if saldo >= valor:
                contas[id_conta] = saldo - valor
                salvar_contas()
                return {'OP': 'Saque', 'status': 'sucesso', 'valor': valor, 'saldo_atual': contas[id_conta]}
            else:
                return {'OP': 'Saque', 'status': 'falha', 'mensagem': 'Saldo insuficiente', 'saldo_atual': saldo}

def transferir(id_origem, id_destino, valor):
    with semaforo:
        with contas_lock:
            saldo_origem = contas.get(id_origem, 0)
            if saldo_origem >= valor:
                contas[id_origem] = saldo_origem - valor
                contas[id_destino] = contas.get(id_destino, 0) + valor
                salvar_contas()
                return {'OP': 'Transferencia', 'status': 'sucesso', 'valor': valor, 'saldo_origem': contas[id_origem], 'saldo_destino': contas[id_destino]}
            else:
                return {'OP': 'Transferencia', 'status': 'falha', 'mensagem': 'Saldo insuficiente', 'saldo_origem': saldo_origem}

def iniciar_servidor():
    carregar_contas()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        print(f'Server {HOST}:{PORT}')
        while True:
            conexao, endereco = s.accept()
            threading.Thread(target=processar_cliente, args=(conexao, endereco)).start()

if __name__ == '__main__':
    iniciar_servidor()
