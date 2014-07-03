#!/usr/bin/python
import serial
import MySQLdb
import time
import re

lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
## OJO QUE TENGO LA CLAVE!
BD = MySQLdb.connect( host='localhost', db='Lisimetro', user='guillermo', passwd='***' )
curs = BD.cursor()
s = ['A']
ultimo = ['A']
Peso_last = -999


	
now = time.strftime("%Y-%m-%d %H:%M:%S")
print '>>>>>>>>>>>>>>>>>> ', str(now), " -- Recepcion de datos ONLINE"

while True:  ## Aca iniciamos un bucle de 120 segundos:
  s = lisimetro.readline().strip("\r\n")   ## Leemos el puerto serie
  if  1==1: # s != ultimo:  ### nos fijamos si el valor cambio con respecto a la ultima recepcion
     ultimo = s     
     if 1==1: # len(s) > 170 and len(s) < 205:  ## nos fijamos si parece una cadena valida ## Validador por longitud de cadena
           try:
            LIS = float(re.findall('LIS (.*?)KG', s)[0])   ## desarmamos la cadena y la grabamos
            MOV = re.findall('KG(.*?) \|', s)
            if Peso_last == -999:
             DIFF = -999
            else:
             DIFF = LIS - Peso_last 
            print 'Correcto:', str(time.strftime("%Y-%m-%d %H:%M:%S")), s, 'last: ', Peso_last, 'diff: ', DIFF
            SENSOR1 = re.findall('SENSOR 1: (.*?)\|',s)  # Esto se repite para cada sensor... deberia ser una funcion..!
            if len(SENSOR1)>0 and SENSOR1[0] != 'FRE X - ADC X ':
             SENSOR1 = SENSOR1[0].split(' ')
            else:
             SENSOR1 = '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
            SENSOR2 = re.findall('SENSOR 2: (.*?)\|',s)
            if len(SENSOR2)>0 and SENSOR2[0] != 'FRE X - ADC X ':
             SENSOR2 = SENSOR2[0].split(' ')
            else:
             SENSOR2 = '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
            SENSOR3 = re.findall('SENSOR 3: (.*?)\|',s)
            if len(SENSOR3)>0 and SENSOR3[0] != 'FRE X - ADC X ':
             SENSOR3 = SENSOR3[0].split(' ')
            else:
             SENSOR3 = '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
            SENSOR4 = re.findall('SENSOR 4: (.*?)\|',s)
            if len(SENSOR4)>0 and SENSOR4[0] != 'FRE X - ADC X ':
             SENSOR4 = SENSOR4[0].split(' ')
            else:
             SENSOR4 = '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
            SENSOR5 = re.findall('SENSOR 5: (.*?)\|',s)
            if len(SENSOR5)>0 and SENSOR5[0] != 'FRE X - ADC X ':
             SENSOR5 = SENSOR5[0].split(' ')
            else:
             SENSOR5 = '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999', '-999'
            BATT = float(re.findall('VCC = (.*?)V', s)[0]) ## Capturamos el valor de la bateria
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
