<?php
include("phpgraphlib.php");
$graph=new PHPGraphLib(1500,500);
//GFO $link = mysql_connect('localhost', 'guillermo', 'midraed561234')
//GFO  or die('Could not connect: ' . mysql_error());

//GFO mysql_select_db('LISIMETRO') or die('Could not select database');

$dataArray=array();

//GFO $sql="SELECT * FROM 'prueba'";
//GFO $result = mysql_query($sql) or die('Query failed: ' . mysql_error());

$host="localhost"; // Host name
$username="guillermo"; // Mysql username
$password="midraed561234"; // Mysql password
$db_name="LISIMETRO"; // Database name
$tbl_name="prueba"; // Table name

// Connect to server and select database.
mysql_connect("$host", "$username", "$password")or die("cannot connect");
mysql_select_db("$db_name")or die("cannot select DB");

// Retrieve data from database
$sql="SELECT * FROM $tbl_name WHERE MOD(ID,10)=0 ORDER BY Fecha DESC LIMIT 100";
$result=mysql_query($sql);

if ($result) {
  while ($row = mysql_fetch_assoc($result)) {
      $Fecha=$row["Fecha"];
      $TEMP1_50=$row["TEMP1_50"];
      $TEMP2_100=$row["TEMP2_100"];
      $TEMP3_150=$row["TEMP3_150"];
      $SENS4=$row["SENS4"];
      $SENS5=$row["SENS5"];
      $SENS6=$row["SENS6"];
      //add to data areray
      $dataArray1[$Fecha]=$TEMP1_50;
      $dataArray2[$Fecha]=$TEMP2_100;
      $dataArray3[$Fecha]=$TEMP3_150;
      $dataArray4[$Fecha]=$SENS4;
      $dataArray5[$Fecha]=$SENS5;
      $dataArray6[$Fecha]=$SENS6;
        }
}
//configure graph
$graph->addData($dataArray2,$dataArray3,$dataArray4,$dataArray5,$dataArray6);
//$graph->addData($dataArray4,$dataArray5,$dataArray6);
$graph->setTitle('Valores RAW de sensores');
$graph->setRange(max($dataArray2)*1.01,380);
//$graph->setRange(625,600);
$graph->setBars(false);
$graph->setLine(true);
$graph->setLineColor('green', 'red', 'blue');
$graph->setDataPoints(true);
$graph->setDataPointSize(2);
$graph->setLegend(true);
$graph->setLegendTitle("TEMP2", "TEMP3", "SENS4", "SENS5", "SENS6");
//$graph->setDataPointColor('blue', 'blue', 'green');
//$graph->setDataValues(true);
//$graph->setDataValueColor('maroon');
//$graph->setGoalLine(600);
//$graph->setGoalLineColor('red');
$graph->createGraph();
?>

