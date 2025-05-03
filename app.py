import uvicorn
import yaml
import logging
import logging.config
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# Load configuration
try:
    with open("config/config.yaml", "r") as f:
        config = yaml.safe_load(f)
except Exception as e:
    print(f"Error loading config: {str(e)}")
    config = {
        "app": {
            "name": "MCP Document Processor",
            "version": "0.1.0",
            "log_level": "INFO"
        },
        "models": {
            "document_classifier": {
                "model_name": "bert-base-uncased",
                "threshold": 0.75
            },
            "entity_extractor": {
                "model_name": "bert-base-uncased",
                "confidence_threshold": 0.65
            },
            "summarizer": {
                "model_name": "t5-small",
                "max_length": 150
            }
        },
        "mcp": {
            "memory": {
                "type": "in_memory",
                "ttl": 3600
            },
            "context": {
                "max_size": 10000,
                "compression": True
            }
        }
    }

# Configure logging
try:
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)
    
    with open("config/logging_config.yaml", "r") as f:
        logging_config = yaml.safe_load(f)
        if logging_config:
            logging.config.dictConfig(logging_config)
        else:
            # Default logging configuration if file is empty
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.StreamHandler(),
                    logging.FileHandler("logs/app.log")
                ]
            )
except Exception as e:
    print(f"Error configuring logging: {str(e)}")
    # Set up basic logging if configuration fails
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )

# Create the FastAPI app
app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    description="Intelligent document processing using Model Context Protocol (MCP)"
)

# Add CORS middleware
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": config["app"]["name"],
        "version": config["app"]["version"],
        "status": "operational"
    }

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)