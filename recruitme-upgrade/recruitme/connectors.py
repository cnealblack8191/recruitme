"""Fixed-host, credential-free search. No crawling, redirects, or paid fallback."""
import json
import urllib.request
import urllib.error
import time
from .budget import StopRun
from .governors import ProviderLimitReached

ENDPOINT = 'https://mcp.exa.ai/mcp?tools=web_search_exa'


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise StopRun('Redirect refused')


def decode_response(raw):
    text = raw.decode('utf-8')
    if text.lstrip().startswith('{'):
        return json.loads(text)
    # Streamable HTTP MCP may use Server Sent Events. Only parse JSON data.
    messages = []
    for event in text.replace('\r\n', '\n').split('\n\n'):
        data = '\n'.join(line[5:].lstrip() for line in event.splitlines() if line.startswith('data:'))
        if data and data != '[DONE]':
            messages.append(json.loads(data))
    if not messages:
        raise StopRun('Unrecognized provider response')
    return messages[-1]


class ExaFree:
    name = 'exa_free'
    supports_options = True
    max_results = 5

    @staticmethod
    def accepts_options(options):
        return not options.get('start_date') and not options.get('end_date')

    def __init__(self, ledger, run_id, guard, opener=None):
        self.ledger, self.run_id, self.guard = ledger, run_id, guard
        self.opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        self.session = None
        self.protocol = '2024-11-05'
        self.counter = 0

    def rpc(self, method, params, operation, logical_id, notification=False):
        self.guard()
        op = self.ledger.reserve(self.run_id, self.name, operation, logical_id)
        self.counter += 1
        body = {'jsonrpc': '2.0', 'method': method, 'params': params}
        if not notification:
            body['id'] = self.counter
        headers = {'Content-Type':'application/json', 'Accept':'application/json, text/event-stream',
                   'User-Agent':'RecruitMe-POC/0.1', 'MCP-Protocol-Version':self.protocol}
        if self.session:
            headers['Mcp-Session-Id'] = self.session
        req = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), headers=headers, method='POST')
        try:
            remaining=self.ledger.dispatch(self.run_id,op)['deadline']-time.time()
            if remaining <= 0:
                raise StopRun('RUNTIME_LIMIT_REACHED: Shared research deadline expired')
            with self.opener.open(req, timeout=min(25,remaining)) as res:
                raw = res.read(524289)
                request_id = res.headers.get('x-request-id')
                if res.headers.get('Mcp-Session-Id'):
                    self.session = res.headers['Mcp-Session-Id']
                if len(raw) > 524288:
                    raise StopRun('Provider response exceeds 512 KiB limit')
                result = {} if notification and not raw else decode_response(raw)
            receipt = result.get('result', {})
            limited = any(c.get('type')=='text' and "exa's free mcp rate limit" in c.get('text','').lower()
                          for c in receipt.get('content',[]))
            status = 'PROVIDER_LIMIT_REACHED' if limited else ('ERROR' if result.get('error') or receipt.get('isError') else 'SUCCESS')
            self.last_observed_at = time.time()
            self.last_operation_id = op
            self.ledger.save_outcome(op,status,receipt,self.last_observed_at)
            self.ledger.reconcile(op,'0',request_id)
            if limited:
                raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: exa_free')
            if status == 'ERROR':
                raise StopRun('Provider returned an error; no automatic retry')
            return receipt
        except ProviderLimitReached:
            raise
        except Exception as error:
            if isinstance(error,urllib.error.HTTPError) and error.code==429:
                self.ledger.save_outcome(op,'PROVIDER_LIMIT_REACHED',{'http_status':429})
                self.ledger.reconcile(op,'0')
                raise ProviderLimitReached('PROVIDER_LIMIT_REACHED: exa_free HTTP 429') from None
            self.ledger.save_outcome(op,'UNKNOWN')
            row = self.ledger.db.execute('SELECT state FROM operations WHERE id=?',(op,)).fetchone()
            if row['state'] == 'RESERVED':
                self.ledger.reconcile(op,None)
            if isinstance(error,StopRun):
                self.ledger.stop(self.run_id,error)
                raise
            self.ledger.stop(self.run_id,'Provider failure; no automatic retry')
            raise StopRun('Provider request failed; unresolved reservations retained; no retry') from None

    def initialize(self):
        r = self.rpc('initialize', {'protocolVersion':self.protocol, 'capabilities':{},
                     'clientInfo':{'name':'recruitme','version':'0.1.0'}}, 'initialize', 'initialize')
        self.protocol = r.get('protocolVersion', self.protocol)
        self.rpc('notifications/initialized', {}, 'initialized', 'initialized', notification=True)

    def tools(self):
        return self.rpc('tools/list', {}, 'list_tools', 'list-tools').get('tools', [])

    def search(self, query, count=5, options=None):
        if options:
            from .plugins import filtered_query
            query=filtered_query(query,options)
        if not isinstance(query,str) or not 1 <= len(query) <= 500 or not 1 <= count <= 5:
            raise StopRun('Invalid bounded search request')
        self.guard()
        logical_id = query if count == 5 else json.dumps([query,count])
        cached = self.ledger.cached_search(self.run_id,self.name,logical_id)
        if cached:
            self.last_observed_at=cached['observed_at']
            self.last_operation_id=cached['operation_id']
            return cached['response']
        return self.rpc('tools/call', {'name':'web_search_exa','arguments':{
            'query':query,'numResults':count}}, 'search', logical_id)


CONNECTORS = {'exa_free': ExaFree}
