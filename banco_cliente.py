import socket
import json
import random
import time
import threading

HOST = 'localhost'
PORT = 5000

def realizar_transacao(id_cliente):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        while True:
            try:
                s.connect((HOST, PORT))
                break
            except ConnectionRefusedError:
                time.sleep(1)

        operacoes = ['consulta', 'deposito', 'saque', 'transferencia']
        tipo = random.choice(operacoes)

        transacao = {'tipo': tipo, 'id_conta': id_cliente}
        if tipo == 'deposito':
            transacao['valor'] = random.randint(10, 1000)
        elif tipo == 'saque':
            transacao['valor'] = random.randint(10, 500)
        elif tipo == 'transferencia':
            transacao['conta_destino'] = random.randint(1, 5)
            transacao['valor'] = random.randint(10, 500)

        s.sendall(json.dumps(transacao).encode('utf-8'))
        resposta = s.recv(1024)
        print(f'Cliente {id_cliente}: {resposta.decode("utf-8")}')
        time.sleep(random.uniform(0.01, 0.5))

def simular_clientes(num_clientes, num_transacoes):
    threads = []
    for i in range(num_clientes):
        for _ in range(num_transacoes):
            t = threading.Thread(target=realizar_transacao, args=(i,))
            threads.append(t)
            t.start()
            time.sleep(0.05)

    for t in threads:
        t.join()

if __name__ == '__main__':
    num_clientes = int(input("Clientes: "))
    num_transacoes = int(input("Transações: "))
    simular_clientes(num_clientes, num_transacoes)
