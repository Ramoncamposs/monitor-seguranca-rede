"""
Monitor de Segurança para Redes Domésticas - Versão Simplificada
Este programa escaneia portas em um endereço IP e mostra quais estão abertas.
"""
import socket
import time
import asyncio # Necessário para chamar funções async do bot
import sqlite3 # Para o banco de dados de alertas

# Importa as funções de escaneamento do network_scanner.py
from network_scanner import scan_port, scan_common_ports, ping_host, discover_network_ips

# Importa a função de envio de alertas para o Telegram do bot_telegram.py
# e a função de setup do banco de dados de usuários do bot.
# É CRÍTICO que 'bot_telegram.py' esteja no MESMO DIRETÓRIO que 'main.py'.
try:
    # CORREÇÃO AQUI: Mudado 'send_alert_to_all_registered_users' para 'send_alert_to_all_users'
    from bot_telegram import send_alert_to_all_users, setup_user_database
except ImportError as e:
    # A mensagem de erro também foi ajustada para refletir o nome do arquivo 'bot_telegram.py'
    print(f"ERRO: Não foi possível importar o 'bot_telegram.py'. Detalhes: {e}")
    print("Certifique-se de que o arquivo 'bot_telegram.py' está no mesmo diretório de 'main.py'.")
    print("Verifique também se todas as dependências (como 'python-telegram-bot') estão instaladas.")
    print("Os alertas do Telegram não serão enviados e os usuários do bot não serão gerenciados.")
    send_alert_to_all_users = None # Define como None para evitar erros se a importação falhar
    setup_user_database = lambda: None # Define uma função vazia para evitar erro de chamada

# --- Configuração do Banco de Dados para Alertas de Segurança ---
ALERT_DATABASE_NAME = 'security_alerts.db'

def setup_alert_database():
    """Cria a tabela para armazenar os alertas de segurança."""
    conn = sqlite3.connect(ALERT_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT, -- Ex: 'Porta Aberta', 'Host Inacessível', 'Vulnerabilidade'
            ip_address TEXT,
            port INTEGER,
            service_info TEXT,
            message TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Banco de dados de alertas ({ALERT_DATABASE_NAME}) configurado.")

def save_security_alert(alert_type, ip_address, port, service_info, message):
    """Salva um alerta de segurança no banco de dados."""
    conn = sqlite3.connect(ALERT_DATABASE_NAME)
    cursor = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO alerts (timestamp, alert_type, ip_address, port, service_info, message) VALUES (?, ?, ?, ?, ?, ?)",
        (timestamp, alert_type, ip_address, port, service_info, message) # CORREÇÃO AQUI: Adicionado 'alert_type'
    )
    conn.commit()
    conn.close()
    print(f"Alerta salvo no histórico: {message}")

def get_alert_history():
    """Retorna o histórico de alertas do banco de dados."""
    conn = sqlite3.connect(ALERT_DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, alert_type, ip_address, port, service_info, message FROM alerts ORDER BY timestamp DESC")
    alerts = cursor.fetchall()
    conn.close()
    return alerts

def mostrar_menu():
    """Exibe o menu principal do programa."""
    print("\n" + "="*50)
    print("MONITOR DE SEGURANÇA PARA REDES DOMÉSTICAS")
    print("="*50)
    print("1. Descobrir dispositivos na rede")
    print("2. Escanear portas comuns em um dispositivo")
    print("3. Verificar uma porta específica")
    print("4. Ver histórico de alertas")
    print("5. Sobre o programa")
    print("6. Sair")
    print("="*50)

def descobrir_dispositivos():
    """Descobre dispositivos acessíveis na rede local."""
    print("\nIniciando descoberta de dispositivos na rede local...")
    
    ips_alcancaveis = discover_network_ips()
    
    if not ips_alcancaveis:
        print("Nenhum dispositivo foi encontrado na rede local.")
        return []
    
    print("\n" + "="*50)
    print("DISPOSITIVOS ENCONTRADOS NA REDE")
    print("="*50)
    
    for i, ip in enumerate(ips_alcancaveis, 1):
        nome = "Este computador (localhost)" if ip == "127.0.0.1" else f"Dispositivo {i}"
        print(f"{i}. {ip} - {nome}")
    
    print("="*50)
    return ips_alcancaveis

def selecionar_dispositivo(ips_disponiveis):
    """Permite ao usuário selecionar um dispositivo da lista por número."""
    if not ips_disponiveis:
        print("Não há dispositivos disponíveis. Execute a opção 1 primeiro.")
        return None
    
    print("\nDispositivos disponíveis:")
    for i, ip in enumerate(ips_disponiveis, 1):
        nome = "Este computador (localhost)" if ip == "127.0.0.1" else f"Dispositivo {i}"
        print(f"{i}. {ip} - {nome}")
    
    try:
        escolha = int(input("\nEscolha um dispositivo pelo número (ou 0 para cancelar): "))
        if escolha == 0:
            return None
        if 1 <= escolha <= len(ips_disponiveis):
            return ips_disponiveis[escolha-1]
        else:
            print("Número inválido!")
            return None
    except ValueError:
        print("Por favor, digite um número válido.")
        return None

def verificar_porta_especifica(ips_disponiveis):
    """Permite ao usuário verificar uma porta específica em um IP."""
    if not ips_disponiveis:
        print("Não há dispositivos disponíveis. Execute a opção 1 primeiro.")
        return
    
    ip = selecionar_dispositivo(ips_disponiveis)
    if not ip:
        return
    
    try:
        porta = int(input("Digite o número da porta para verificar: "))
        if porta < 1 or porta > 65535:
            print("Número de porta inválido! Deve estar entre 1 e 65535.")
            return
    except ValueError:
        print("Por favor, digite um número válido para a porta.")
        return
    
    print(f"\nVerificando se o dispositivo {ip} está acessível...")
    if not ping_host(ip):
        print(f"O dispositivo {ip} não está respondendo. Verifique a conexão e tente novamente.")
        alert_msg = f"ALERTA: O dispositivo {ip} não está acessível para verificação da porta {porta}."
        save_security_alert("Host Inacessível", ip, porta, "N/A", alert_msg)
        if send_alert_to_all_users: # Usando o nome da função corrigido
            asyncio.run(send_alert_to_all_users(alert_msg))
        return
    
    print(f"Verificando porta {porta} em {ip}...")
    resultado = scan_port(ip, porta)
    
    if resultado:
        print(f"A porta {porta} está ABERTA em {ip}")
        alert_message = f"ALERTA DE SEGURANÇA: A porta {porta} está ABERTA no dispositivo {ip}."
        save_security_alert("Porta Aberta", ip, porta, "Desconhecido", alert_message)
        if send_alert_to_all_users: # Usando o nome da função corrigido
            asyncio.run(send_alert_to_all_users(alert_message))
    else:
        print(f"A porta {porta} está FECHADA em {ip}")

def escanear_portas_comuns(ips_disponiveis):
    """Escaneia as portas mais comuns em um endereço IP."""
    if not ips_disponiveis:
        print("Não há dispositivos disponíveis. Execute a opção 1 primeiro.")
        return
    
    ip = selecionar_dispositivo(ips_disponiveis)
    if not ip:
        return
    
    print(f"\nVerificando se o dispositivo {ip} está acessível...")
    if not ping_host(ip):
        print(f"O dispositivo {ip} não está respondendo. Verifique a conexão e tente novamente.")
        alert_msg = f"ALERTA: O dispositivo {ip} não está acessível para escaneamento de portas comuns."
        save_security_alert("Host Inacessível", ip, None, "N/A", alert_msg)
        if send_alert_to_all_users: # Usando o nome da função corrigido
            asyncio.run(send_alert_to_all_users(alert_msg))
        return
    
    resultados = scan_common_ports(ip)
    
    # Contagem de portas abertas
    portas_abertas = sum(1 for porta, aberta in resultados.items() if aberta)
    
    print("\n" + "="*50)
    print(f"RESULTADO DO ESCANEAMENTO PARA {ip}")
    print("="*50)
    print(f"Total de portas verificadas: {len(resultados)}")
    print(f"Portas abertas encontradas: {portas_abertas}")
    
    if portas_abertas > 0:
        alert_summary = f"ALERTA DE SEGURANÇA: Portas abertas encontradas no dispositivo {ip}!"
        print("\nPORTAS ABERTAS ENCONTRADAS:")
        telegram_alert_details = []
        telegram_alert_details.append(alert_summary) # Adiciona o resumo ao alerta do Telegram
        
        for porta, aberta in resultados.items():
            if aberta:
                servicos = {
                    21: "FTP (Transferência de arquivos)",
                    22: "SSH (Acesso remoto seguro)",
                    23: "Telnet (Acesso remoto NÃO seguro)",
                    25: "SMTP (Envio de e-mails)",
                    53: "DNS (Resolução de nomes)",
                    80: "HTTP (Servidor web)",
                    443: "HTTPS (Servidor web seguro)",
                    3306: "MySQL (Banco de dados)",
                    3389: "RDP (Área de trabalho remota)"
                }
                service_info = servicos.get(porta, 'Serviço desconhecido')
                port_message = f"Porta {porta}: {service_info}"
                print(port_message)
                telegram_alert_details.append(port_message)
                
                # Salva o alerta da porta aberta
                save_security_alert("Porta Aberta", ip, porta, service_info, port_message)
                
                # Alertas simples para portas específicas
                if porta == 23:
                    warning_msg = "   ⚠️ ALERTA DE SEGURANÇA: Telnet não é seguro! Recomenda-se usar SSH."
                    print(warning_msg)
                    telegram_alert_details.append(warning_msg)
                    save_security_alert("Vulnerabilidade - Telnet", ip, porta, service_info, warning_msg)
                elif porta == 3389:
                    warning_msg = "   ⚠️ ALERTA DE SEGURANÇA: RDP pode ser alvo de ataques. Proteja com senha forte."
                    print(warning_msg)
                    telegram_alert_details.append(warning_msg)
                    save_security_alert("Vulnerabilidade - RDP", ip, porta, service_info, warning_msg)
        
        full_telegram_message = "\n".join(telegram_alert_details)
        if send_alert_to_all_users: # Usando o nome da função corrigido
            asyncio.run(send_alert_to_all_users(full_telegram_message))
    else:
        print("Nenhuma porta comum aberta encontrada.")
        alert_msg = f"Nenhuma porta comum aberta encontrada no dispositivo {ip}."
        save_security_alert("Nenhuma Porta Aberta", ip, None, "N/A", alert_msg)
        if send_alert_to_all_users: # Usando o nome da função corrigido
            asyncio.run(send_alert_to_all_users(alert_msg))

def ver_historico_alertas():
    """Exibe o histórico de alertas do banco de dados."""
    print("\n" + "="*50)
    print("HISTÓRICO DE ALERTAS DE SEGURANÇA")
    print("="*50)
    alerts = get_alert_history()
    if not alerts:
        print("Nenhum alerta registrado ainda.")
        print("="*50)
        return
    
    # Imprime os cabeçalhos da tabela
    print(f"{'Data/Hora':<20} | {'Tipo':<25} | {'IP':<15} | {'Porta':<8} | {'Serviço':<15} | {'Mensagem'}")
    print("-" * 100) # Linha separadora
    
    for alert in alerts:
        timestamp, alert_type, ip_address, port, service_info, message = alert
        # Formata a saída para alinhamento (opcional, para melhor leitura)
        port_display = str(port) if port else "N/A"
        print(f"{timestamp:<20} | {alert_type:<25} | {ip_address:<15} | {port_display:<8} | {service_info:<15} | {message}")
    print("="*100) # Linha final

def sobre_programa():
    """Exibe informações sobre o programa."""
    print("\n" + "="*50)
    print("SOBRE O MONITOR DE SEGURANÇA")
    print("="*50)
    print("Este é um programa simples para monitorar a segurança de redes domésticas.")
    print("Ele verifica quais portas estão abertas em dispositivos da rede.")
    print("\nPorque isso é importante?")
    print("- Portas abertas são como 'portas' e 'janelas' na sua rede")
    print("- Cada porta aberta pode ser uma entrada para invasores")
    print("- Conhecer as portas abertas ajuda a melhorar a segurança")
    print("\nFuncionalidades:")
    print("1. Descoberta de dispositivos na rede local")
    print("2. Verificação de portas comuns")
    print("3. Teste de portas específicas")
    print("4. Histórico de alertas")
    print("\nDesenvolvido para o trabalho de Aplicações em Rede")
    print("="*50)

def main():
    """Função principal que executa o programa."""
    # Garante que os bancos de dados estejam configurados
    # setup_user_database() vem do bot_telegram.py e cria 'bot_users.db'
    setup_user_database()
    # setup_alert_database() é local ao main.py e cria 'security_alerts.db'
    setup_alert_database()
    
    # Lista para armazenar IPs descobertos
    ips_disponiveis = []
    
    while True:
        mostrar_menu()
        
        try:
            opcao = int(input("\nEscolha uma opção (1-6): "))
        except ValueError:
            print("Por favor, digite um número válido.")
            continue
        
        if opcao == 1:
            ips_disponiveis = descobrir_dispositivos()
        elif opcao == 2:
            escanear_portas_comuns(ips_disponiveis)
        elif opcao == 3:
            verificar_porta_especifica(ips_disponiveis)
        elif opcao == 4:
            ver_historico_alertas()
        elif opcao == 5:
            sobre_programa()
        elif opcao == 6:
            print("\nObrigado por usar o Monitor de Segurança para Redes Domésticas!")
            break
        else:
            print("Opção inválida. Por favor, escolha uma opção entre 1 e 6.")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()