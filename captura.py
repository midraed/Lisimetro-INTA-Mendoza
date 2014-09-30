#!/usr/bin/python
import serial
import MySQLdb
import time
import re
import subprocess

## Iniciamos
lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
f = open('/home/guillermo/Lisimetro-INTA-Mendoza/clave')
clave = f.read().strip('\n')
f.close
BD = MySQLdb.connect( host='localhost', db='Lisimetro', user='guillermo', passwd=clave )
curs = BD.cursor()
s = ['NA']
Peso_last = -999 # dummy para el arranque
now = time.strftime("%Y-%m-%d %H:%M:%S")
extra = 0 # tiempo extra en el loop principal
LOWBATT = 0 # estado de baja bateria detectado (LOWBATT=1)

lisimetro.write('<INT 0110>')

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

while True:  
  try:
    s = lisimetro.readline().strip("\r\n")   ## Leemos el puerto serie
    ultimo = s     
    MOV = re.findall('KG(.*?) \|', s) 
    LIS = float(re.findall('LIS\s*([-]?\d{1,3}\.?\d{0,3})\s?K', s)[0])
    if Peso_last == -999:
      DIFF = -999
    else:
      DIFF = LIS - Peso_last 
      print 'Correcto:', str(time.strftime("%Y-%m-%d %H:%M:%S")), s, 'last: ', Peso_last, 'diff: ', DIFF
    SENSOR1 = SENSOR_post(1)  # oh yeah  
    SENSOR2 = SENSOR_post(2)
    SENSOR3 = SENSOR_post(3)
    SENSOR4 = SENSOR_post(4)
    SENSOR5 = SENSOR_post(5)
    BATT = float(re.findall('VCC = (.*?)V', s)[0]) ## Capturamos el valor de la bateria
    if BATT <= 12.5 and LOWBATT == 0:  ## Si las baterias bajan a 12.5, y no lo habiamos reportado, lo hacemos
      LOWBATT = 1
      tg_report("[LISIMETRO] Low Batt")
      lisimetro.write('<INT 0550>')  # Ademas cambiamos el intervalo a *casi* 10 minutos,... para preservar la bateria que queda..
      extra =  480 # Esto + el int normal de 120, da 10  minutos
    if BATT > 12.6 and LOWBATT == 1: ## Cuando la bateria sube de 12.6, volvemos al estado normal
      LOWBATT = 0
      tg_report("[LISIMETRO Bateria Normal")
      lisimetro.write('<INT 0110>')
      extra = 0
    ESTMET = re.findall('ESTMET (.*?)\]',s)
    curs.execute('insert into Ciclo20142015'
                 '(Fecha, Batt, Peso, Inestable, Peso_diff, E1_Temp_50, E1_Temp_100, E1_Temp_150, E1_Tens_50, E1_Tens_100, E1_Tens_150, E2_Temp_50, E2_Temp_100, E2_Tens_50, E2_Tens_100, ESTMET, Crudo)'
                 'VALUES'
                 '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                 (time.strftime("%Y-%m-%d %H:%M:%S"), BATT, LIS, MOV[0]=='M', DIFF, SENSOR1[6], SENSOR2[6], SENSOR3[6], SENSOR1[1],
                   SENSOR2[1], SENSOR3[1], SENSOR4[6], SENSOR5[6], SENSOR4[1], SENSOR5[1], ESTMET[0], s))
    BD.commit()
    Peso_last = LIS
  except (IndexError, ValueError):
    print '>>>>>>>>>>>>   IndexError ', str(time.strftime("%Y-%m-%d %H:%M:%S")), s
    pass  
  except (serial.serialutil.SerialException):
    lisimetro.close
    time.sleep(30)
    lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
  except:
    print "Unexpected error:", sys.exc_info()[0]
    tg_report("Unexpected error:", sys.exc_info()[0])
  time.sleep(120+extra)
