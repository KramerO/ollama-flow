#!/usr/bin/env python3
import os

def system_components():
    print("System Components:")
    print("  * Sensor Data Collector Service (SDKS):")
        "    - Collects sensor data from IoT devices"
        "    - Stores data in S3 bucket"
    print("  * Data Processing Microservice (DPM):")
        "    - Processes sensor data using machine learning algorithms"
        "    - Stores processed data in DynamoDB table"
    print("  * Storage Service (S3, DynamoDB):")
        "    - Provides persistent storage for raw and processed data"
    print("  * Analytics Microservice (AM):")
        "    - Analyzes processed data to generate insights and visualizations"

if __name__ == "__main__":
    system_components()
