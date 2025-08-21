import os
import tempfile
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Import your existing Agent class from agent.py
from agent import Agent

app = FastAPI(
    title="License Generator API",
    description="Upload a research paper summary JSON to generate license templates."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/generate-licenses/", status_code=200)
async def create_licenses(file: UploadFile = File(...)):
    """
    Accepts a JSON file, processes it with the Agent, 
    and returns a list of generated license templates.
    """
    # Ensure the uploaded file is a JSON file
    if file.content_type != "application/json":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a JSON file.")

    temp_file_path = None
    try:
        # Create a temporary file to store the upload
        # 'delete=False' is needed to use the file path after closing it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="wb") as temp_f:
            contents = await file.read()
            temp_f.write(contents)
            temp_file_path = temp_f.name

        # Instantiate the Agent with the path of the temporary file
        agent = Agent(file_path=temp_file_path)
        
        # Call the solve method to get the licenses
        licenses = agent.solve()
        
        if licenses is None:
             raise HTTPException(status_code=500, detail="Agent failed to generate licenses. Check server logs.")

        return licenses

    except Exception as e:
        # Catch any other errors during processing
        raise HTTPException(status_code=500, detail=f"An internal error occurred: {str(e)}")
    
    finally:
        # IMPORTANT: Clean up and delete the temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
