name := "stream-processor"
version := "1.0.0"
scalaVersion := "2.13.12"

libraryDependencies ++= Seq(
  "org.apache.flink" %% "flink-streaming-scala" % "1.18.0",
  "org.apache.flink" %% "flink-connector-kafka" % "3.0.1-1.18",
  "org.apache.flink" %% "flink-connector-elasticsearch" % "3.0.1-1.18",
  "org.apache.flink" %% "flink-connector-redis" % "1.1.0",
  "org.apache.flink" %% "flink-clients" % "1.18.0"
)

assemblyMergeStrategy in assembly := {
  case PathList("META-INF", xs @ _*) => MergeStrategy.discard
  case x => MergeStrategy.first
}

