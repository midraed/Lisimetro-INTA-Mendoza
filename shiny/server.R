library(shiny)
library(ShinyDash)
library(XML)
library(httr)
library(RMySQL)

datos = dbConnect(MySQL(), user='guillermo', password='midraed561234', dbname='LISIMETRO', host='localhost')
fecha.inicial <- paste(format(Sys.Date()-3, "%d/%m/%Y"), "-", format(Sys.Date(), "%d/%m/%Y"))

shinyServer(function(input, output, session) {
    
  todos.los.datos <- reactive({
    invalidateLater(30000, session)
    datos.online <- fetch(dbSendQuery(datos, "select * from Ciclo2014"), n=-1)
    datos.online$Peso[datos.online$Peso < -10000] = NA
    datos.online$Fecha <- as.POSIXct(strptime(datos.online$Fecha, format= "%Y-%m-%d %H:%M:%S", tz="ART"))
    todos.los.datos <- datos.online
    todos.los.datos$Peso[todos.los.datos$Peso < -500] <- NA
    todos.los.datos$Peso_diff[abs(todos.los.datos$Peso_diff) > 30] <- NA
    todos.los.datos$Peso_diff[is.na(todos.los.datos$Peso_diff)] <- 0
    todos.los.datos
  })
  
  datasetInput <- reactive({
    todos.los.datos()[todos.los.datos()$Fecha >= as.POSIXct(input$fechaRango[1], format="%Y-%m-%d") & todos.los.datos()$Fecha <= as.POSIXct(paste(input$fechaRango[2], " 23:59:59"), format="%Y-%m-%d %H:%M:%S"),]             
    })
  
  
#   ARREGLAR - BOTON PUTO PARA CAMBIAR LA FECHA !!  
#   observe({
#     x <- input$menosdia
# #     updateDateRangeInput("fechaRango",label = paste("Date label", x), start = Sys.Date()-x, end= Sys.Date()-x, min = paste("2013-04-", x-1, sep=""),
# #                          max = paste("2013-04-", x+1, sep=""))
#      })
  

  
diviner <- reactive({
  invalidateLater(30000, session)
  diviner <- fetch(dbSendQuery(datos, "select * from diviner"), n=-1)
  diviner
})
    
  output$table <- renderTable({
    tail(diviner(), 12)
  })
  
  output$TempPlot <- renderPlot({
    plot(datasetInput()[,2], datasetInput()[,5], pch=20, col="blue", xlab="Fecha", ylab="Temperatura (mV)", main="Temperatura del suelo", ylim=c(min(datasetInput()[,5:7]),max(datasetInput()[,5:7])))
    points(datasetInput()[,2], datasetInput()[,6], col="red", pch=20)
    points(datasetInput()[,2], datasetInput()[,7], col="green", pch=20)
    abline(v=c(as.POSIXct(unique(as.Date(datasetInput()[,2])))), lty=3)
    })
  
  output$WatPlot <- renderPlot({
    plot(datasetInput()[,2], datasetInput()[,8], pch=20, col="blue", xlab="Fecha", ylab="Succión matriz (ohm)", main="Agua en el suelo", ylim=c(min(datasetInput()[,8:9]),max(datasetInput()[,8:9])))
   points(datasetInput()[,2], datasetInput()[,9], col="red", pch=20)
   #points(datasetInput()[,2], datasetInput()[,10], col="green", pch=20) ## ANULADO PORQUE ES EL DEL BALDE
  abline(v=c(as.POSIXct(unique(as.Date(datasetInput()[,2])))), lty=3)
  })
  
  output$ETinstPlot <- renderPlot({
    #ETinst <-  datasetInput()[,3]
    #plot(datasetInput()[,2], c(NA, diff(ETinst, 1)), pch=20, col="blue", xlab="Fecha", ylab="Peso (kg)")
    plot(datasetInput()[datasetInput()[,4]==0,2], datasetInput()[datasetInput()[,4]==0,3], pch=20, col="blue", xlab="Fecha", ylab="Peso (kg)")
    points(datasetInput()[datasetInput()[,4]==1,2], datasetInput()[datasetInput()[,4]==1,3], pch=21, col="red")
    par(new = T)
    plot(datasetInput()[,2], cumsum(datasetInput()[,5]), pch=21, col="red",axes = F, xlab = NA, ylab = NA)
    axis(side = 4)
    mtext(side = 4, line = 3, "y")
    abline(v=c(as.POSIXct(unique(as.Date(datasetInput()[,2])))), lty=3)
  })

  output$weatherWidget <- renderWeather(465726, units="c", session=session)
  

  output$live_gauge <- renderGauge({
#     diarios_5am <-  todos.los.datos()[ todos.los.datos()[,2] > strptime(paste(Sys.Date()," 05:00:00"), format= "%Y-%m-%d %H:%M:%S", tz=""),3]
#     ETr_acum <- (head(diarios_5am,1) - tail(diarios_5am,1)) / 6.25
    (tail(cumsum(datasetInput()[,5]),1)*-1)/6.25
    })
  

  output$status <- reactive({
      if (input$sstatus==2)
      list(text="Error", widgetState="alert", subtext="Ha ocurrido un fallo grave", lastdata=as.character(tail(todos.los.datos()[,2], 1)))
    else if (
      ## De las 3 ultimas lecturas de peso, mas de 3 son errores? 
      sum(is.na(tail(datasetInput(),10)[,3])) > 3 |
      ## La estacion meteo se ha reiniciado en los ultimos 30 minutos (15 lecturas)?
      length(grep("Brownout", tail(datasetInput(),15)[,11], value=T)) > 0 |
      ## La estacion no ha mandado datos en 60 minutos? 
      sum(tail(datasetInput(),30)[,11] != "") < 1  
      )
      list(text="Alerta", subtext = "Se han reportado fallos",
           widgetState="warning", lastdata=as.character(tail(todos.los.datos()[,2], 1)))
    else
      list(text="OK", subtext="Equipo funcionando con normalidad", lastdata=as.character(tail(todos.los.datos()[,2], 1)))
      
  })


  
  # Generate a summary of the dataset
  output$pruebas <- renderPrint({
 ## INSERTE AQUI PELOTUDECES PARA PROBAR:
    #cumsum(datasetInput()[,5])
   input$menosdia
    })  
    
  output$tabla <- renderTable({
#     tablatemporal <- tail(datasetInput(),5)[,1:11]
#     tablatemporal[,2] <- as.character(tablatemporal[,2])
#     tablatemporal
      tail(diviner(),4)
  })
  
output$GrafDiv <- renderPlot({
  i = as.integer(input$profdiviner)
  divinertab <- diviner()
  divinertab$Acum <- rowSums(divinertab[,5:14])
  divinertab$Fecha <- paste(divinertab$Fecha, divinertab$Hora)
  divinertab$Fecha <- as.POSIXct(strptime(divinertab$Fecha, format= "%d/%m/%Y %H:%M", tz=""))
#    plot(divinertab$Fecha[divinertab$Tubo==20], divinertab[divinertab$Tubo==20,i], ylim=c(min(divinertab[,i]), max(divinertab[,i])))
  plot(divinertab$Fecha[divinertab$Tubo==20], divinertab[divinertab$Tubo==20,i], ylim=c(min(divinertab[,i]), max(divinertab[,i])), col="dark green", xlab="Fecha", ylab="Contenido de Agua %vol", type="l", main=paste("Contenido de agua", names(divinertab)[i]))
   lines(divinertab$Fecha[divinertab$Tubo==21], divinertab[divinertab$Tubo==21,i], pch=2, col="blue", lty=2)
   lines(divinertab$Fecha[divinertab$Tubo==22], divinertab[divinertab$Tubo==22,i], pch=3, col="green")
   lines(divinertab$Fecha[divinertab$Tubo==23], divinertab[divinertab$Tubo==23,i], pch=4, col="cyan", lty=2)
   legend("topleft", legend=c("LIS, goteo", "PARC, goteo", "LIS, interf", "PARC, interf"), col=c("dark green", "green", "blue","cyan"), lty=c(1,1,2,2), box.lty=0, cex=0.8, inset=0.01)
   axis(side = 4)
   mtext(side = 4, line = 3, "y")
  })
  
})