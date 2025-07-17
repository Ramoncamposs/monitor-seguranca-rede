"""
Módulo de Scanner de Rede Simples
Este arquivo contém funções básicas para escanear portas em uma rede.
"""
import socket
import time
import subprocess
import platform
import ipaddress

def scan_port(ip, port, timeout=1):
    """
    Verifica se uma porta específica está aberta em um endereço IP.
    
    Args:
        ip (str): O endereço IP a ser escaneado
        port (int): O número da porta a ser verificada
        timeout (float): Tempo limite em segundos para a tentativa de conexão
        
    Returns:
        bool: True se a porta estiver aberta, False caso contrário
    """
    # Cria um objeto socket para tentar a conexão
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Define um tempo limite para a tentativa de conexão
    s.settimeout(timeout)
    
    try:
        # Tenta conectar ao IP e porta especificados
        # Se retornar 0, a conexão foi bem-sucedida (porta aberta)
        result = s.connect_ex((ip, port))
        
        # Verifica se a conexão foi bem-sucedida
        if result == 0:
            # Tenta enviar dados para verificar se a porta realmente aceita conexões
            try:
                s.send(b"\r\n")
                s.close()
                return True
            except:
                s.close()
                # Se não conseguir enviar dados, pode ser um falso positivo
                # especialmente em localhost com firewall
                if ip == "127.0.0.1" or ip == "localhost":
                    print(" [VERIFICANDO FIREWALL]", end="")
                    # Verifica se há regras de firewall bloqueando a porta
                    if is_port_blocked_by_firewall(port):
                        print(" [BLOQUEADA POR FIREWALL]")
                        return False
                return True
        else:
            s.close()
            return False
    except:
        # Em caso de erro (ex: IP inválido), retorna False
        s.close()
        return False

def is_port_blocked_by_firewall(port):
    """
    Verifica se uma porta está bloqueada pelo firewall (apenas Linux).
    
    Args:
        port (int): O número da porta a verificar
        
    Returns:
        bool: True se a porta estiver bloqueada, False caso contrário ou se não for possível verificar
    """
    if platform.system() != "Linux":
        return False
    
    try:
        # Verifica regras de UFW
        ufw_output = subprocess.check_output(["sudo", "ufw", "status"], stderr=subprocess.DEVNULL).decode('utf-8')
        if f"{port}/tcp" in ufw_output or f"{port}" in ufw_output and "DENY" in ufw_output:
            return True
        
        # Verifica regras de iptables
        iptables_output = subprocess.check_output(["sudo", "iptables", "-L", "-n"], stderr=subprocess.DEVNULL).decode('utf-8')
        if f"dpt:{port}" in iptables_output and ("DROP" in iptables_output or "REJECT" in iptables_output):
            return True
            
        return False
    except:
        # Se não conseguir verificar, assume que não está bloqueado
        return False

def scan_common_ports(ip):
    """
    Escaneia as portas mais comuns em um endereço IP.
    
    Args:
        ip (str): O endereço IP a ser escaneado
        
    Returns:
        dict: Dicionário com as portas escaneadas e seus estados (True=aberta, False=fechada)
    """
    # Lista de portas comuns para escanear
    common_ports = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        3306: "MySQL",
        3389: "RDP"
    }
    
    results = {}
    print(f"Escaneando portas comuns em {ip}...")
    
    # Escaneia cada porta da lista
    for port, service in common_ports.items():
        print(f"Verificando porta {port} ({service})...", end="")
        is_open = scan_port(ip, port)
        results[port] = is_open
        
        if is_open:
            print(" [ABERTA]")
        else:
            print(" [FECHADA]")
        
        # Pequena pausa para não sobrecarregar a rede
        time.sleep(0.1)
    
    return results

def ping_host(ip):
    """
    Verifica se um host está acessível através de ping.
    
    Args:
        ip (str): O endereço IP a ser verificado
        
    Returns:
        bool: True se o host responder ao ping, False caso contrário
    """
    # Comando de ping varia conforme o sistema operacional
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    # Executa apenas 2 pings para ser rápido
    command = ['ping', param, '2', ip]
    
    try:
        # Executa o comando e verifica se retornou com sucesso (código 0)
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
    except:
        return False

def discover_network_ips():
    """
    Descobre IPs na rede local que estão acessíveis.
    
    Returns:
        list: Lista de IPs acessíveis na rede local
    """
    # Tenta obter o IP da própria máquina para determinar a rede
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    
    # Determina o prefixo da rede (assumindo uma máscara /24 comum em redes domésticas)
    ip_parts = local_ip.split('.')
    network_prefix = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}."
    
    print(f"Descobrindo dispositivos na rede {network_prefix}0/24...")
    print("(Este processo pode levar alguns minutos)")
    
    # Lista para armazenar IPs acessíveis
    reachable_ips = []
    
    # Adiciona o localhost e o IP local à lista
    reachable_ips.append("127.0.0.1")  # localhost
    if local_ip != "127.0.0.1":
        reachable_ips.append(local_ip)
    
    # Testa alguns IPs comuns na rede local
    common_last_octets = [1, 100, 101, 102, 254]  # Roteador e alguns dispositivos comuns
    
    for last_octet in common_last_octets:
        ip = f"{network_prefix}{last_octet}"
        if ip != local_ip:  # Evita testar o próprio IP novamente
            print(f"Verificando {ip}...", end="")
            if ping_host(ip):
                print(" [ALCANÇÁVEL]")
                reachable_ips.append(ip)
            else:
                print(" [NÃO ALCANÇÁVEL]")
    
    return reachable_ips

# Exemplo de uso direto (quando executado como script principal)
if __name__ == "__main__":
    target_ip = input("Digite o endereço IP para escanear: ")
    
    # Verifica se o host está acessível antes de escanear
    if ping_host(target_ip):
        scan_results = scan_common_ports(target_ip)
        
        print("\nResultado do escaneamento:")
        for port, is_open in scan_results.items():
            status = "ABERTA" if is_open else "FECHADA"
            print(f"Porta {port}: {status}")
    else:
        print(f"O host {target_ip} não está acessível. Verifique a conexão e tente novamente.")
