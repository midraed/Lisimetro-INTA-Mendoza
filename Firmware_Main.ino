/* INCLUDES */
/* ================================================================== */

#include <Scheduler.h>
#include <LiquidCrystal.h>
#include <EEPROMex.h>
#include "Arduino.h"

/* CONFIGURACIÓN */
/* ================================================================== */

#define MAX_CANT_SENS			(8)

#define ACTIVE_LCD_TIME			(10)

/* MACROS */
/* ================================================================== */

// Operaciones con bytes e int
#define _LSB(x) 		(byte)(x & 0xFF)
#define _MSB(x) 		(byte)((x >> 8) & 0xFF)
#define _INT(MSB,LSB)		(int)((int)(MSB << 8) + (int)LSB)

// Pines de control del LCD
#define BUT_DOWN		(3)
#define BUT_UP			(2)

#define LCD_D4			(4)
#define LCD_D5			(5)
#define LCD_D6			(6)
#define LCD_D7			(7)
#define LCD_RS 			(8)
#define LCD_EN			(9)

// Se definen los pines digitales significativos
#define LED 			(13)
#define EN_TX_485		(22)
#define EN_REMOTE_SENS		(23)
#define PRESSURE		(25)
#define O_VALV   	        (A11)
#define C_VALV                  (A12)
#define RESET_CELDA             (10)

#define SFD			('<')
#define EOFD			('>')

#define INT_ENV_ADDR		(0)
#define CANT_SENS_ADDR		(1)                          

#define TEMPA_ADDR              (2)
#define TEMPB_ADDR              (6)
#define WATA_ADDR               (10)
#define WATB_ADDR               (14)
#define SCH_ACT                 (18)

#define XBee			(Serial)
#define Lisimetro		(Serial1)
#define EstMet			(Serial2)
#define Esclavo			(Serial3)

#define VCC_ADC			(0)
#define VREF			(2.45)                      
#define RS1			(15)
#define VCC_CONV_FACTOR		(1.82 / 12.09)

#define BOUNCING		(200)

typedef struct lisimetro_tag
{
  bool valido;
  float valor;
  String unidad;
}
lisimetro_t;

typedef struct sensor_tag
{
  int hs;
  int t;
  int tgrad;
  int tens;
  bool valido;
}
sensor_t;

/* VARIABLES GLOBALES */
/* ================================================================== */

// Últimos valores de los sensores
sensor_t valorSensor[MAX_CANT_SENS];

// Último valor del lisímetro
lisimetro_t valActLis;

// Última cadena enviada por la estación
String cadenaEstMet = "";

// Intervalo de envío
int intervaloEnvio;

// Cantidad de sensores
int cantSens;

// Sensor siendo muestreado actualmente
int sensMuestreado = 0;

// Objetos que permiten manejar tareas programadas
Scheduler scheduler_envio = Scheduler();
Scheduler scheduler_menu = Scheduler();

// Objeto que permite manejar el LCD
LiquidCrystal lcd(LCD_RS, LCD_EN, LCD_D4, LCD_D5, LCD_D6, LCD_D7);

// Variables del menú
volatile int menuItem = 1;
volatile bool menuEnabled = 0;

/* FUNCIONES DE ARDUINO */
/* ================================================================== */

void setup()
{
  // Configuración de pines
  pinMode(BUT_UP, INPUT);
  digitalWrite(BUT_UP, HIGH); // turn on pullup
  pinMode(BUT_DOWN, INPUT);
  digitalWrite(BUT_DOWN, HIGH); // turn on pullup
  pinMode(LED, OUTPUT);
  pinMode(EN_TX_485, OUTPUT);
  pinMode(EN_REMOTE_SENS, OUTPUT);
  pinMode(PRESSURE, INPUT);
  pinMode(O_VALV, OUTPUT);
  digitalWrite(O_VALV, LOW);
  pinMode(C_VALV, OUTPUT);
  digitalWrite(C_VALV, LOW);
  pinMode(RESET_CELDA, OUTPUT);
  digitalWrite(RESET_CELDA, LOW);

  digitalWrite(LED, LOW);
  digitalWrite(EN_TX_485, LOW);
  digitalWrite(EN_REMOTE_SENS, LOW);

  // Configuración del ADC
  analogReference(INTERNAL2V56);
  analogRead(VCC_ADC); // Estabiliza la primer medición

  // Inicialización del puertos serie
  XBee.begin(9600);
  Lisimetro.begin(9600);
  EstMet.begin(9600);
  Esclavo.begin(9600);

  // Inicialización del LCD
  lcd.begin(16, 2);
  delay(1000); 

  // Mensaje de bienvenida
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("INTA EEA MENDOZA");
  XBee.println("INTA EEA MENDOZA");
  delay(1000);
  lcd.setCursor(0, 1);
  lcd.print("ESTACION REMOTA");
  XBee.println("ESTACION REMOTA");
  delay(3000);
  
    // Inicialización de variables
  valActLis.valido = false;
  valActLis.valor = 0;

  // Leer el valor almacenado como intervalo de envío en segundos (si hay un cero guardado, usar 15 segundos)
  intervaloEnvio = 1000 * EEPROM.read(INT_ENV_ADDR);
  if (intervaloEnvio <= 0)
    intervaloEnvio = 15000;

  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("INT. ENVIO: ");
  lcd.print((intervaloEnvio / 1000));
  lcd.print("s");
  XBee.print("INTERVALO DE ENVIO DE ");
  XBee.print((intervaloEnvio / 1000), DEC);
  XBee.println("s");

  // Leer el valor almacenado como cantidad de sensores
  cantSens = EEPROM.read(CANT_SENS_ADDR);
  if ((cantSens <= 0) || (cantSens > MAX_CANT_SENS))
    cantSens = MAX_CANT_SENS;

  lcd.setCursor(0, 1);
  lcd.print("CANT. SENS: ");
  lcd.print(cantSens);
  XBee.print("CANTIDAD DE SENSORES: ");
  XBee.println(cantSens);

  delay(2000);

  // Realiza el primer muestreo
  lcd.clear();

  lcd.setCursor(0, 0);
  lcd.print("Realizando el");
  lcd.setCursor(0, 1);
  lcd.print("primer muestreo");
  XBee.println("Realizando el primer muestreo...");

  muestreo();

  // Espera a que lleguen las muestras
  delay((cantSens * 0.15 + 2) * 1000);

  lcd.clear();

  // Configuración de interrupciones
  attachInterrupt(0, upMenu, RISING);
  attachInterrupt(1, downMenu, RISING);

  // Programar envío de valores
  scheduler_envio.schedule(envio_prog, intervaloEnvio);

  // Programar y activar menú
  scheduler_menu.schedule(menu_prog, 1000);
}

void loop()
{
  // Actualizar los schedulers
  scheduler_menu.update();
  scheduler_envio.update();

  // Leer los datos enviados por la Estación meteorológica y almacenarlos
  while (EstMet.available())
  {
    char inChar = (char)EstMet.read();
    if ((inChar != '\n') && (inChar != '\r'))
      cadenaEstMet.concat(inChar);
  }

  // Leer los datos enviados por el Lisímetro y guardar el último valor

  if (Lisimetro.available())
  {
    delay(100);

    char lectura[20];
    int cantChar = 14;
    lectura[0] = (char)Lisimetro.read();

    if(lectura[0] == 0x02)
    {
      for (int i = 1; i < cantChar; i++)
      {
        lectura[i] = (char)Lisimetro.read();
      }

      if (lectura[9] == 'K')
      {
        valActLis.unidad = "";
        for (int i = 0; i < 3; i++)
          valActLis.unidad += lectura[9 + i];

        char valor[7];
        for (int i = 0; i < 7; i++)
          valor[i] = lectura[2 + i];

        valActLis.valor = atof(valor);

        if (lectura[1] == '-')
          valActLis.valor *= -1;

        valActLis.valido = true;
      }
    }

    Lisimetro.flush();
  }
  
  // Leer los datos recibidos por el Esclavo y analizarlos
  if (Esclavo.available())
  {
    String paquete = "";

    char inChar = (char)Esclavo.read();
    paquete.concat(inChar);

    if (inChar == SFD)
    {
      delay(100);

      while (Esclavo.available())
      {
        inChar = (char)Esclavo.read();
        paquete.concat(inChar);

        if (inChar == EOFD)
          break;
      }
    }

    if (paquete.startsWith("<S") && paquete.endsWith(">")) // <S0|FRE1950|ADC0589>
    {
      char charNumEsclavo[] = { paquete[2] };
      int numEsclavo = atoi(charNumEsclavo);

      char charhs[] = { paquete[7], paquete[8], paquete[9], paquete[10] };
      valorSensor[numEsclavo].hs = atoi(charhs);
      int valor = ((EEPROM.readFloat(WATA_ADDR)) * pow((valorSensor[numEsclavo].hs),-(EEPROM.readFloat(WATB_ADDR))));  
      
      if(valor<=0)
        valorSensor[numEsclavo].tens=0;
      else if(valor>=200)
        valorSensor[numEsclavo].tens=200;
      else if(valor>=0 && valor<=200)
        valorSensor[numEsclavo].tens=valor;
      
      char chart[] = { paquete[15], paquete[16], paquete[17], paquete[18] };
      valorSensor[numEsclavo].t = atoi(chart);
      float temp= valorSensor[numEsclavo].t * EEPROM.readFloat(TEMPA_ADDR) - EEPROM.readFloat(TEMPB_ADDR);
      valorSensor[numEsclavo].tgrad =temp;
      valorSensor[numEsclavo].valido = true;
    }
   Esclavo.flush();
  }

  // Lee los datos recibidos por el XBee y los analiza:
  if (XBee.available())
  {
    String paquete = "";

    char inChar = (char)XBee.read();
    paquete.concat(inChar);

    if (inChar == SFD)
    {
      delay(100);

      while (XBee.available())
      {
        inChar = (char)XBee.read();
        paquete.concat(inChar);

        if (inChar == EOFD)
          break;
      }
    }

    if (paquete.startsWith("<VALV ") && paquete.endsWith(">"))
    {
      char valchar[] = { paquete[6] };
      int valor = atoi(valchar);
      
      if (valor == 1)
      {
        digitalWrite(O_VALV, HIGH);
        delay(30);
        digitalWrite(O_VALV, LOW);
        XBee.println("[VALVULA ENCENDIDA]");
      }
      
      else
      {
        digitalWrite(C_VALV, HIGH);
        delay(30);
        digitalWrite(C_VALV, LOW);
        XBee.println("[VALVULA APAGADA]");
      }
    }
    
    else if (paquete.startsWith("<TEMP_A ") && paquete.endsWith(">"))
    { 
      char valchar[] = { paquete[8],paquete[9],paquete[10],paquete[11],paquete[12],paquete[13],paquete[14],paquete[15] };
      EEPROM.writeFloat(TEMPA_ADDR, atof(valchar));

        XBee.println("");
        XBee.print("[CAMBIO COEFICIENTE A TEMPERATURA. A= ");
        XBee.print(atof(valchar));
        XBee.print("]");
        XBee.println("");
    }
    
     else if (paquete.startsWith("<TEMP_B ") && paquete.endsWith(">"))
    {
      char valchar[] = { paquete[8],paquete[9],paquete[10],paquete[11],paquete[12],paquete[13],paquete[14],paquete[15] };
      EEPROM.writeFloat(TEMPB_ADDR, atof(valchar));
       
        XBee.println("");
        XBee.print("[CAMBIO COEFICIENTE B TEMPERATURA. B= ");
        XBee.print(atof(valchar));
        XBee.print("]");
        XBee.println("");
    }
    
    else if (paquete == "<TEMP DEFAULT>")
      {
        EEPROM.writeFloat(TEMPA_ADDR, 0.38);
        EEPROM.writeFloat(TEMPB_ADDR, 206.41);
        XBee.println("[COEFICIENTES DE TEMPERATURA POR DEFECTO]");
        XBee.println("A=0.38");
        XBee.println("B=206.41");
      }
    
    else if (paquete.startsWith("<WAT_A ") && paquete.endsWith(">"))
    {
      char valchar[] = { paquete[7],paquete[8], paquete[9], paquete[10], paquete[11], paquete[12], paquete[13], paquete[14], paquete[15], paquete[16] };
      EEPROM.writeFloat(WATA_ADDR, atof(valchar));
        
        XBee.println("");
        XBee.print("[CAMBIO COEFICIENTE A WATERMARK. A= ");
        XBee.print(atof(valchar));
        XBee.print("]");
        XBee.println("");
    }
     
     else if (paquete.startsWith("<WAT_B ") && paquete.endsWith(">"))
    {
      char valchar[] = { paquete[7], paquete[8], paquete[9], paquete[10], paquete[11], paquete[12], paquete[13] };
      EEPROM.writeFloat(WATB_ADDR, atof(valchar));
        
        XBee.println("");
        XBee.print("[CAMBIO COEFICIENTE B WATERMARK. B= ");
        XBee.print(atof(valchar));
        XBee.println("]");
        XBee.println("");
    }
    
        else if (paquete == "<WAT DEFAULT>")
      {
        EEPROM.writeFloat(WATA_ADDR, 1116173.81);
        EEPROM.writeFloat(WATB_ADDR, 1.53);
        XBee.println("[COEFICIENTES DE WATERMARK POR DEFECTO]");
        XBee.println("A=1116173.81");
        XBee.println("B=1.53");
      }

    else if (paquete == "<DESINT>")
    {
      //Desactivo scheduler envio
       EEPROM.write(SCH_ACT, 0x00);  
       XBee.println("Intervalo de envio desactivado.");  
    }
      
    else if (paquete == "<ACTINT>")
    {
      //Activo scheduler envio
       EEPROM.write(SCH_ACT, 0xFF);  
       XBee.println("Intervalo de envio activado.");
       scheduler_envio = Scheduler();
       scheduler_envio.schedule(envio_prog, intervaloEnvio);
    }
    
    else if(paquete.startsWith("<INT ") && paquete.endsWith(">"))
    {
      char strval[] = { paquete[5], paquete[6], paquete[7], paquete[8] };
      int valor;

      if (paquete == "<INT AUTO>")
      {
        valor = (int)(2 + cantSens * 0.15);
      }
      else
      {
        valor = atoi(strval);
      }

      if (valor >= (int)(2 + cantSens * 0.15))
      {
        XBee.print("[CAMBIO DE INTERVALO DE ENVIO A ");
        XBee.print(valor);
        XBee.println(" SEG.]");

        intervaloEnvio = valor * 1000;
        EEPROM.write(INT_ENV_ADDR, valor);

//Reprogramo y activo el scheduler para el nuevo intervalo
        EEPROM.write(SCH_ACT, 0xFF);
        scheduler_envio = Scheduler();
        scheduler_envio.schedule(envio_prog, intervaloEnvio);
      }
      else
      {
        XBee.print("[INTERVALO NO VALIDO. POR LA CANTIDAD DE SENSORES DEBE SER MAYOR A ");
        XBee.print((int)(2 + cantSens * 0.15));
        XBee.println(" SEG.]");
      }
    }
    
    else if(paquete.startsWith("<SENS ") && paquete.endsWith(">"))
    {
      char strval[] = { paquete[6], paquete[7] };
      int valor = atoi(strval);

      XBee.print("[CANTIDAD DE SENSORES: ");
      XBee.print(valor);
      XBee.println("]");

      cantSens = valor;
      EEPROM.write(CANT_SENS_ADDR, cantSens);

      valor = (int)(2 + cantSens * 0.15);
      if (intervaloEnvio / 1000 < valor)
      {
        XBee.print("[SE CAMBIO EL INTERVALO DE ENVIO A ");
        XBee.print(valor);
        XBee.println(" SEG.]");

        intervaloEnvio = valor * 1000;
        EEPROM.write(INT_ENV_ADDR, valor);

//Reprogramo y activo el scheduler para el nuevo intervalo
        EEPROM.write(SCH_ACT, 0xFF);
        scheduler_envio = Scheduler();
        scheduler_envio.schedule(envio_prog, intervaloEnvio);
      }
    }
    
    else if(paquete == "<COEF>")
    {
        XBee.println(EEPROM.readFloat(TEMPA_ADDR));
        XBee.println(EEPROM.readFloat(TEMPB_ADDR));
        XBee.println(EEPROM.readFloat(WATA_ADDR));
        XBee.println(EEPROM.readFloat(WATB_ADDR));
    }
    
    else if(paquete == "<VALORES>")
    {
      envio();
    }
        else if (paquete== "<RESET_CELDA>")
    {
        digitalWrite(RESET_CELDA, HIGH);
        delay(2000);
        digitalWrite(RESET_CELDA, LOW);
        XBee.println("[CELDA RESETEADA]");
    }
    else
    {
      XBee.println("[COMANDO NO VALIDO]");
    }
  }
  XBee.flush();
}

/* FUNCIONES DE USUARIO */
/* ================================================================== */

void envio_prog()
{
  envio();
  // Reprograma el envío si esta activado
  if((EEPROM.read(SCH_ACT)) == 0xFF)
    scheduler_envio.schedule(envio_prog, intervaloEnvio);
}

void envio()
{
   float V, porc_v;
  
  // Valor del lisímetro
  XBee.print("[VALORES > LIS ");
  if (valActLis.valido)
  {
    XBee.print(valActLis.valor, 3);
    XBee.print(" ");
    XBee.print(valActLis.unidad);
    XBee.print(" ");
  }
  else
  {
    XBee.print("-99999.999 KG ");
  }
   
  V=read_vcc();
  porc_v=((V*100)/13.6);
  XBee.print(" | VCC = ");
  XBee.print(V);
  XBee.print("V");
  XBee.print(" | ");
  XBee.print(porc_v);
  XBee.print("%");

  // Valores de los sensores
  for (int i = 1; i <= cantSens; i++)              
  {
    XBee.print(" | SENSOR ");
    XBee.print(i);
    XBee.print(": ");

    if (valorSensor[i].valido)
    {
      XBee.print("TEN ");
      XBee.print(valorSensor[i].tens);
      XBee.print(" b");
      XBee.print(" - T:  ");
      XBee.print(valorSensor[i].tgrad);
      XBee.print(" C");
    }
    else
    {
      XBee.print("FRE X - ADC X");
    }

    // Una vez enviados, invalida los datos
    valorSensor[i].valido = false;
  }
  // Reinicia el muestreo de sensores
  sensMuestreado = 0;

  // Valores de la estación meteorológica
  XBee.print(" | ESTMET ");
  XBee.print(cadenaEstMet);

  XBee.println("]");

  // Resetea valores almacenados
  valActLis.valido = false;
  cadenaEstMet = "";

  // Envía la orden de muestreo
  muestreo();
}

void muestreo()
{
  // Alimenta los sensores
  digitalWrite(EN_REMOTE_SENS, HIGH);

  // Programa el apagado para mantenerlos alimentados por 1 + cantSens + 1 segundos
  scheduler_envio.schedule(apagar_sensores, (1.5 + cantSens * 0.15) * 1000);
}

void apagar_sensores()
{
  // Apaga la alimentación de los sensores
  digitalWrite(EN_REMOTE_SENS, LOW);
}

void upMenu()
{
  static unsigned long lastMillis = 0;
  unsigned long currentMillis = millis();

  if (currentMillis - lastMillis > BOUNCING)
  {
    // Cambia de ítem
    if (menuEnabled)
    {
      menuItem++;
      if (menuItem > (cantSens + 3)) menuItem = 1;

      // Actualiza en pantalla
      menu();
    }
    else
    {
      // Activa el menú
      menuEnabled = true;

      // Comienza a mostrar el menú nuevamente
      menu_prog();
    }
  }

  lastMillis = currentMillis;
}

void downMenu()
{
  static unsigned long lastMillis = 0;
  unsigned long currentMillis = millis();

  if (currentMillis - lastMillis > BOUNCING)
  {

    // Cambia de ítem
    if (menuEnabled)
    {
      menuItem--;
      if (menuItem < 1) menuItem = cantSens + 3;        

      // Actualiza en pantalla
      menu();
    }
    else
    {
      // Activa el menú
      menuEnabled = true;

      // Comienza a mostrar el menú nuevamente
      menu_prog();
    }
  }

  lastMillis = currentMillis;
}

void enable_interrupts()
{
  interrupts();
}

void menu_prog()
{
  static int countSeconds = 0;

  // Si el item cambió, comienza de nuevo el conteo
  static int prevMenuItem = cantSens + 3;
  if (menuItem != prevMenuItem) countSeconds = 0;
  prevMenuItem = menuItem;

  if ((countSeconds < ACTIVE_LCD_TIME) && menuEnabled)
  {
    menu();
    scheduler_menu.schedule(menu_prog, 2000);

    countSeconds++;
  }
  else
  {
    menuEnabled = false;
    countSeconds = 0;
    lcd.clear();
  }
}

void menu()
{
  lcd.clear();

  if (menuEnabled)
  {
    lcd.setCursor(0, 0);
    lcd.print(menuItem);
    lcd.setCursor(1, 0);
    lcd.print("-");
    lcd.setCursor(2, 0);

    if (menuItem <= cantSens)                
    {
      lcd.print("Sensor ");
      lcd.print(menuItem);
      show_sensor(menuItem);
    }
    else
    {
      if (menuItem == (cantSens+1))          
      {
        lcd.print("Alimentacion");
        show_vcc();
      }

      if (menuItem == (cantSens + 2))      
      {
        lcd.print("Lisimetro");
        show_lisimetro();
      }

      if (menuItem == (cantSens + 3))      
      {
        lcd.print("Contraste");
        show_contrast();
      }
    }
  }
}

void show_sensor(int sensor)
{
  if (valorSensor[menuItem].valido)
  {
    lcd.setCursor(0, 1);
    lcd.print("HS=");
    lcd.print(valorSensor[menuItem].tens);
    lcd.print(" b");
    lcd.setCursor(8, 1);
    lcd.print("T=");
    lcd.print(valorSensor[menuItem].tgrad);
    lcd.print(" C");
  }
  else
  {
    lcd.setCursor(0, 1);
    lcd.print("HS=X");
    lcd.setCursor(8, 1);
    lcd.print("T=X");
  }
}

void show_vcc()                            
{
  float V, porc_v;
  V=read_vcc();
  porc_v=((V*100)/13.6);
  
  lcd.setCursor(1, 1);
  lcd.print(V);
  lcd.print("V");
  lcd.print(" | ");
  lcd.print(porc_v);
  lcd.print("%");
  
  
}

void show_lisimetro()
{
  // Mostrar valor
  lcd.setCursor(0, 1);
  if (valActLis.valido)
  {
    lcd.print(valActLis.valor);
    lcd.print(valActLis.unidad);
  }
  else
  {
    lcd.print("SIN VALOR");
  }
}

void show_contrast()
{
  // Mostrar valor
  lcd.setCursor(0, 1);
  for (int x = 0; x < 16; x++) lcd.print((char)0xFF);
}

float read_vcc()                                                      
{
   float V;
  // Testear la tensión de alimentación
  int adc = analogRead(VCC_ADC);
  V=((float)adc * VREF / 1024.0) / (float)VCC_CONV_FACTOR;
  return (V);
}
