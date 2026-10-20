"""Prepare isolated local demo configuration; never replace existing demo keys."""
from pathlib import Path
import base64, json, os, subprocess
R=Path(os.environ['HARNESS_RUNTIME'])
if not R.is_absolute() or R.exists():
 raise SystemExit('HARNESS_RUNTIME must be a new absolute directory')
R.mkdir(mode=0o700,parents=True)
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
keyfile=R/'demo-keys.json'
subprocess.run(['java',str(Path(__file__).with_name('GenerateDemoKeys.java')),str(keyfile)],check=True)
keys=json.loads(keyfile.read_text())
# Prove distinct disposable key pairs and refusal to replace an existing file.
probe=R/'key-generation-probe.json'
command=['java',str(Path(__file__).with_name('GenerateDemoKeys.java'))]
subprocess.run(command+[str(probe)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
second=json.loads(probe.read_text())
all_keys=[keys['issuer'],keys['token'],second['issuer'],second['token']]
if any(set(k)!={'kty','crv','x','y','d'} or k['kty']!='EC' or k['crv']!='P-256' for k in all_keys):
 raise SystemExit('Synthetic key shape rejected')
if len({json.dumps(k,sort_keys=True) for k in all_keys})!=4:
 raise SystemExit('Synthetic keys must be fresh and distinct')
if keyfile.stat().st_mode & 0o777 != 0o600 or R.stat().st_mode & 0o777 != 0o700:
 raise SystemExit('Synthetic key permissions rejected')
if subprocess.run(command+[str(probe)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0:
 raise SystemExit('Existing key file must not be replaced')
probe.unlink()
preparation_report=Path(os.environ['HARNESS_PREPARATION_REPORT'])
preparation_report.parent.mkdir(parents=True,exist_ok=True)
preparation_report.write_text(json.dumps({'schemaVersion':1,'sourceCommit':os.environ['GITHUB_SHA'],
 'freshDistinctIssuerTokenAndRepeatKeys':True,'existingKeyFileRejected':True,
 'privateFileMode':'0600','privateDirectoryMode':'0700','upstreamCredentialsUsed':False},indent=2)+'\n')
pub={k:v for k,v in keys['issuer'].items() if k!='d'}
did='did:jwk:'+b64(json.dumps(pub,separators=(',',':')).encode())
(R/'public-issuer.json').write_text(json.dumps({'did':did,'name':'LSP Teknik Ketenagalistrikan Nusantara (demo)'}))
def conf(s,n,v):
 p=R/'walt'/s/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2));p.chmod(0o600)
for svc,port in [('issuer',7005),('wallet',7006),('verifier',7004)]:
 conf(svc,'web.conf',{'webHost':'0.0.0.0','webPort':port})
 conf(svc,'_features.conf',{'enabledFeatures':['wallet2-persistence'] if svc=='wallet' else [],'disabledFeatures':[]})
conf('issuer','issuer-service.conf',{'baseUrl':'http://issuer:7005','enforcePushedAuthorizationRequests':False,'ciTokenKey':json.dumps({'type':'jwk','jwk':keys['token']})})
conf('issuer','authentication-service.conf',{'name':'unused-for-preauthorized-demo','authorizeUrl':'http://issuer:7005/unused','accessTokenUrl':'http://issuer:7005/unused','clientId':'unused','clientSecret':'unused','defaultScopes':['openid']})
conf('issuer','credential-issuer-metadata.conf',{
 'issuerDisplay':[{'name':'LSP Teknik Ketenagalistrikan Nusantara (demo)','locale':'id'}],
 'credentialConfigurations':{'competency_demo':{'format':'dc+sd-jwt','scope':'competency_demo','vct':'vctBaseUrl','credential_signing_alg_values_supported':['ES256'],'cryptographic_binding_methods_supported':['jwk','did:jwk'],'proof_types_supported':{'jwt':{'proof_signing_alg_values_supported':['ES256']}},'credential_metadata':{'display':[{'name':'Bukti Kompetensi (demo)','locale':'id'}],'claims':[{'path':[c],'mandatory':True} for c in ['id','candidate_id','competency_code','assessment_result']]}}}})
conf('issuer','issuer2-profiles.conf',{'profiles':{'competencyDemo':{'name':'Bukti Kompetensi (demo)','credentialConfigurationId':'competency_demo','issuerKey':{'type':'jwk','jwk':keys['issuer']},'issuerDid':did,'credentialData':{'candidate_id':'candidate-demo-001','competency_code':'DEMO-ELEC-001','assessment_result':'competent'},'mapping':{'id':'<uuid>','iat':'<timestamp-seconds>','nbf':'<timestamp-seconds>','exp':'<timestamp-in-seconds:365d>'}}}})
conf('wallet','wallet-service.conf',{'publicBaseUrl':'http://wallet:7006'})
conf('wallet','wallet2-persistence.conf',{'jdbcUrl':'jdbc:sqlite:/data/wallet2.db','driverClassName':'org.sqlite.JDBC'})
conf('verifier','verifier-service.conf',{'clientMetadata':{'client_name':'PT Karya Instalasi Nusantara (demo)'},'urlPrefix':'http://verifier:7004/verification-session','urlHost':'openid4vp://authorize'})
print('Prepared fresh synthetic service configuration.')
