from fastapi import FastAPI
from app.neo4j import DB as db
from app.api.endpoints import similarityFuncs

app=FastAPI(title='E-Rex')

app.include_router(similarityFuncs.router)

def on_shutdown():
    # Perform cleanup or resource management here
    db.close()
    print("Neo4j Driver closed...")   #LOG

# Register the shutdown event handler
app.add_event_handler("shutdown", on_shutdown)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)