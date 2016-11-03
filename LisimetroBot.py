import telebot

f = open('TOKEN.txt')
TOKEN = f.read().strip('\n')
f.close

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "LISIMETRO EEA MENDOZA")

@bot.message_handler(regexp="tiempo")
def handle_message(message):
    bot.reply_to(message, "Hacen 23 grados")


@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, message.text)

bot.polling()
