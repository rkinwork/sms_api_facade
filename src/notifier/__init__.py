from quart_trio import QuartTrio
from quart import render_template, websocket, request

app = QuartTrio(__name__)


@app.get('/')
async def index():
    return await render_template('index.html')


@app.post('/send/')
async def get_message():
    form = await request.form
    print(form)
    return {'status': 'ok'}


@app.websocket('/ws')
async def ws():
    while True:
        message = await websocket.receive()
        print(message)


def run():
    app.run(host='0.0.0.0', port=6000)


if __name__ == '__main__':
    run()
