# Playwright Test Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Test script
COPY test_exam_playwright.py .

# Environment variables (override edilecek)
ENV SURVEY_TOKEN=""
ENV BASE_URL="https://digipharma.com.tr"
ENV USER_COUNT="1"
ENV PARALLEL="1"
ENV HEADLESS="true"

# Run test
CMD ["python", "test_exam_playwright.py"]
