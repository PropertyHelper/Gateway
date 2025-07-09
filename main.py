import uvicorn
from src.app import build_app

if __name__ == '__main__':
    app = build_app()

    uvicorn.run(app, port=8002, host="0.0.0.0")
