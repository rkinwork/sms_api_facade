from dataclasses import dataclass

from cli import DEFAULT_SMS_TTL, ENV_PREFIX, SmscApiError, request_smsc
from pydantic import BaseModel, BaseSettings, Field, FilePath, SecretStr
from quart import render_template, websocket
from quart_schema import (DataSource, QuartSchema,
                          RequestSchemaValidationError, validate_request,
                          validate_response)
from quart_trio import QuartTrio

app = QuartTrio(__name__)
QuartSchema(app, convert_casing=True)


class Settings(BaseSettings):
    login: str
    password: SecretStr
    numbers: FilePath
    ttl: str = Field(default=DEFAULT_SMS_TTL, regex=r'\d\d:\d{2}')

    class Config:
        env_prefix = '{0}_'.format(ENV_PREFIX)
        case_sensitive = False


@dataclass
class DistributionIn:
    text: str


class DistributionRes(BaseModel):
    status: str  # todo add enum for status
    error_message: str | None = Field(None, alias='errorMessage')

    class Config:  # noqa
        allow_population_by_field_name = True


@app.errorhandler(RequestSchemaValidationError)
async def handle_response_validation_error():
    return DistributionRes(
        status='failed',
        error_message='form validation error',
    ), 400


@app.get('/')
async def index():
    return await render_template('index.html')


@app.post('/send/')
@validate_request(DistributionIn, source=DataSource.FORM)
@validate_response(DistributionRes, 201)
@validate_response(DistributionRes, 200)
async def get_message(data: DistributionIn):
    sms_setting: Settings = app.config.get('SMS_SETTINGS')
    phones = [el.strip() for el in sms_setting.numbers.read_text().split('\n')]
    phones = ';'.join(phones)
    try:
        await request_smsc(
            'GET',
            'send.php',
            login=sms_setting.login,
            password=sms_setting.password.get_secret_value(),
            payload={
                'phones': phones,
                'message': '\n'.join(data.text),
                'valid': sms_setting.ttl,
            },
        )
    except SmscApiError:
        return DistributionRes(
            status='failed',
            error_message='Problems with provider api',
        ), 200
    return DistributionRes(status='ok'), 201


@app.websocket('/ws')
async def ws():
    while True:
        message = await websocket.receive()


def run():
    app.config['SMS_SETTINGS'] = Settings()
    app.run(host='0.0.0.0', port=6000)


if __name__ == '__main__':
    run()
