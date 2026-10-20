"""Real HTTP integration with the pinned walt.id services (no simulated responses)."""
import json, os, urllib.request, urllib.error, urllib.parse
PORTS={'issuer':7005,'wallet':7006,'verifier':7004}
def call(service,path,body=None,method=None):
 url=(os.environ.get(service.upper()+'_URL',f'http://127.0.0.1:{PORTS[service]}')+path)
 data=None if body is None else json.dumps(body).encode()
 req=urllib.request.Request(url,data=data,method=method or ('GET' if body is None else 'POST'),headers={'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=40) as r:
   b=r.read().decode()
   if not b: return None
   try:return json.loads(b)
   except json.JSONDecodeError:return b
 except urllib.error.HTTPError as e:
  raise RuntimeError(f'{service}: HTTP {e.code}; response body withheld') from None

def new_wallet():
 w=call('wallet','/wallet',{})['walletId']
 key=call('wallet',f'/wallet/{w}/keys/generate',{'backend':'jwk','keyType':'secp256r1'})
 return w,key['keyId']

def offer(code='DEMO-ELEC-001'):
 return call('issuer','/issuer2/credential-offers',{'profileId':'competencyDemo','authMethod':'PRE_AUTHORIZED','runtimeOverrides':{'credentialData':{'candidate_id':'candidate-demo-001','competency_code':code,'assessment_result':'competent'}}})

def resolve_offer(w,url):return call('wallet',f'/wallet/{w}/credentials/receive/resolve-offer',{'offerUrl':url})

def accept(w,k,resolved):
 p=f'/wallet/{w}/credentials/receive/'
 t=call('wallet',p+'request-token',{'tokenEndpoint':resolved['tokenEndpoint'],'preAuthorizedCode':resolved['preAuthorizedCode'],'credentialIssuer':resolved['credentialIssuer']})
 u=urllib.parse.urlparse(resolved['nonceEndpoint'])
 nonce=call('issuer',u.path,{})['c_nonce']
 proof=call('wallet',p+'sign-proof',{'issuerUrl':resolved['credentialIssuer'],'nonce':nonce,'credentialConfigurationId':resolved['credentialConfigurationIds'][0],'keyId':k})
 return call('wallet',p+'fetch-credential',{'credentialEndpoint':resolved['credentialEndpoint'],'accessToken':t['accessToken'],'credentialConfigurationId':resolved['credentialConfigurationIds'][0],'proofJwt':proof['proofJwt'],'storeInWallet':True})

def session():
 return call('verifier','/verification-session/create',{'flow_type':'cross_device','core_flow':{'dcql_query':{'credentials':[{'id':'competency','format':'dc+sd-jwt','multiple':True,'meta':{'vct_values':['http://issuer:7005/openid4vci/competency_demo']},'require_cryptographic_holder_binding':True,'claims':[{'path':[x]} for x in ['id','candidate_id','competency_code','assessment_result','exp']]}]},'policies':{'vc_policies':[{'policy':'signature'},{'policy':'expiration','requireField':True},{'policy':'not-before'}]}}})

def preview(w,url):return call('wallet',f'/wallet/{w}/credentials/present/preview',{'requestUrl':url})

def present(w,url,selection,key):
 p=f'/wallet/{w}/credentials/present/'
 vp=call('wallet',p+'build-vp-token',{'requestUrl':url,'keyId':key,'selectedCredentialOptions':[{'queryId':selection['queryId'],'credentialId':selection['credentialId']}]})
 return call('wallet',p+'send-response',{'requestUrl':url,'vpToken':vp['vpToken']})

def credentials(w):return call('wallet',f'/wallet/{w}/credentials')
def info(sid):return call('verifier',f'/verification-session/{sid}/info')
