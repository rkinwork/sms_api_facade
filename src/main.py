import http
import logging

import asyncclick as click
import asks
import trio

DEFAULT_SMS_TTL = '01:00'
ENV_PREFIX = 'DVMN_SMS'
SEND_ENDPOINT = 'https://smsc.ru/sys/send.php'

log = logging.getLogger(__file__)


class SMSCError(Exception):
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
    phones = ';'.join(phone.strip() for phone in numbers_src)
    message = '\n'.join(sms_text)
    session = asks.Session(connections=1)
    response = await session.get(
        SEND_ENDPOINT,
        params={
            'login': login,
            'psw': password,
            'phones': phones,
            'mes': message,
            'valid': ttl,
            'fmt': 3,
            # 'cost': 1,
        },
    )
    if response.status_code != http.HTTPStatus.OK:
        raise SMSCError(response.text)
    if (parsed := response.json()).get('error'):
        raise SMSCError(response.text)
    log.info('sms response %s', parsed)
    click.echo('messages has been sent')


if __name__ == '__main__':
    send.context_settings.update({'auto_envvar_prefix': ENV_PREFIX})
    trio.run(send.main)
