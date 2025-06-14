
import os  
import random
from collections import Counter
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext

# Configuración del juego
elementos = {
    "Agua": 5,
    "Fuego": 4,
    "Tierra": 3,
    "Madera": 2,
    "Metal": 1
}
colores = ["Negro", "Rojo", "Verde", "Blanco", "Amarillo"]
baraja = [f"{elemento}-{color}" for elemento in elementos for color in colores]
jugadores = {}
sobrantes = []
registro_jugadores = []  # Lista para guardar el orden de los jugadores
turno_actual = 0

# Repartir cartas automáticamente al iniciar
def repartir_cartas():
    global jugadores, sobrantes
    random.shuffle(baraja)
    jugadores.clear()
    for i in range(1, len(registro_jugadores) + 1):  # Ajustar según cantidad de jugadores registrados
        jugadores[i] = baraja[(i - 1) * 5:i * 5]
    sobrantes[:] = baraja[len(registro_jugadores) * 5:len(registro_jugadores) * 5 + 5]

# Comando /start para iniciar el juego
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "¡Bienvenido al juego de cartas! Usa /unirme para registrarte y unirte al juego."
    )

# Comando /unirme para registrar jugadores
async def unirme(update: Update, context: CallbackContext) -> None:
    global registro_jugadores

    user_id = update.message.from_user.id
    username = update.message.from_user.username

    # Verificar si el jugador ya está registrado
    if user_id in [jugador["id"] for jugador in registro_jugadores]:
        await update.message.reply_text("¡Ya estás registrado!")
        return

    # Registrar al nuevo jugador
    registro_jugadores.append({"id": user_id, "username": username})
    await update.message.reply_text(
        f"🎉 {username} se ha unido al juego como Jugador {len(registro_jugadores)}."
    )

# Comando /empezar para repartir cartas e iniciar turnos
async def empezar(update: Update, context: CallbackContext) -> None:
    global turno_actual

    # Verificar que haya jugadores registrados
    if len(registro_jugadores) < 2:
        await update.message.reply_text("Necesitas al menos 2 jugadores para empezar el juego.")
        return

    # Repartir las cartas
    repartir_cartas()
    turno_actual = 0  # Comenzar desde el primer jugador en el registro

    # Notificar a los jugadores que el juego comienza
    mensaje = "El juego ha comenzado. Las cartas han sido repartidas.\n"
    mensaje += "Orden de los jugadores:\n"
    for i, jugador in enumerate(registro_jugadores, start=1):
        mensaje += f"Jugador {i}: @{jugador['username']}\n"
    await update.message.reply_text(mensaje)

    # Indicar de quién es el turno
    await notificar_turno(update, context)

# Notificar de quién es el turno actual
async def notificar_turno(update: Update, context: CallbackContext) -> None:
    global turno_actual

    jugador_actual = registro_jugadores[turno_actual]
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"🃏 Es el turno de @{jugador_actual['username']}."
    )

# Comando /entregar para mostrar opciones de entrega
async def mostrar_opciones(update: Update, context: CallbackContext) -> None:
    global turno_actual

    # Verificar si es el turno del jugador
    user_id = update.message.from_user.id
    jugador_actual = registro_jugadores[turno_actual]

    if user_id != jugador_actual["id"]:
        await update.message.reply_text("No es tu turno. Por favor, espera tu turno.")
        return

    # Crear botones interactivos para seleccionar una carta
    keyboard = [
        [InlineKeyboardButton(f"Carta {i}: {carta}", callback_data=str(i))]
        for i, carta in enumerate(jugadores[turno_actual + 1])
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Selecciona la carta que deseas entregar:", reply_markup=reply_markup)

# Callback para manejar el intercambio cuando el jugador selecciona una carta
async def intercambio(update: Update, context: CallbackContext) -> None:
    global turno_actual, jugadores, sobrantes

    query = update.callback_query
    await query.answer()  # Responder para evitar "cargando..."

    # Obtener el índice de la carta seleccionada
    indice = int(query.data)
    jugador_id = turno_actual + 1
    carta_entregada = jugadores[jugador_id].pop(indice)
    carta_nueva = random.choice(sobrantes)

    jugadores[jugador_id].append(carta_nueva)
    sobrantes.remove(carta_nueva)
    sobrantes.append(carta_entregada)

    # Mensaje grupal con los resultados
    mensaje = (
        f"🔄 @{registro_jugadores[turno_actual]['username']} ha entregado '{carta_entregada}' y recibido '{carta_nueva}'.\n"
        f"Cartas sobrantes ahora: {sobrantes}\n"
        f"Su nueva mano: {jugadores[jugador_id]}"
    )
    await context.bot.send_message(chat_id=query.message.chat_id, text=mensaje)

    # Pasar al siguiente turno
    turno_actual = (turno_actual + 1) % len(registro_jugadores)
    await notificar_turno(update, context)

# Configuración del bot
def main():
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Obtiene el token desde las variables de entorno
    application = Application.builder().token(TOKEN).build()

    # Manejadores de comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("unirme", unirme))
    application.add_handler(CommandHandler("empezar", empezar))
    application.add_handler(CommandHandler("entregar", mostrar_opciones))
    application.add_handler(CallbackQueryHandler(intercambio))  # Manejar botones interactivos

    # Ejecutar el bot
    application.run_polling()

if __name__ == "__main__":
    main()
