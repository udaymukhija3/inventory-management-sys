FROM flink:1.18.0-scala_2.13

COPY target/scala-2.13/stream-processor-assembly-1.0.0.jar /opt/flink/lib/

CMD ["/opt/flink/bin/start-cluster.sh"]

