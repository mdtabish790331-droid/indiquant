from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import participant_router, admin_router, internal_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IndiQuant Auth Service",
    description="""
## IndiQuant Authentication Service

### Participant Portal
- **Register:** `POST /api/participant/register` — koi bhi register kar sakta hai
- **Login:** `POST /api/participant/login` — sirf participant login kar sakta hai

### Admin Portal  
- **Register:** `POST /api/admin/register?admin_key=SECRET` — secret key chahiye
- **Login:** `POST /api/admin/login` — sirf admin login kar sakta hai
- **Users:** `GET /api/admin/users` — sabke users dekho
- **Delete User:** `DELETE /api/admin/users/{id}` — user delete karo
- **Block User:** `PATCH /api/admin/users/{id}/deactivate` — user block karo
    """,
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers register karo
app.include_router(participant_router)
app.include_router(admin_router)
app.include_router(internal_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "IndiQuant Auth Service",
        "version": "2.0.0",
        "status": "running",
        "portals": {
            "participant": {
                "register": "POST /api/participant/register",
                "login": "POST /api/participant/login",
            },
            "admin": {
                "register": "POST /api/admin/register?admin_key=REQUIRED",
                "login": "POST /api/admin/login",
                "users": "GET /api/admin/users",
            }
        }
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)