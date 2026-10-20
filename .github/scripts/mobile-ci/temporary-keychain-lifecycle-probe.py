import json, os, pathlib, subprocess, time
root=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'waltid-identity'
out=pathlib.Path(os.environ['GITHUB_WORKSPACE'])/'keychain-lifecycle'
out.mkdir(exist_ok=True)
record={'identity':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'results':[]}
def run(args,log,timeout=600):
 start=time.monotonic()
 with (out/log).open('w') as stream:
  result=subprocess.run(args,cwd=root,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
 return {'returncode':result.returncode,'seconds':round(time.monotonic()-start,3),'log':log}
sim=subprocess.check_output(['xcrun','simctl','create','WAL1585 Keychain lifecycle control','iPhone 17','iOS 27.0'],text=True).strip()
record['simulator']=sim
(out/'state.json').write_text(json.dumps(record,indent=2))
stream=None
try:
 record['boot']=run(['xcrun','simctl','bootstatus',sim,'-b'],'boot.log')
 assert record['boot']['returncode']==0
 with (out/'lifecycle.log').open('w') as f:
  stream=subprocess.Popen(['xcrun','simctl','spawn',sim,'log','stream','--style','compact','--level','info','--predicate','process == "runningboardd" OR (process == "SpringBoard" AND eventMessage CONTAINS[c] "keychain") OR process == "KeychainTests"'],stdout=f,stderr=subprocess.STDOUT)
  record['results'].append(run(['bash','waltid-libraries/crypto/waltid-crypto2-signum/scripts/test-ios-keychain.sh',sim,str(out/'baseline-1')],'baseline-1-driver.log',1200))
  for n in range(2,7):
   if record['results'][-1]['returncode']!=0: break
   record['results'].append(run(['python3','waltid-libraries/crypto/waltid-crypto2-signum/scripts/run_keychain_tests.py',sim,str(out/f'baseline-{n}')],f'baseline-{n}-driver.log',180))
   (out/'state.json').write_text(json.dumps(record,indent=2))
finally:
 if stream:
  stream.terminate()
  stream.wait(timeout=10)
 record['cleanup']=run(['xcrun','simctl','delete',sim],'cleanup.log',90)
 (out/'state.json').write_text(json.dumps(record,indent=2))
 print(json.dumps(record,indent=2))
if any(r["returncode"] for r in record["results"]): raise SystemExit(1)
