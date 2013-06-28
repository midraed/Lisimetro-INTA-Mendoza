#!/usr/bin/python
import serial
import MySQLdb
import time
import re

lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=5)
BD = MySQLdb.connect( host='localhost', db='LISIMETRO', user='guillermo', passwd='******' )
curs = BD.cursor()
s = 'A', 'S', 'D'
ultimo = 'A','S','D'

while True:
 s = lisimetro.readline().strip("\r\n")
 if s != ultimo:
   if True: ## Aca va la condicion para detectar quien es el emisor s[0]=='S':
            ultimo = s
            s = re.findall(r'\d+', s)
            #s[0] = (5.0 * float(s[0]) * 100.0)/1024.0 - 273.15 Por ej. para convertir de mV a Temp 
            #s[1] = (5.0 * float(s[1]) * 100.0)/1024.0 - 273.15
            #s[2] = (5.0 * float(s[2]) * 100.0)/1024.0 - 273.15
            curs.execute(
                 'insert into prueba'
                 '(Fecha, Temp1_50, Temp2_100, Temp3_150, SENS4, SENS5, SENS6) '
                 'VALUES '
                 '(%s, %s, %s, %s, %s, %s, %s)',
                 (time.strftime("%Y-%m-%d %H:%M:%S"), s[0], s[1], s[2], s[3], s[4], s[5]))
            BD.commit()
 else:
     pass
 time.sleep(120)
