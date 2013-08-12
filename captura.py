#!/usr/bin/python
import serial
import MySQLdb
import time
import re

lisimetro = serial.Serial( '/dev/ttyS0', 9600, timeout=None)
BD = MySQLdb.connect( host='localhost', db='LISIMETRO', user='guillermo', passwd='******' )
curs = BD.cursor()
s = ['A', 'B']
ultimo = ['A', 'B']

while True:
  s = lisimetro.readline().strip("\r\n")
  if s != ultimo:
            ultimo = s
            LIS = re.findall('LIS (.*?)KG', s)
            MOV = re.findall('KG(.*?) \|', s)
            R0 = re.findall('ESCLAVO_0 (.*?)\|',s)
            R0 = R0[0].split(' ')
            ESTMET = re.findall('ESTMET (.*?)\]',s)
            curs.execute(
                 'insert into prueba2'
                 '(Fecha, Peso, Inestable, TEMP50, TEMP100, TEMP150, TENS50, ESTMET) '
                 'VALUES '
                 '(%s, %s, %s, %s, %s, %s, %s, %s)',
                 (time.strftime("%Y-%m-%d %H:%M:%S"), float(LIS[0]), MOV[0]=='M', R0[0], R0[2], R0[4], R0[5], ESTMET[0]))
            BD.commit()
  else:
     pass
  time.sleep(100)

  
