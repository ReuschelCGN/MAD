from mapadroid.db.model import AutoconfigRegistration

from mapadroid.mitm_receiver.endpoints.AbstractMitmReceiverRootEndpoint import AbstractMitmReceiverRootEndpoint


class AutoconfRegisterEndpoint(AbstractMitmReceiverRootEndpoint):
    """
    "/autoconfig/register"
    """

    # TODO: Auth/preprocessing for autoconfig?
    async def post(self):
        """ Device attempts to register with MAD.  Returns a session id for tracking future calls """
        status = 0
        #  TODO - auto-accept list
        if False:
            status = 1
        async with self._session.begin_nested() as nested_transaction:
            autoconfig_registration: AutoconfigRegistration = AutoconfigRegistration()
            autoconfig_registration.status = status
            autoconfig_registration.ip = self._get_request_address()
            autoconfig_registration.instance_id = self._get_instance_id()
            self._session.add(autoconfig_registration)
            await nested_transaction.commit()

        log_data = {
            'session_id': autoconfig_registration.session_id,
            'instance_id': self._get_instance_id(),
            'level': 2,
            'msg': 'Registration request from {}'.format(self._get_request_address())
        }
        await self.autoconfig_log(**log_data)
        self._commit_trigger = True
        return self._json_response(text=str(autoconfig_registration.session_id), status=201)
