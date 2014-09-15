#!/usr/bin/python
import serial
import MySQLdb
import time
import re
import subprocess

## Iniciamos
lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
BD = MySQLdb.connect( host='localhost', db='Lisimetro', user='guillermo', passwd='***' )
curs = BD.cursor()
s = ['NA']
Peso_last = -999
now = time.strftime("%Y-%m-%d %H:%M:%S")

lisimetro.write('<INT 0060>')

## Definimos algunas funciones:
def SENSOR_post(n_sensor):
  SENSOR = re.findall('SENSOR ' + str(n_sensor)  + ': (.*?)\|',s)
  if len(SENSOR)>0 and SENSOR[0] != 'FRE X - ADC X ':
    SENSOR = SENSOR[0].split(' ')
  else:
    SENSOR= ['-999'] * 9
  return SENSOR

def tg_report(mensaje):
  subprocess.call(["/home/guillermo/Lisimetro-INTA-Mendoza/tg.sh", "Guillermo_Federico_Olmedo", str(mensaje)])

print '>>>>>>>>>>>>>>>>>> ', str(now), " -- Recepcion de datos ONLINE"
print 'running from github.com'
tg_report("[LISIMETRO] UP " + str(now))

## Y ahora a escuchar:
while True:
  try:
    s = lisimetro.readline().strip("\r\n")   ## Leemos el puerto serie
    ultimo = s     
      try:
        LIS = float(re.findall('LIS\s*([-]?\d{1,3}\.?\d{0,3})\s?K', s)[0])   ## desarmamos la cadena y la grabamos
        MOV = re.findall('KG(.*?) \|', s) 
        if Peso_last == -999:
          DIFF = -999
        else:
          DIFF = LIS - Peso_last 
        print 'Correcto:', str(time.strftime("%Y-%m-%d %H:%M:%S")), s, 'last: ', Peso_last, 'diff: ', DIFF
        SENSOR1 = SENSOR_post(1)  # oh yeah  --- ahora nomas hace falta poder pasar un parametro de entrada con la cantidad de sensores.. y de paso la duracion del bucle :P
        SENSOR2 = SENSOR_post(2)
        SENSOR3 = SENSOR_post(3)
        SENSOR4 = SENSOR_post(4)
        SENSOR5 = SENSOR_post(5)
        BATT = float(re.findall('VCC = (.*?)V', s)[0]) ## Capturamos el valor de la bateria
        if BATT <= 12.5:  ## Reportamos baterias bajas
          tg_report("[LISIMETRO] Low Batt")
          lisimetro.write('<INT 1500>')  # Ademas cambiamos el intervalo a 25 minutos,... para preservar la bateria que queda..
        ESTMET = re.findall('ESTMET (.*?)\]',s)
        curs.execute(
                 'insert into Ciclo20142015'
                 '(Fecha, Batt, Peso, Inestable, Peso_diff, E1_Temp_50, E1_Temp_100, E1_Temp_150, E1_Tens_50, E1_Tens_100, E1_Tens_150, E2_Temp_50, E2_Temp_100, E2_Tens_50, E2_Tens_100, ESTMET, Crudo)'
                 'VALUES'
                 '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                 (time.strftime("%Y-%m-%d %H:%M:%S"), BATT, LIS, MOV[0]=='M', DIFF, SENSOR1[6], SENSOR2[6], SENSOR3[6], SENSOR1[1],
                   SENSOR2[1], SENSOR3[1], SENSOR4[6], SENSOR5[6], SENSOR4[1], SENSOR5[1], ESTMET[0], s))
        BD.commit()
        Peso_last = LIS
      except (IndexError, TypeError, NameError):
         print '>>>>>>>>>>>>    ERRONEA', str(time.strftime("%Y-%m-%d %H:%M:%S")), s
         pass  #si la cadena tenia algun problema, aunque de longitud correcta
  except SerialError:
   pass
  time.sleep(120)
