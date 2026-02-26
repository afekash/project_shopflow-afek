import fastapi

app = fastapi.FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

if __name__ == "__main__":
    fastapi.run(app)