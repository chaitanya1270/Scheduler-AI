import uvicorn

if __name__ == "__main__":
    # Running the FastAPI app on host 0.0.0.0 (accessible from outside localhost) on port 8000
    uvicorn.run("app.server:app", host="0.0.0.0", port=8000, reload=True)
