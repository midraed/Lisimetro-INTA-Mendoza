<?php
include("phpgraphlib.php");
$graph=new PHPGraphLib(1500,500);
//GFO $link = mysql_connect('localhost', 'guillermo', '****')
//GFO  or die('Could not connect: ' . mysql_error());

//GFO mysql_select_db('LISIMETRO') or die('Could not select database');

$dataArray=array();

//GFO $sql="SELECT * FROM 'prueba2'";
//GFO $result = mysql_query($sql) or die('Query failed: ' . mysql_error());

$host="localhost"; // Host name
$username="guillermo"; // Mysql username
$password="********"; // Mysql password
$db_name="LISIMETRO"; // Database name
$tbl_name="prueba2"; // Table name

// Connect to server and select database.
mysql_connect("$host", "$username", "$password")or die("cannot connect");
mysql_select_db("$db_name")or die("cannot select DB");

// Retrieve data from database
$sql="SELECT * FROM $tbl_name WHERE MOD(ID,1)=0 ORDER BY Fecha ASC LIMIT 100";
$result=mysql_query($sql);

if ($result) {
  while ($row = mysql_fetch_assoc($result)) {
      $Fecha=$row["Fecha"];
      $PESO=$row["Peso"];
      //add to data areray
      $dataArray1[$Fecha]=$PESO;
  }
}
//configure graph
$graph->addData($dataArray1);
//$graph->addData($dataArray4,$dataArray5,$dataArray6);
$graph->setTitle('Valores de Peso');
//graph->setRange(max($dataArray2)*1.01,380);
//$graph->setRange(1030,500);
$graph->setBars(false);
$graph->setLine(true);
$graph->setLineColor('green', 'red', 'blue');
$graph->setDataPoints(true);
$graph->setDataPointSize(2);
$graph->setLegend(true);
$graph->setLegendTitle("Peso");
//$graph->setDataPointColor('blue', 'blue', 'green');
//$graph->setDataValues(true);
//$graph->setDataValueColor('maroon');
//$graph->setGoalLine(600);
//$graph->setGoalLineColor('red');
$graph->createGraph();
?>
