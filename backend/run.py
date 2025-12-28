import uvicorn

uvicorn.run("app.main:app", reload=True)

# uvicorn app.main:app --reload