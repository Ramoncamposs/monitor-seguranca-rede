from flask import Flask, render_template, request, jsonify
import sqlite3
import threading
import asyncio
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from bot_telegram import send_alert_to_all_users, setup_user_database
from network_scanner import scan_port, scan_common_ports, ping_host, discover_network_ips

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=4)

# Configurações
DATABASE = 'security_alerts.db'

def init_db():
    """Inicializa os bancos de dados"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alert_type TEXT,
            ip_address TEXT,
            port INTEGER,
            service_info TEXT,
            message TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    setup_user_database()

def run_async(coro):
    """Executa uma corotina em uma thread separada"""
    def wrapper():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(coro)
        except Exception as e:
            logger.error(f"Erro na execução assíncrona: {e}")
        finally:
            loop.close()
    threading.Thread(target=wrapper, daemon=True).start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/alerts')
def get_alerts():
    """Retorna todos os alertas do banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT timestamp, alert_type, ip_address, port, service_info, message 
            FROM alerts 
            ORDER BY timestamp DESC
            LIMIT 50
        """)
        alerts = cursor.fetchall()
        conn.close()
        
        alerts_list = [{
            'timestamp': alert[0],
            'type': alert[1],
            'ip': alert[2],
            'port': alert[3] if alert[3] else 'N/A',
            'service': alert[4] if alert[4] else 'N/A',
            'message': alert[5]
        } for alert in alerts]
        
        return jsonify({'alerts': alerts_list})
    except Exception as e:
        logger.error(f"Erro ao buscar alertas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def get_stats():
    """Retorna estatísticas dos alertas"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM alerts")
        total_alerts = cursor.fetchone()[0]
        
        cursor.execute("SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type")
        alerts_by_type = dict(cursor.fetchall())
        
        cursor.execute("""
            SELECT ip_address, COUNT(*) 
            FROM alerts 
            GROUP BY ip_address 
            ORDER BY COUNT(*) DESC 
            LIMIT 5
        """)
        problematic_ips = cursor.fetchall()
        
        cursor.execute("""
            SELECT strftime('%Y-%m-%d', timestamp) as day, COUNT(*) 
            FROM alerts 
            GROUP BY day 
            ORDER BY day DESC 
            LIMIT 7
        """)
        alerts_by_day = dict(cursor.fetchall())
        
        conn.close()
        
        return jsonify({
            'total_alerts': total_alerts,
            'alerts_by_type': alerts_by_type,
            'problematic_ips': problematic_ips,
            'alerts_by_day': alerts_by_day
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/discover')
def discover():
    """Descobre dispositivos na rede"""
    try:
        devices = discover_network_ips()
        return jsonify({'devices': devices})
    except Exception as e:
        logger.error(f"Erro na descoberta de dispositivos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scan_common_ports', methods=['POST'])
def scan_common():
    """Escaneia portas comuns em um IP"""
    try:
        ip = request.form.get('ip')
        if not ip:
            return jsonify({'error': 'IP não fornecido'}), 400
        
        results = scan_common_ports(ip)
        
        # Processa resultados e envia alertas
        for port, is_open in results.items():
            if is_open:
                service_info = {
                    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                    53: "DNS", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 3389: "RDP"
                }.get(port, "Desconhecido")
                
                message = f"Porta {port} ({service_info}) aberta em {ip}"
                save_alert("Porta Aberta", ip, port, service_info, message)
                
                if port in [23, 3389]:  # Portas críticas
                    warning = f"ALERTA: Porta {port} ({service_info}) aberta em {ip}"
                    if port == 23:
                        warning += " - Telnet é inseguro! Recomenda-se desativar."
                    elif port == 3389:
                        warning += " - RDP pode ser vulnerável. Proteja com senha forte."
                    
                    run_async(send_alert_to_all_users(warning))
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Erro no escaneamento de portas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/scan_port', methods=['POST'])
def scan_single_port():
    """Verifica uma porta específica"""
    try:
        ip = request.form.get('ip')
        port = request.form.get('port')
        
        if not ip or not port:
            return jsonify({'error': 'IP ou porta não fornecidos'}), 400
        
        try:
            port = int(port)
            if not (1 <= port <= 65535):
                return jsonify({'error': 'Porta deve estar entre 1 e 65535'}), 400
        except ValueError:
            return jsonify({'error': 'Porta deve ser um número'}), 400
        
        is_open = scan_port(ip, port)
        
        if is_open:
            service_info = {
                21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
                53: "DNS", 80: "HTTP", 443: "HTTPS", 3306: "MySQL", 3389: "RDP"
            }.get(port, "Desconhecido")
            
            message = f"Porta {port} ({service_info}) aberta em {ip}"
            save_alert("Porta Aberta", ip, port, service_info, message)
            run_async(send_alert_to_all_users(message))
        
        return jsonify({'port': port, 'is_open': is_open})
    except Exception as e:
        logger.error(f"Erro na verificação de porta: {e}")
        return jsonify({'error': str(e)}), 500

def save_alert(alert_type, ip, port, service_info, message):
    """Salva alerta no banco de dados"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO alerts 
            (timestamp, alert_type, ip_address, port, service_info, message) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (timestamp, alert_type, ip, port, service_info, message))
        conn.commit()
        conn.close()
        logger.info(f"Alerta salvo: {message}")
    except Exception as e:
        logger.error(f"Erro ao salvar alerta: {e}")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)