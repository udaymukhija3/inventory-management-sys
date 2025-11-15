package com.inventory.stream

import org.apache.flink.streaming.api.scala._
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment
import org.apache.flink.streaming.connectors.kafka.FlinkKafkaConsumer
import org.apache.flink.api.common.serialization.SimpleStringSchema
import java.util.Properties

object InventoryStreamProcessor {
  def main(args: Array[String]): Unit = {
    val env = StreamExecutionEnvironment.getExecutionEnvironment
    
    val properties = new Properties()
    properties.setProperty("bootstrap.servers", "localhost:9092")
    properties.setProperty("group.id", "inventory-stream-processor")
    
    val kafkaConsumer = new FlinkKafkaConsumer[String](
      "inventory-events",
      new SimpleStringSchema(),
      properties
    )
    
    val stream = env.addSource(kafkaConsumer)
    
    // Process stream
    stream.print()
    
    env.execute("Inventory Stream Processor")
  }
}

