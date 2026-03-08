ARG DOCKER_MIRROR=docker.m.daocloud.io

# Stage 1: Build
FROM ${DOCKER_MIRROR}/library/maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app

# Configure Maven to use Aliyun mirror for faster downloads in China
RUN mkdir -p /root/.m2 && echo '<?xml version="1.0" encoding="UTF-8"?>\
<settings><mirrors><mirror>\
<id>aliyun</id><mirrorOf>*</mirrorOf>\
<url>https://maven.aliyun.com/repository/public</url>\
</mirror></mirrors></settings>' > /root/.m2/settings.xml

COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests -B

# Stage 2: Run
FROM ${DOCKER_MIRROR}/library/eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
