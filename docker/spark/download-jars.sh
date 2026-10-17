#!/usr/bin/env bash
set -euo pipefail
JARS="/opt/spark/jars"
MAVEN="https://repo.maven.apache.org/maven2"
get() {
  local url="$1" filename="$2"
  test -s "${JARS}/${filename}" && { echo "already present: ${filename}"; return 0; }
  curl -fSL --retry 3 --retry-all-errors -o "${JARS}/${filename}.tmp" "$url"
  mv "${JARS}/${filename}.tmp" "${JARS}/${filename}"
}
get "${MAVEN}/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar" hadoop-aws-3.3.4.jar
get "${MAVEN}/com/amazonaws/aws-java-sdk-bundle/1.12.517/aws-java-sdk-bundle-1.12.517.jar" aws-java-sdk-bundle-1.12.517.jar
get "${MAVEN}/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.6.1/iceberg-spark-runtime-3.5_2.12-1.6.1.jar" iceberg-spark-runtime-3.5_2.12-1.6.1.jar
get "${MAVEN}/software/amazon/awssdk/bundle/2.25.48/bundle-2.25.48.jar" bundle-2.25.48.jar
get "${MAVEN}/software/amazon/awssdk/url-connection-client/2.25.48/url-connection-client-2.25.48.jar" url-connection-client-2.25.48.jar
