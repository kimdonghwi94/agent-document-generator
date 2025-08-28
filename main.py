from src.agent_document_generator.__main__ import create_app

app = create_app()
if __name__ == '__main__':
    import uvicorn
    from src.agent_document_generator.__main__ import create_app
    uvicorn.run(
       create_app(),
       host="0.0.0.0",
       port=8000,
       reload=True
   )