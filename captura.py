#!/usr/bin/python
import serial
import MySQLdb
import time
import re
import subprocess

## Iniciamos
lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
## OJO QUE TENGO LA CLAVE!
BD = MySQLdb.connect( host='localhost', db='Lisimetro', user='guillermo', passwd='***' )
curs = BD.cursor()
s = ['A']
ultimo = ['A']
Peso_last = -999
now = time.strftime("%Y-%m-%d %H:%M:%S")


## Definimos algunas funciones:
def SENSOR_post(n_sensor):
 SENSOR = re.findall('SENSOR ' + str(n_sensor)  + ': (.*?)\|',s)
 if len(SENSOR)>0 and SENSOR[0] != 'FRE X - ADC X ':
  SENSOR = SENSOR[0].split(' ')
 else:
  SENSOR= '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
 return SENSOR

def tg_report(mensaje):
 subprocess.call(["./tg.sh", "Guillermo_Federico_Olmedo", str(mensaje)])

print '>>>>>>>>>>>>>>>>>> ', str(now), " -- Recepcion de datos ONLINE"
tg_report("[LIS] UP " + str(now))
## Y ahora a escuchar:
while True:  ## Aca iniciamos un bucle de 120 segundos:
  s = lisimetro.readline().strip("\r\n")   ## Leemos el puerto serie
  if  True: # s != ultimo:  ### nos fijamos si el valor cambio con respecto a la ultima recepcion
     ultimo = s     
     if True: # len(s) > 170 and len(s) < 205:  ## nos fijamos si parece una cadena valida ## Validador por longitud de cadena
           try:
            LIS = float(re.findall('LIS (.*?)KG', s)[0])   ## desarmamos la cadena y la grabamos
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
            if BATT <= 12.5  ## Reportamos baterias bajas!
             tg_report("[LIS] Low Batt")
            ESTMET = re.findall('ESTMET (.*?)\]',s)
            curs.execute(
                 'insert into Ciclo20142015'
                 '(Fecha, Batt, Peso, Inestable, Peso_diff, E1_Temp_50, E1_Temp_100, E1_Temp_150, E1_Tens_50, E1_Tens_100, E1_Tens_150, E2_Temp_50, E2_Temp_100, E2_Tens_50, E2_Tens_100, ESTMET, Crudo)'
                 'VALUES'
                 '(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                 (time.strftime("%Y-%m-%d %H:%M:%S"), BATT, LIS, MOV[0]=='M', DIFF, SENSOR1[7], SENSOR2[7], SENSOR3[7], SENSOR1[2], SENSOR2[2], SENSOR3[2], SENSOR4[7], SENSOR5[7], SENSOR4[2], SENSOR5[2], ESTMET[0], s))
            BD.commit()
            Peso_last = LIS
           except IndexError:
            pass  #si la cadena tenia algun problemo
     else:  ## Si no era una cadena valida la pasamos
      print '>>>> ERRONEA:', str(time.strftime("%Y-%m-%d %H:%M:%S")), s
  else: ## Si es la misma de antes
    print 'SIN CAMBIOS ', str(time.strftime("%Y-%m-%d %H:%M:%S")), s, ' VS ', ultimo
     
  time.sleep(120)
