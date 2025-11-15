package com.inventory.stream.anomaly

import org.apache.flink.streaming.api.scala._
import org.apache.flink.api.common.state.ValueState
import org.apache.flink.api.common.state.ValueStateDescriptor
import org.apache.flink.configuration.Configuration
import org.apache.flink.streaming.api.functions.KeyedProcessFunction
import org.apache.flink.util.Collector

case class InventoryAnomaly(
  sku: String,
  warehouseId: String,
  anomalyType: String,
  severity: String,
  currentValue: Double,
  expectedValue: Double,
  deviation: Double,
  timestamp: Long,
  message: String
)

case class MovingAverageState(values: List[Double], mean: Double, stdDev: Double)

class AnomalyDetector extends KeyedProcessFunction[String, InventoryEvent, InventoryAnomaly] {
  
  private var movingAverage: ValueState[MovingAverageState] = _
  
  override def open(parameters: Configuration): Unit = {
    movingAverage = getRuntimeContext.getState(
      new ValueStateDescriptor[MovingAverageState](
        "moving-average",
        classOf[MovingAverageState]
      )
    )
  }
  
  override def processElement(
    event: InventoryEvent,
    ctx: KeyedProcessFunction[String, InventoryEvent, InventoryAnomaly]#Context,
    out: Collector[InventoryAnomaly]
  ): Unit = {
    val currentState = Option(movingAverage.value()).getOrElse(
      MovingAverageState(List.empty, 0.0, 0.0)
    )
    
    // Update moving average
    val updatedValues = (currentState.values :+ event.quantityChange.toDouble).takeRight(100)
    val updatedMean = updatedValues.sum / updatedValues.length
    val updatedStdDev = math.sqrt(
      updatedValues.map(v => math.pow(v - updatedMean, 2)).sum / updatedValues.length
    )
    
    movingAverage.update(MovingAverageState(updatedValues, updatedMean, updatedStdDev))
    
    // Detect anomalies
    detectVolumeAnomaly(event, updatedMean, updatedStdDev, out)
  }
  
  private def detectVolumeAnomaly(
    event: InventoryEvent,
    mean: Double,
    stdDev: Double,
    out: Collector[InventoryAnomaly]
  ): Unit = {
    val threshold = 3.0
    val zScore = if (stdDev > 0) {
      math.abs(event.quantityChange - mean) / stdDev
    } else 0.0
    
    if (zScore > threshold) {
      out.collect(InventoryAnomaly(
        sku = event.sku,
        warehouseId = event.warehouse,
        anomalyType = "VOLUME_ANOMALY",
        severity = if (zScore > 5) "CRITICAL" else "HIGH",
        currentValue = event.quantityChange,
        expectedValue = mean,
        deviation = zScore,
        timestamp = event.timestamp,
        message = s"Unusual inventory change detected: ${event.quantityChange}"
      ))
    }
  }
}

