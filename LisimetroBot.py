import telebot
from telebot import types
import pyowm
from osgeo import ogr, gdal
import struct
import MySQLdb
import re
import subprocess
import time


########### Functions

def extract_point_from_raster(point, data_source, band_number=1):
    """Return floating-point value that corresponds to given point."""
  
    source = osr.SpatialReference()
    source.ImportFromEPSG(4326)
    target = osr.SpatialReference()
    target.ImportFromEPSG(32719)
   
    transform = osr.CoordinateTransformation(source, target)
    point.Transform(transform)

    gt=data_source.GetGeoTransform()
    rb=data_source.GetRasterBand(1)
    geom = point.GetGeometryRef()
    mx,my=geom.GetX(), geom.GetY()
    px = int((mx - gt[0]) / gt[1]) #x pixel
    py = int((my - gt[3]) / gt[5]) #y pixel

    structval=rb.ReadRaster(px,py,1,1,buf_type=gdal.GDT_UInt16) #Assumes 16 bit int aka 'short'
    intval = struct.unpack('h' , structval) #use the 'short' format code (2 bytes) not int (4 bytes)

    return intval[0] 

def getEmoji(weatherID):
    if weatherID:
        if str(weatherID)[0] == '2' or weatherID == 900 or weatherID==901 or weatherID==902 or weatherID==905:
            return thunderstorm
        elif str(weatherID)[0] == '3':
            return drizzle
        elif str(weatherID)[0] == '5':
            return rain
        elif str(weatherID)[0] == '6' or weatherID==903 or weatherID== 906:
            return snowflake + ' ' + snowman
        elif str(weatherID)[0] == '7':
            return atmosphere
        elif weatherID == 800:
            return clearSky
        elif weatherID == 801:
            return fewClouds
        elif weatherID==802 or weatherID==803 or weatherID==803:
            return clouds
        elif weatherID == 904:
            return hot
        else:
            return defaultEmoji    # Default emoji
    else:
        return defaultEmoji # Default emoji



######### Emojis (from Weather Bot)

thunderstorm = u'\U0001F4A8'    # Code: 200's, 900, 901, 902, 905
drizzle = u'\U0001F4A7'         # Code: 300's
rain = u'\U00002614'            # Code: 500's
snowflake = u'\U00002744'       # Code: 600's snowflake
snowman = u'\U000026C4'         # Code: 600's snowman, 903, 906
atmosphere = u'\U0001F301'      # Code: 700's foogy
clearSky = u'\U00002600'        # Code: 800 clear sky
fewClouds = u'\U000026C5'       # Code: 801 sun behind clouds
clouds = u'\U00002601'          # Code: 802-803-804 clouds general
hot = u'\U0001F525'             # Code: 904
defaultEmoji = u'\U0001F300' # default emojis

####### BOT

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/TOKEN.txt')
TOKEN = f.read().strip('\n')
f.close

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/OWM.key')
OWM = f.read().strip('\n')
f.close

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/clavebot')
clavebot = f.read().strip('\n')
f.close


owm = pyowm.OWM(OWM, language='es')

bot = telebot.TeleBot(TOKEN)

########## COMMANDS

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Estacion Lisimetrica\nINTA EEA Mendoza")

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Este bot es experimental, por ahora solo interpreta palabras como tiempo, temperatura, lluvia.\nResponde comandos como /start, /help y /status")

@bot.message_handler(commands=['status'])
def send_status(message):
    f = open('/home/guillermo/Lisimetro-INTA-Mendoza/current/status')
    status = f.readline().split(',')
    f.close
    try:
      db_status = 'ONLINE'
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
      cursor = db.cursor()        
      cursor.execute("SELECT VERSION()")
      results = cursor.fetchone()
      # Check if anything at all is returned
    except MySQLdb.Error:
      db_status = 'OFFLINE'
    cursor.close()
    db.close()
    output = subprocess.check_output(['systemctl', 'status'])
    output = str(output)
    comm_status = "ONLINE"
    test_comm = re.search('LisimetroCaptura', output)
    if test_comm == None:
       comm_status = "OFFLINE"
    bot.reply_to(message, "Batería: " + str(status[1]) + "V"
    + "\nÚltimo dato recibido: " + str(status[0])
    + "\nBase de datos: " + str(db_status)
    + "\nComunicaciones: " + str(comm_status) )

@bot.message_handler(commands=['about'])
def send_about(message):
    bot.reply_to(message, "Estacion Lisimétrica")

@bot.message_handler(commands=['last'])
def send_last(message):
    output = subprocess.check_output(['systemctl', 'status', 'LisimetroCaptura'])
    bot.reply_to(message, output)



########## TEXT MESSAGES HANDLERS

@bot.message_handler(regexp="tiempo")
def handle_message(message):
    observation = owm.weather_at_place('Vistalba,AR')
    # TODO: Don't ask for a new observation if this one is from the last 10 minutes
    w = observation.get_weather()
    # Weather details
    w_status = w.get_detailed_status()
    wind = w.get_wind()
    hum = w.get_humidity()
    pres = w.get_pressure()
    temp = w.get_temperature('celsius')
    weatherID = w.get_weather_code()   
    emoji = getEmoji(weatherID)
    bot.reply_to(message, str(w_status) + " " + emoji + emoji
    + "\nHacen " +  str(temp['temp']) 
    + " grados \nEl viento es de " + str(wind['speed']) 
    + " km/h \nLa humedad relativa es de " + str(hum) 
    + "%.\nLa presión es de " + str(pres['press']) + " mb.")

@bot.message_handler(regexp="clima")
def send_welcome(message):
    bot.reply_to(message, "Mendoza tiene un clima arido y continental, las temperaturas presentan una importante oscilacion anual y las precipitaciones son escasas.\nEl verano es calido y humedo, es la epoca más lluviosa y las temperaturas medias estan por encima de los 25 C.\nEl invierno es frio y seco, con temperaturas medias por debajo de los 8 C, heladas nocturnas ocasionales y escasas precipitaciones. La caida de nieve y aguanieve son poco comunes, suelen tirdarse una vez por año, aunque con poca intensidad en las zonas más altas de la ciudad.\nQuizas quieras informacion sobre el estado del tiempo?")


@bot.message_handler(regexp="pronostico")
def handle_message(message):
    fc = owm.daily_forecast('Vistalba,AR', limit=6)
    fore = fc.get_forecast()
    lst = fore.get_weathers()
    bot.reply_to(message, str(lst))


@bot.message_handler(regexp="lloviendo|llueve")
def handle_message(message):
    bot.reply_to(message, "No, hoy es un dia Peronista!")


@bot.message_handler(regexp="calor")
def handle_message(message):
    bot.reply_to(message, "Esta para una birra")


@bot.message_handler(regexp="padre|creador|autor")
def handle_message(message):
    bot.reply_to(message, "Luke, I am your father")


########################## ET


@bot.message_handler(regexp="ET|evapotranspiracion|evapo|ETr|ETa")
def handle_message(message):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    start = time.strftime("%Y-%m-%d")
    db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
    cursor = db.cursor()
    query = ("SELECT Peso_diff FROM Ciclo20162017 WHERE Fecha BETWEEN %s AND %s")
    cursor.execute(query, (start, now))
    results = cursor.fetchall()
    bot.reply_to(message, str(results))
    cursor.close()
    db.close()


##############################################  LOCATION

@bot.message_handler(content_types=['location'])
def handle_location(message):
    if abs(message.location.latitude - -33) > 0.5 or \
    abs(message.location.longitude - -68.8) > 0.5:
       observation = owm.weather_at_coords(message.location.latitude, message.location.longitude)  
       w = observation.get_weather()
       # Weather details
       w_status = w.get_detailed_status()
       wind = w.get_wind()
       hum = w.get_humidity()
       pres = w.get_pressure()
       temp = w.get_temperature('celsius')
       weatherID = w.get_weather_code() 
       emoji = getEmoji(weatherID)
       bot.reply_to(message, "Solo puedo dar datos de evapotranspiracion cerca de la estación, "
       + "pero puedo buscar el estado del tiempo en [owm](http://openweathermap.org/) para esa localización: "
       + "\n" + str(w_status) + " "  + emoji + emoji
       + "\nHacen " +  str(temp['temp']) + " grados \nEl viento es de " + str(wind['speed'])
       + " km/h \nLa humedad relativa es de " + str(hum) + "%.\nLa presión es de " + str(pres['press']) + " mb.",
       parse_mode = "Markdown")
    if abs(message.location.latitude - -33) <= 0.5 and \
    abs(message.location.longitude - -68.8) <= 0.5:
       markup = types.ReplyKeyboardMarkup(row_width=1)
       itembtn1 = types.KeyboardButton('Evapotranspiración Potencial')
       itembtn2 = types.KeyboardButton('Evapotranspiración Real')
       itembtn3 = types.KeyboardButton('Coeficiente de Cultivo')
       markup.add(itembtn1, itembtn2, itembtn3)
       bot.send_message(message.chat.id, "Que información quieres para esa localización?:", reply_markup=markup)
       point = ogr.Geometry(ogr.wkbPoint)
       point.AddPoint(message.location.latitude, message.location.longitude)
       #imagen = gdal.Open('/home/guillermo/test.tif')
       #resultado = extract_point_from_raster(point, imagen)
       bot.reply_to(message, "Lat: " + str(message.location.latitude) + 
       "\nLongitude: " + str(message.location.longitude)) 
       #"\nraster value:" +str(resultado))
       

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    if message.chat.type == "private":
       bot.reply_to(message, "Lo siento, no se como interpretar esto. Prueba con /help")

bot.polling()
