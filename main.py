import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agent.graph import build_graph
from utils import vectorstore

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

app = FastAPI()

# Ensure static dir exists
os.makedirs("static", exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

@app.websocket("/ws/analyze")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    if not GEMINI_API_KEY:
        await websocket.send_json({"type": "error", "message": "No API key found in server."})
        await websocket.close()
        return

    graph = build_graph()

    try:
        data = await websocket.receive_text()
        request_data = json.loads(data)
        repo_url = request_data.get("repo_url")
        
        if not repo_url:
            await websocket.send_json({"type": "error", "message": "Empty repo URL"})
            await websocket.close()
            return
            
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        
        initial_state = {
            "repo_url": repo_url,
            "repo_name": repo_name,
            "api_key": GEMINI_API_KEY
        }
        
        # Async stream over the graph
        # Wait, LangGraph is sync by default unless we use astream
        # Since our nodes are sync, we can use astream with threadpool automatically
        final_state = {}
        async for output in graph.astream(initial_state):
            # output is a dict like {"node_name": {"state_key": "val"}}
            for node_name, updates in output.items():
                if updates.get('error'):
                    await websocket.send_json({"type": "error", "message": updates['error']})
                    await websocket.close()
                    return
                    
                await websocket.send_json({
                    "type": "progress", 
                    "node": node_name,
                    "message": f"Completed {node_name}"
                })
                # Keep accumulating state
                final_state.update(updates)

        # Build Vector Store
        await websocket.send_json({"type": "progress", "node": "vectorstore", "message": "Indexing vectorstore..."})
        try:
            # this is a sync function so we might want to run in executor, but for demo it's ok
            await asyncio.to_thread(
                vectorstore.initialize_vector_store,
                final_state['repo_path'], repo_name, GEMINI_API_KEY
            )
        except Exception as e:
            print("Vectorstore error:", e)
            
        await websocket.send_json({"type": "complete", "state": final_state})
        await websocket.close()
        
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
        import traceback
        traceback.print_exc()

class SearchRequest(BaseModel):
    repo_name: str
    query: str

@app.post("/api/search")
def search_api(request: SearchRequest):
    results = vectorstore.search_codebase(
        request.repo_name,
        request.query,
        GEMINI_API_KEY
    )
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
