import telebot
import pyowm

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/TOKEN.txt')
TOKEN = f.read().strip('\n')
f.close

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/OWM.key')
OWM = f.read().strip('\n')
f.close

owm = pyowm.OWM(OWM, language='es') 

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Estacion Lisimetrica\nINTA EEA Mendoza")

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Este bot es experimental, por ahora solo interpreta palabras como tiempo, temperatura, lluvia.\nResponde comandos como /start, /help y /status")

@bot.message_handler(commands=['status'])
def send_welcome(message):
    bot.reply_to(message, "Up and running!")

@bot.message_handler(regexp="tiempo")
def handle_message(message):
    observation = owm.weather_at_place('Vistalba,AR')
    # TODO: Don't ask for a new observation if this one is from the last 10 minutes
    w = observation.get_weather()
    # Weather details
    wind = w.get_wind()                  # {'speed': 4.6, 'deg': 330}
    hum = w.get_humidity()              # 87
    pres = w.get_pressure() 
    temp = w.get_temperature('celsius')
    bot.reply_to(message, "Hacen " +  str(temp['temp']) + " grados \nEl viento es de " + str(wind['speed']) + " km/h \nLa humedad relativa es de " + str(hum) + " %.\nLa presión es de" + str(pres['press']) + " mb.")


@bot.message_handler(regexp="pronostico")
def handle_message(message):
    fc = owm.daily_forecast('Vistalba,AR', limit=6)
    fore = fc.get_forecast()
    lst = fore.get_weathers()
    bot.reply_to(message, str(lst))



@bot.message_handler(regexp="lloviendo")
def handle_message(message):
    bot.reply_to(message, "No, hoy es un dia Peronista!")

@bot.message_handler(regexp="temperatura")
def handle_message(message):
    bot.reply_to(message, "Esta para una birra")

@bot.message_handler(regexp="padre")
def handle_message(message):
    bot.reply_to(message, "Luke, I am your father")



@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Lo siento, no se como interpretar esto. Prueba con /help")

bot.polling()
