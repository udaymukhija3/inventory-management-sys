package com.inventory.stream.anomaly

import org.apache.flink.streaming.api.scala._

class AlertGenerator {
  def generateAlerts(anomalies: DataStream[InventoryAnomaly]): DataStream[String] = {
    anomalies
      .filter(_.severity == "CRITICAL")
      .map(anomaly => 
        s"ALERT: ${anomaly.anomalyType} detected for SKU ${anomaly.sku} at ${anomaly.warehouseId}"
      )
  }
}

