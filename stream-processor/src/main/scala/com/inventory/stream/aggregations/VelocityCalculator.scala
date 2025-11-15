package com.inventory.stream.aggregations

import org.apache.flink.streaming.api.scala._

case class VelocityMetrics(sku: String, warehouse: String, velocity: Double, period: Int)

class VelocityCalculator {
  def calculateVelocity(stream: DataStream[InventoryEvent], periodMinutes: Int): DataStream[VelocityMetrics] = {
    stream
      .keyBy(event => event.sku + "_" + event.warehouse)
      .timeWindow(org.apache.flink.streaming.api.windowing.time.Time.minutes(periodMinutes))
      .apply((key, window, events, out: Collector[VelocityMetrics]) => {
        val totalQuantity = events.map(_.quantityChange).sum
        val velocity = totalQuantity.toDouble / periodMinutes
        out.collect(VelocityMetrics(key.split("_")(0), key.split("_")(1), velocity, periodMinutes))
      })
  }
}

