package com.inventory.stream.sinks

import org.apache.flink.streaming.api.scala._

class RedisSink {
  def writeToRedis(stream: DataStream[String]): Unit = {
    // TODO: Implement Redis sink
  }
}

