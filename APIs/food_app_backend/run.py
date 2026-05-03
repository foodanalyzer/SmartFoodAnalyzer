import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   # file path: app/main.py → the `app` variable inside it
        host="0.0.0.0",   # listen on all network interfaces
        port=8000,
        reload=True       # auto-restart when you save any file (dev only)
    )
