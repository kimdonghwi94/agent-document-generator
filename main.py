import asyncio
from src.__main__ import create_app

# Create app synchronously for import
# app = asyncio.new_event_loop().run_until_complete(create_app())
app = create_app()

if __name__ == '__main__':
    import uvicorn
    
    # Create new app instance for running
    async def get_app():
        return await create_app()
    
    app_instance = asyncio.run(get_app())
    
    uvicorn.run(
       app_instance,
       host="0.0.0.0",
       port=8004,
       reload=False
   )