FROM maven:3.9-eclipse-temurin-26 AS build
WORKDIR /workspace
COPY pom.xml .
COPY src ./src
RUN mvn --batch-mode --no-transfer-progress verify

FROM eclipse-temurin:17-jre-jammy
WORKDIR /app
COPY --from=build --chown=10001:10001 /workspace/target/app.jar /app/app.jar
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75.0", "-jar", "/app/app.jar"]
