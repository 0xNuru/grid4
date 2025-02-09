from fastapi import FastAPI, HTTPException
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Grid4 API")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/nga-datasets")
async def get_nga_datasets():
    url = (
        "https://hub.arcgis.com/api/search/v1/collections/all/items"
        "?filter=((group%20IN%20(6be3552af25e468782d371f3cc867087%2C%20"
        "2ceb253ed4794a8e85d6984ab4dfd394%2C%20e56cdce5fe30429b90a8333b19fa84a7%2C%20"
        "7a1d4174907d48cf9c4f30d49ebd7e89)))%20AND%20((tags%20IN%20(NGA)))&limit=50"
    )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            dataset_summaries = [
                {
                    "name": feature.get("properties", {}).get("name"),
                    "title": feature.get("properties", {}).get("title", "No title"),
                    "snippet": feature.get("properties", {}).get(
                        "snippet", "No description available"
                    ),
                    "tags": feature.get("properties", {}).get("tags", []),
                    "created": datetime.fromtimestamp(
                        feature.get("properties", {}).get("created", 0) / 1000
                    ).isoformat(),
                    "source": feature.get("properties", {}).get(
                        "source", "Unknown source"
                    ),
                }
                for feature in data.get("features", [])
                if (
                    feature.get("properties", {}).get("type") != "Web Map"
                    and feature.get("properties", {}).get("name") is not None
                )
            ]

            return {
                "timestamp": data.get("timestamp"),
                "total_datasets": len(dataset_summaries),
                "datasets": dataset_summaries,
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise HTTPException(
            status_code=503, detail="Error fetching data from ArcGIS Hub"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
