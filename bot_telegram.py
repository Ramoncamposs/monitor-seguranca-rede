import logging
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio
import sqlite3
import time

# --- Configurações do Bot ---
# SUBSTITUA ISSO pelo seu token real do bot
TELEGRAM_BOT_TOKEN = "7839856100:AAHD6POFWQJJz8jtwQabp5Pa2d4TCzaWu5g"

# --- Configuração do Banco de Dados para Usuários ---
DATABASE_NAME = 'bot_users.db'

def setup_user_database():
    """Cria a tabela para armazenar os IDs de chat dos usuários."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            chat_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            last_interaction TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_user_to_database(chat_id, first_name, username):
    """Adiciona um novo usuário ao banco de dados ou atualiza a interação."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute("INSERT INTO users (chat_id, first_name, username, last_interaction) VALUES (?, ?, ?, ?)",
                       (chat_id, first_name, username, timestamp))
        conn.commit()
        print(f"Novo usuário adicionado: {first_name} ({chat_id})")
    except sqlite3.IntegrityError:
        # Se o usuário já existe (chat_id é PRIMARY KEY), apenas atualiza a última interação
        cursor.execute("UPDATE users SET last_interaction = ? WHERE chat_id = ?",
                       (timestamp, chat_id))
        conn.commit()
        print(f"Usuário {first_name} ({chat_id}) já existe, interação atualizada.")
    finally:
        conn.close()

def get_all_user_chat_ids():
    """Retorna uma lista de todos os chat_ids registrados."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    chat_ids = [row[0] for row in cursor.fetchall()]
    conn.close()
    return chat_ids

# --- Configuração de Logging para o Bot (Opcional, mas útil para depuração) ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Funções de Handler para o Bot ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /start é emitido."""
    user = update.effective_user
    chat_id = user.id
    first_name = user.first_name
    username = user.username if user.username else "N/A" # Alguns usuários não têm username

    add_user_to_database(chat_id, first_name, username)

    await update.message.reply_html(
        f"Olá, {user.mention_html()}! Bem-vindo(a) ao Monitor de Segurança para Redes Domésticas.\n"
        "Seu ID de chat foi registrado. Você receberá alertas de segurança aqui.\n"
        "Para mais informações, contate o administrador."
    )
    logger.info(f"Comando /start recebido de {chat_id} ({first_name})")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia uma mensagem quando o comando /help é emitido."""
    await update.message.reply_text(
        "Eu sou o bot do Monitor de Segurança da Rede. Eu te enviarei alertas sobre portas abertas e vulnerabilidades.\n"
        "Por enquanto, apenas o administrador pode iniciar os escaneamentos."
    )
    logger.info(f"Comando /help recebido de {update.effective_user.id}")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ecoa a mensagem do usuário. Pode ser removido ou modificado."""
    await update.message.reply_text(f"Recebi sua mensagem: '{update.message.text}'.")
    logger.info(f"Mensagem de texto recebida de {update.effective_user.id}: {update.message.text}")

async def send_alert_to_all_users(message_text: str) -> None:
    """
    Função para ser chamada de fora (por exemplo, do seu network_scanner.py)
    para enviar um alerta a todos os usuários registrados.
    """
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    bot_instance = application.bot # Obtém a instância do bot para enviar mensagens

    chat_ids = get_all_user_chat_ids()
    if not chat_ids:
        logger.warning("Nenhum usuário registrado para enviar alertas.")
        return

    for chat_id in chat_ids:
        try:
            await bot_instance.send_message(chat_id=chat_id, text=message_text)
            logger.info(f"Alerta enviado para {chat_id}")
        except Exception as e:
            logger.error(f"Erro ao enviar alerta para {chat_id}: {e}")
            # Você pode adicionar lógica para remover chat_ids inválidos aqui

# --- Função Principal para Rodar o Bot ---
def main_bot_listener():
    """Inicia o bot e o polling."""
    setup_user_database() # Garante que o DB de usuários esteja pronto

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Adiciona handlers para comandos e mensagens
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot iniciado. Começando polling...")
    # Roda o bot até que o usuário pressione Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main_bot_listener()