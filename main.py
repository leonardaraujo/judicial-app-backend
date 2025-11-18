from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from controllers.document_controller import router as documento_router
from controllers.document_crud_controller import router as crud_router
from controllers.search_controller import router as search_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://judicial-app-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def ping():
    return {"message": "pong"}


app.include_router(documento_router)
app.include_router(crud_router)
app.include_router(search_router)
