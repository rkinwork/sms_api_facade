import http

import asyncclick as click
import asks
import trio

DEFAULT_SMS_TTL = '01:00'
ENV_PREFIX = 'DVMN_SMS'
SMSC_HOST = 'https://smsc.ru/sys/'
ALLOWED_API_METHODS = (
    'send.php',
    'status.php',
)

ALLOWED_METHODS = (
    http.HTTPMethod.POST.value,
    http.HTTPMethod.GET.value,
)


class SmscApiError(Exception):
    """Common error for smsc problems."""




@click.command()
@click.argument('numbers_src', type=click.File('r'))
@click.option('sms_text', '-m', required=True, multiple=True)
@click.option('--login', prompt='SMSC login', help='SMSC login')
@click.option(
    '--password',
    prompt=True,
    hide_input=True,
    help='SMSC password',
)
@click.option('--ttl', default=DEFAULT_SMS_TTL)
async def send(
        numbers_src,
        sms_text,
        login,
        password,
        ttl,
):
    api_method = 'send.php'
    response = await request_smsc(
        http_method='GET',
        api_method=api_method,
        login=login,
        password=password,
        payload={
            'phones': ';'.join(phone.strip() for phone in numbers_src),
            'message': '\n'.join(sms_text),
            'valid': ttl,
        },
    )
    click.echo(response)


async def request_smsc(
        http_method: str,
        api_method: str,
        *,
        login: str,
        password: str,
        payload: dict = None,
) -> dict:
    payload = payload or {}
    message = payload.pop('message')
    phones = payload.pop('phones')
    if not all((message, phones)):
        raise SmscApiError('message and phones are absent')

    # change it to enums in future
    if http_method not in ALLOWED_METHODS:
        raise SmscApiError('{0} is not allowed method'.format(
            http_method,
        ),
        )

    if api_method not in ALLOWED_API_METHODS:
        raise SmscApiError(
            '{0} is not allowed API method'.format(api_method),
        )

    session = asks.Session(connections=1)
    response = await session.request(
        method=http_method,
        url='{0}{1}'.format(SMSC_HOST, api_method),
        params={
            'login': login,
            'psw': password,
            'phones': phones,
            'mes': message,
            **payload,
            'fmt': 3,
            # 'cost': 1
        },
    )
    if response.status_code != http.HTTPStatus.OK:
        raise SmscApiError(response.text)
    if (parsed := response.json()).get('error'):
        raise SmscApiError(response.text)
    return parsed


if __name__ == '__main__':
    send.context_settings.update({'auto_envvar_prefix': ENV_PREFIX})
    trio.run(send.main)
