from aiohttp import web as webserver
from datetime import datetime
import pytz  # Ensure this is installed: pip install pytz

routes = webserver.RouteTableDef()

async def bot_run():
    _app = webserver.Application(client_max_size=30000000)
    _app.add_routes(routes)
    return _app

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    india_tz = pytz.timezone('Asia/Kolkata')
    india_time = datetime.now(india_tz).strftime('%A, %Y-%m-%d %I:%M:%S %p')

    return webserver.json_response({
        "message": "og eva. . .! ! !",
        "india_time": india_time
    })

# Run the server on port 8080
#if __name__ == "__main__":
#    webserver.run_app(bot_run(), port=8080)
