import telebot
from telebot import types
import pyowm
from osgeo import ogr, gdal
import struct
import MySQLdb
import re
import subprocess
import time
import datetime
import os
import numpy as np
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt


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

#### Potencial suelo

@bot.message_handler(regexp="potencial|humedad|suelo")
def handle_message(message):
    if("grafico" in message.text):
      now = time.strftime("%Y-%m-%d %H:%M:%S")
      start = time.strftime("%Y-%m-%d")
      if("desde" in message.text):
          if("ayer" in message.text):
              start = datetime.date.today() - datetime.timedelta(days=1)
              start = start.strftime("%Y-%m-%d")
          if("hace" in message.text):
              ndias = int(re.findall('\d', message.text)[0])
              start = datetime.date.today() - datetime.timedelta(days=ndias)
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
      cursor = db.cursor()
      query = ("SELECT Fecha, E1_Tens_50 FROM Ciclo20162017 WHERE (Fecha BETWEEN %s AND %s)"
               + " AND (E1_Tens_50 BETWEEN 0 and 200)")
      cursor.execute(query, (start, now))
      results = list(cursor.fetchall())
      dates = []
      temps = []
      dates[:] = (value[0] for value in results)
      temps[:] = (value[1] for value in results)
      plt.rcParams['axes.color_cycle']='brown'
      plt.rcParams['lines.linewidth'] = 1.5
      fig = plt.figure()
      ax = fig.add_subplot(111)
      ax.set_ylim(-5,205)
      plt.plot(dates, temps)
      ax.set_ylabel('Potencial suelo a 50 cm (bares)')
      ax.set_title('Evolución de la humedad del suelo')
      os.remove("/home/guillermo/potencialsue.png")
      fig.savefig('/home/guillermo/potencialsue.png')
      photo = open('/home/guillermo/potencialsue.png', 'rb')
      bot.send_photo(message.chat.id, photo)
      cursor.close()
      db.close()
    else:
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
      cursor = db.cursor()
      query = ("SELECT E1_Tens_50 FROM Ciclo20162017 ORDER BY Fecha DESC LIMIT 1;")
      cursor.execute(query)
      results = cursor.fetchall()[0][0]
      bot.reply_to(message, "Potencial suelo a 50cm: " + str(results) + "bares ")
      cursor.close()



######################### Temperatura

@bot.message_handler(regexp="temperatura")
def handle_message(message):
    if("grafico" in message.text):
      now = time.strftime("%Y-%m-%d %H:%M:%S")
      start = time.strftime("%Y-%m-%d")
      if("desde" in message.text):
          if("ayer" in message.text):
              start = datetime.date.today() - datetime.timedelta(days=1)
              start = start.strftime("%Y-%m-%d")
          if("hace" in message.text):
              ndias = int(re.findall('\d', message.text)[0])
              start = datetime.date.today() - datetime.timedelta(days=ndias)
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
      cursor = db.cursor()
      query = ("SELECT Fecha, E1_Temp_50 FROM Ciclo20162017 WHERE (Fecha BETWEEN %s AND %s)"
               +  " AND (E1_Temp_50 BETWEEN -30 AND 50)")
      cursor.execute(query, (start, now))
      results = list(cursor.fetchall())
      dates = []
      temps = []
      dates[:] = (value[0] for value in results)
      temps[:] = (value[1] for value in results)
      plt.rcParams['axes.color_cycle']='brown'
      plt.rcParams['lines.linewidth'] = 1.5
      fig = plt.figure()
      ax = fig.add_subplot(111)
      plt.plot(dates, temps)
      ax.set_ylabel('Temperatura (°C)')
      ax.set_title('Evolución de la Temperatura')
      os.remove("/home/guillermo/temp84.png")
      fig.savefig('/home/guillermo/temp84.png')
      photo = open('/home/guillermo/temp84.png', 'rb')
      bot.send_photo(message.chat.id, photo)
      cursor.close()
      db.close()
    else:
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
      cursor = db.cursor()
      query = ("SELECT E1_Temp_50 FROM Ciclo20162017 ORDER BY Fecha DESC LIMIT 1;")
      cursor.execute(query)
      results = cursor.fetchall()[0][0]
      bot.reply_to(message, "Temperatura: " + str(results) + "C ")
      cursor.close()
      db.close()


########################## ET

@bot.message_handler(regexp="grafico")
def handle_message(message):
    if("evapo" in message.text):
      ndias = 1
      if("desde" in message.text):
        if("ayer" in message.text):
           ndias = 2
        if("hace" in message.text):
            ndias = int(re.findall('\d+', message.text)[0])
      db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot)
      cursor = db.cursor()
      query = ("SELECT Peso_diff FROM Ciclo20162017 WHERE Fecha BETWEEN %s AND %s")
      datos = []
      for i in range(0,ndias):
        start = datetime.date.today() - datetime.timedelta(days=i)
        stop = datetime.date.today() - datetime.timedelta(days=i)
        stop = stop.strftime("%Y-%m-%d") + " 23:59"
        cursor.execute(query, (start, stop))
        results = list(cursor.fetchall())
        results[:] = (value[0] for value in results)
        results[:] = (value for value in results if value > -30)
        datos.append(round(abs(sum(results) / 6.25),2))
      ind = np.arange(ndias-1,-1,-1)
      datos = tuple(datos)
      fig = plt.figure()
      ax = fig.add_subplot(111)
      ax.bar(ind,datos, 0.35)
      ax.set_ylim(0,max(datos)*1.1)
      ax.set_ylabel('ETr acumulada (mm)')
      ax.set_title('Evolución de la ETr')
      xTickMarks = [datetime.date.today() - datetime.timedelta(days=i) for i in range(0, ndias)]
      xTickMarks = [xTickMarks[i].strftime("%d/%m/%y") for i in range(0, ndias)]
      ax.set_xticks(ind+0.175)
      xtickNames = ax.set_xticklabels(xTickMarks)
      plt.setp(xtickNames, rotation=45, fontsize=8)
      os.remove("/home/guillermo/temp.png")
      fig.savefig('/home/guillermo/temp.png')
      photo = open('/home/guillermo/temp.png', 'rb')
      bot.send_photo(message.chat.id, photo)


@bot.message_handler(regexp="ET|evapotranspiracion|evapo|ETr|ETa|Evapo")
def handle_message(message):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    start = time.strftime("%Y-%m-%d")
    if("desde" in message.text):
        if("ayer" in message.text):
            start = datetime.date.today() - datetime.timedelta(days=1)
            start = start.strftime("%Y-%m-%d")
        if("hace" in message.text):
            ndias = int(re.findall('\d+', message.text)[0])
            start = datetime.date.today() - datetime.timedelta(days=ndias)
    db = MySQLdb.connect( host='localhost', db='LISIMETRO', user='bot', passwd=clavebot )
    cursor = db.cursor()
    query = ("SELECT Peso_diff FROM Ciclo20162017 WHERE Fecha BETWEEN %s AND %s")
    cursor.execute(query, (start, now))
    results = list(cursor.fetchall())
    results[:] = (value[0] for value in results)
    results[:] = (value for value in results if value > -30)
    bot.reply_to(message, "ET real acumulada: " + str(round(abs(sum(results) / 6.25),2)) + "mm. "
    + "\nDesde :" + str(start) + "\nHasta: " + str(now))
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
