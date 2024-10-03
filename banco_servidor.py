import socket
import threading
import json
import time
from threading import Lock, Semaphore

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
        json.dump(contas, f)

def processar_cliente(conexao, endereco):
    with conexao:
        print(f'Conectado a {endereco}')
        
        while True:
            try:
                dados = conexao.recv(1024)
                if not dados:
                    break
                dados = dados.decode('utf-8')
                operacao = json.loads(dados)
                resposta = processar_operacao(operacao)
                conexao.sendall(json.dumps(resposta).encode('utf-8'))
            except Exception as e:
                print(f"Erro no processamento do cliente {endereco}: {e}")
                break

def processar_operacao(operacao):
    tipo = operacao['tipo']
    id_conta = operacao['id_conta']

    if tipo == 'consulta':
        return consultar_saldo(id_conta)
    elif tipo == 'deposito':
        valor = operacao['valor']
        return depositar(id_conta, valor)
    elif tipo == 'saque':
        valor = operacao['valor']
        return sacar(id_conta, valor)
    elif tipo == 'transferencia':
        conta_destino = operacao['conta_destino']
        valor = operacao['valor']
        return transferir(id_conta, conta_destino, valor)

def consultar_saldo(id_conta):
    with contas_lock:
        saldo = contas.get(id_conta, 0)
        return {'status': 'sucesso', 'saldo': saldo}

def depositar(id_conta, valor):
    with semaforo:
        with contas_lock:
            saldo = contas.get(id_conta, 0)
            contas[id_conta] = saldo + valor
            salvar_contas()
            return {'status': 'sucesso', 'saldo': contas[id_conta]}

def sacar(id_conta, valor):
    with semaforo:
        with contas_lock:
            saldo = contas.get(id_conta, 0)
            if saldo >= valor:
                contas[id_conta] = saldo - valor
                salvar_contas()
                return {'status': 'sucesso', 'saldo': contas[id_conta]}
            else:
                return {'status': 'falha', 'mensagem': 'Saldo insuficiente'}

def transferir(id_origem, id_destino, valor):
    with semaforo:
        with contas_lock:
            saldo_origem = contas.get(id_origem, 0)
            if saldo_origem >= valor:
                contas[id_origem] = saldo_origem - valor
                contas[id_destino] = contas.get(id_destino, 0) + valor
                salvar_contas()
                return {'status': 'sucesso', 'saldo_origem': contas[id_origem], 'saldo_destino': contas[id_destino]}
            else:
                return {'status': 'falha', 'mensagem': 'Saldo insuficiente'}

def iniciar_servidor():
    carregar_contas()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()

        print(f'Servidor bancário rodando em {HOST}:{PORT}')
        while True:
            conexao, endereco = s.accept()
            threading.Thread(target=processar_cliente, args=(conexao, endereco)).start()

if __name__ == '__main__':
    iniciar_servidor()