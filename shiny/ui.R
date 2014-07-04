library(shiny)
library(ShinyDash)
library(RMySQL)
library(shinyExt)


shinyUI(bootstrapPage(
  h1("Estación lisimétrica EEA Mendoza INTA"),
     
  gridster(tile.width = 250, tile.height = 250,
           
           ### Control menu ####
           gridsterItem(col = 1, row = 1, size.x = 1, size.y = 2,
                        
                                                
                         
                        
                        dateRangeInput("fechaRango", "Intervalo temporal:",
                                       start = Sys.Date()-3,
                                       end   = NULL, language="es", separator = "a", format="dd/mm/yyyy" ),
                        
#                         BOTONES PUTOS DE FECHA
#                         actionButton(inputId="menosdia", label="-1 Día"),
#                         actionButton(inputId="hoy", label="Hoy"),
#                         actionButton(inputId="masdia", label="+1 Día"),
#                        
                                                
                         
                        tags$p(
                        ),                        tags$p(
                        ),
                        
                        selectInput(inputId = "sstatus",
                                    label = "(Debug) Elegir estado:",
                                    choices = c(0, 1, 2),
                                   selected = 0),
                        
           
                        tags$p(
                          tags$br(),
                          tags$a(href = "https://github.com/trestletech/ShinyDash", "Source code")
                        )
                        
           ),
           
           ## Temperatura de suelo  ####
           gridsterItem(col = 1, row = 3, size.x = 2, size.y = 1,
                        plotOutput("TempPlot", height = "250px")
           ),
           
           ## Vista tabular  ####
           gridsterItem(col = 1, row =4, size.x = 4, size.y = 2,
                        tableOutput("tabla")
           ),
         
           
           ## Agua en el suelo  ####
           gridsterItem(col = 3, row = 3, size.x = 2, size.y = 1,
                        plotOutput("WatPlot", height = "250px")
           ),
           
           ## Diviner   ####
           gridsterItem(col = 5, row = 3, size.x = 2, size.y = 2,
                        selectInput(inputId = "profdiviner",
                                    label = "Profundidad datos Diviner:",
                                    choices = c("10cm"=5,"20cm"=6,"30cm"=7,"40cm"=8,"50cm"=9,"60cm"=10,"70cm"=11,"80cm"=12,"90cm"=13,"100cm"=14,Perfil=15),
                                    selected = 15),
#                         checkboxGroupInput("variable", "Variable:",
#                                            c("Cylinders" = "cyl",
#                                              "Transmission" = "am",
#                                              "Gears" = "gear")),
#                         div(border= '1px solid black',overflow= 'hidden', display='inline-block'),
#                         checkboxInput("outliers", "Show outliers", FALSE),
#                         checkboxInput("outliers1", "Show outliers", FALSE),
                        plotOutput("GrafDiv", height = "450px")
           ),
           
           ### ETr acumulada  ####
           gridsterItem(col = 5, row = 2, size.x = 1, size.y = 1,
                        gaugeOutput("live_gauge", width=250, height=200, units="mm", min=0, max=20, title="ETr diaria acumulada")
           ),
           
           ### Status  ####
           gridsterItem(col = 6, row = 1, size.x = 1, size.y = 1,
                        tags$div(class = 'grid_title', 'Status'),
                        htmlWidgetOutput('status',
                                         tags$div(id="text", class = 'grid_bigtext'),
                                         tags$p(id="subtext"),
                                         tags$p(id="lastdata",
                                                `data-filter`="prepend 'Último dato recibido el: ' | append ''",
                                                `class`="text"))
           ),
           
           ### Temperatura del aire y estado de la atm  ####
           gridsterItem(col = 5, row = 1, size.x = 1, size.y = 1,
                        weatherWidgetOutput("weatherWidget", width="100%", height="90%")
           ),
           
           ### ET instantánea  ####
           gridsterItem(col = 2, row = 1, size.x = 3, size.y = 2,
                        plotOutput("ETinstPlot", height = "500px")
           ),
           
           ### Caja de pruebas  ####
           gridsterItem(col = 6, row = 2, size.x = 1, size.y = 1,
                        verbatimTextOutput("pruebas")
           )
  ))
)