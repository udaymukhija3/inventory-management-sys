package com.inventory.stream.sinks

import org.apache.flink.api.common.functions.RuntimeContext
import org.apache.flink.streaming.connectors.elasticsearch.{ElasticsearchSinkFunction, RequestIndexer}
import org.apache.flink.streaming.connectors.elasticsearch7.{ElasticsearchSink => ES7Sink}
import org.apache.http.HttpHost
import org.elasticsearch.action.index.IndexRequest
import org.elasticsearch.client.Requests
import org.elasticsearch.common.xcontent.XContentType
import com.fasterxml.jackson.databind.ObjectMapper
import com.fasterxml.jackson.module.scala.DefaultScalaModule

import java.util
import scala.collection.JavaConverters._

/**
 * Elasticsearch sink for inventory events.
 * Indexes inventory transactions and analytics data for search and reporting.
 */
class ElasticsearchSink(
    elasticsearchHost: String = sys.env.getOrElse("ELASTICSEARCH_HOST", "elasticsearch"),
    elasticsearchPort: Int = sys.env.getOrElse("ELASTICSEARCH_PORT", "9200").toInt
) {

  private val objectMapper = {
    val mapper = new ObjectMapper()
    mapper.registerModule(DefaultScalaModule)
    mapper
  }

  /**
   * Creates an Elasticsearch sink function for inventory events.
   * Events are indexed to the 'inventory-events' index.
   */
  def createSink(): ElasticsearchSinkFunction[String] = {
    new ElasticsearchSinkFunction[String] {
      override def process(
          element: String,
          ctx: RuntimeContext,
          indexer: RequestIndexer
      ): Unit = {
        try {
          // Parse the incoming JSON event
          val eventMap = objectMapper.readValue(element, classOf[java.util.Map[String, Any]])
          
          // Add timestamp if not present
          if (!eventMap.containsKey("indexedAt")) {
            eventMap.put("indexedAt", System.currentTimeMillis())
          }
          
          // Determine index name based on event type
          val eventType = Option(eventMap.get("eventType")).map(_.toString).getOrElse("unknown")
          val indexName = eventType.toLowerCase match {
            case "inventory_updated" => "inventory-updates"
            case "reserved" | "released" => "inventory-reservations"
            case "restocked" => "inventory-restocks"
            case "low_stock_alert" => "inventory-alerts"
            case _ => "inventory-events"
          }
          
          // Create index request
          val request: IndexRequest = Requests.indexRequest()
            .index(indexName)
            .source(objectMapper.writeValueAsString(eventMap), XContentType.JSON)
          
          // Add to indexer
          indexer.add(request)
        } catch {
          case e: Exception =>
            System.err.println(s"Failed to index event: ${e.getMessage}")
        }
      }
    }
  }

  /**
   * Builds the complete Elasticsearch sink with connection configuration.
   */
  def buildSink(): ES7Sink[String] = {
    val httpHosts = new util.ArrayList[HttpHost]()
    httpHosts.add(new HttpHost(elasticsearchHost, elasticsearchPort, "http"))
    
    val sinkBuilder = new ES7Sink.Builder[String](
      httpHosts,
      createSink()
    )
    
    // Configure bulk flush settings
    sinkBuilder.setBulkFlushMaxActions(100)
    sinkBuilder.setBulkFlushInterval(5000) // 5 seconds
    sinkBuilder.setBulkFlushMaxSizeMb(5)
    
    // Configure failure handler
    sinkBuilder.setFailureHandler((failure, context, indexRequest) => {
      System.err.println(s"Elasticsearch indexing failed: ${failure.getMessage}")
    })
    
    sinkBuilder.build()
  }
}

/**
 * Companion object with factory methods.
 */
object ElasticsearchSink {
  def apply(): ElasticsearchSink = new ElasticsearchSink()
  
  def apply(host: String, port: Int): ElasticsearchSink = 
    new ElasticsearchSink(host, port)
}
