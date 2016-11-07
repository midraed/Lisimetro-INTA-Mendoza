import telebot
from telebot import types
import pyowm
from osgeo import ogr, gdal
import struct
import MySQLdb
import re
import subprocess

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

####### BOT

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/TOKEN.txt')
TOKEN = f.read().strip('\n')
f.close

f = open('/home/guillermo/Lisimetro-INTA-Mendoza/OWM.key')
OWM = f.read().strip('\n')
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
      f = open('/home/guillermo/Lisimetro-INTA-Mendoza/clave')
      clave = f.read().strip('\n')
      f.close
      db_status = 'ONLINE'
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='guillermo', passwd=clave )
      cursor = db.cursor()        
      cursor.execute("SELECT VERSION()")
      results = cursor.fetchone()
      # Check if anything at all is returned
    except MySQLdb.Error:
      db_status = 'OFFLINE'
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
def send_last(message):
    bot.reply_to(message, "Estacion Lisimétrica")


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
    bot.reply_to(message, str(w_status)
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
       bot.reply_to(message, "Solo puedo dar datos de evapotranspiracion cerca de la estación, "
       + "pero puedo buscar el estado del tiempo en [owm](http://openweathermap.org/) para esa localización: "
       + "\n" + str(w_status)
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
