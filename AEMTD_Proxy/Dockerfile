# Use a base image with Java installed
FROM openjdk:8-jre-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the compiled JAR file from your target directory into the container
COPY target/aemtd-proxy-1.0-SNAPSHOT-jar-with-dependencies.jar AEMTDProxy.jar

# Command to run when the container starts
CMD ["java", "-jar", "AEMTDProxy.jar"]