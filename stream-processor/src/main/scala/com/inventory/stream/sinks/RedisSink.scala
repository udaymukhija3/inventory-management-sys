package com.inventory.stream.sinks

import org.apache.flink.streaming.api.scala._
import org.apache.flink.streaming.api.functions.sink.{RichSinkFunction, SinkFunction}
import org.apache.flink.configuration.Configuration
import redis.clients.jedis.{Jedis, JedisPool, JedisPoolConfig}
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule

import scala.util.{Try, Success, Failure}

/**
 * Redis sink for real-time inventory data caching.
 * Stores current inventory levels for fast access by the API.
 */
class RedisSink(
    redisHost: String = sys.env.getOrElse("REDIS_HOST", "redis"),
    redisPort: Int = sys.env.getOrElse("REDIS_PORT", "6379").toInt,
    redisPassword: Option[String] = sys.env.get("REDIS_PASSWORD").filter(_.nonEmpty),
    ttlSeconds: Int = 3600 // 1 hour default TTL
) {

  private val objectMapper = {
    val mapper = new ObjectMapper()
    mapper.registerModule(DefaultScalaModule)
    mapper
  }

  /**
   * Creates a Flink sink function that writes to Redis.
   */
  def createSinkFunction(): RichSinkFunction[String] = {
    new InventoryRedisSinkFunction(redisHost, redisPort, redisPassword, ttlSeconds)
  }

  /**
   * Writes a DataStream to Redis.
   */
  def writeToRedis(stream: DataStream[String]): Unit = {
    stream.addSink(createSinkFunction())
  }
}

/**
 * Rich sink function with Redis connection lifecycle management.
 */
class InventoryRedisSinkFunction(
    redisHost: String,
    redisPort: Int,
    redisPassword: Option[String],
    ttlSeconds: Int
) extends RichSinkFunction[String] {

  @transient private var jedisPool: JedisPool = _
  @transient private var objectMapper: ObjectMapper = _

  override def open(parameters: Configuration): Unit = {
    super.open(parameters)
    
    // Initialize object mapper
    objectMapper = new ObjectMapper()
    objectMapper.registerModule(DefaultScalaModule)
    
    // Configure connection pool
    val poolConfig = new JedisPoolConfig()
    poolConfig.setMaxTotal(10)
    poolConfig.setMaxIdle(5)
    poolConfig.setMinIdle(1)
    poolConfig.setTestOnBorrow(true)
    poolConfig.setTestWhileIdle(true)
    
    // Create pool with or without password
    jedisPool = redisPassword match {
      case Some(password) => new JedisPool(poolConfig, redisHost, redisPort, 2000, password)
      case None => new JedisPool(poolConfig, redisHost, redisPort)
    }
  }

  override def invoke(value: String, context: SinkFunction.Context): Unit = {
    var jedis: Jedis = null
    try {
      jedis = jedisPool.getResource
      
      // Parse the event
      val eventMap = objectMapper.readValue(value, classOf[java.util.Map[String, Any]])
      
      val eventType = Option(eventMap.get("eventType")).map(_.toString).getOrElse("")
      val sku = Option(eventMap.get("sku")).map(_.toString).getOrElse("")
      val warehouseId = Option(eventMap.get("warehouseId")).map(_.toString).getOrElse("")
      
      if (sku.nonEmpty && warehouseId.nonEmpty) {
        // Update inventory cache
        val cacheKey = s"inventory:$sku:$warehouseId"
        
        eventType match {
          case "INVENTORY_UPDATED" | "RESTOCKED" =>
            // Store full inventory state
            jedis.setex(cacheKey, ttlSeconds, value)
            
            // Update quantity in a separate key for fast reads
            Option(eventMap.get("quantity")).foreach { qty =>
              jedis.setex(s"inventory:qty:$sku:$warehouseId", ttlSeconds, qty.toString)
            }
            
          case "RESERVED" =>
            // Increment reserved count in Redis
            val reservedKey = s"inventory:reserved:$sku:$warehouseId"
            Option(eventMap.get("quantity")).foreach { qty =>
              jedis.incrBy(reservedKey, Math.abs(qty.toString.toLong))
              jedis.expire(reservedKey, ttlSeconds)
            }
            
          case "RELEASED" =>
            // Decrement reserved count
            val reservedKey = s"inventory:reserved:$sku:$warehouseId"
            Option(eventMap.get("quantity")).foreach { qty =>
              jedis.decrBy(reservedKey, Math.abs(qty.toString.toLong))
            }
            
          case "LOW_STOCK_ALERT" =>
            // Add to low stock set
            jedis.sadd("inventory:low_stock", s"$sku:$warehouseId")
            jedis.setex(s"inventory:alert:$sku:$warehouseId", ttlSeconds * 24, value)
            
          case _ =>
            // Store as generic event
            jedis.setex(cacheKey, ttlSeconds, value)
        }
        
        // Publish to Redis pub/sub for real-time updates
        jedis.publish("inventory:updates", value)
      }
    } catch {
      case e: Exception =>
        System.err.println(s"Failed to write to Redis: ${e.getMessage}")
    } finally {
      if (jedis != null) {
        jedis.close()
      }
    }
  }

  override def close(): Unit = {
    if (jedisPool != null) {
      jedisPool.close()
    }
    super.close()
  }
}

/**
 * Companion object with factory methods.
 */
object RedisSink {
  def apply(): RedisSink = new RedisSink()
  
  def apply(host: String, port: Int): RedisSink = 
    new RedisSink(host, port)
    
  def apply(host: String, port: Int, password: String): RedisSink =
    new RedisSink(host, port, Some(password))
}
