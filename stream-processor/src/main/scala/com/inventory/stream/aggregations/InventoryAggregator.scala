package com.inventory.stream.aggregations

import org.apache.flink.streaming.api.scala._
import org.apache.flink.streaming.api.windowing.time.Time

case class InventoryEvent(sku: String, warehouse: String, quantityChange: Int, timestamp: Long)

class InventoryAggregator {
  def aggregateByWindow(stream: DataStream[InventoryEvent], windowSize: Time): DataStream[(String, Int)] = {
    stream
      .keyBy(event => event.sku + "_" + event.warehouse)
      .timeWindow(windowSize)
      .sum("quantityChange")
  }
}

