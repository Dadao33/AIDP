"""Signed AIDP Agent Flow gateway call. No silent fallback, no JDE API."""
import json,os,subprocess,tempfile,re
from pathlib import Path

def extract_text(value):
    if isinstance(value,str):return value
    if isinstance(value,list):return '\n'.join(filter(None,(extract_text(v) for v in value)))
    if not isinstance(value,dict):return ''
    if value.get('type') in ('OUTPUT_TEXT','TEXT','text','output_text') and isinstance(value.get('text'),str):return value['text']
    for key in ('answer','output','content','message','response','data'):
        if key in value:
            out=extract_text(value[key])
            if out:return out
    return ''

def chat(question,context,session_id):
    endpoint=os.environ.get('AIDP_AGENT_CHAT_URL','')
    if not re.fullmatch(r'https://gateway\.aidp\.[a-z0-9-]+\.oci\.oraclecloud\.com/agentendpoint/[a-f0-9-]+/chat',endpoint):
        raise ValueError('Configure the BIC AIDP Agent Flow HTTPS endpoint before using live mode.')
    prompt=json.dumps({'application':'BIC Retail Studio','trusted_context':context,'user_question':question},ensure_ascii=False)
    payload={'isStreamEnabled':False,'trace':True,'sessionKey':session_id,'input':[{'role':'User','content':[{'type':'INPUT_TEXT','text':prompt}]}]}
    with tempfile.TemporaryDirectory(prefix='bic-aidp-') as tmp:
        p=Path(tmp)/'request.json';p.write_text(json.dumps(payload));p.chmod(0o600)
        args=[os.environ.get('OCI_CLI','oci'),'raw-request','--http-method','POST','--target-uri',endpoint,'--request-body','file://'+str(p),'--request-headers','{"Content-Type":"application/json","Accept":"application/json"}','--profile',os.environ.get('OCI_CONFIG_PROFILE','DEFAULT'),'--read-timeout','90','--connection-timeout','10']
        if os.environ.get('OCI_AUTH')=='security_token':args+=['--auth','security_token']
        proc=subprocess.run(args,capture_output=True,text=True,timeout=105,env={**os.environ,'OCI_CLI_SUPPRESS_FILE_PERMISSIONS_WARNING':'True'})
    if proc.returncode:raise RuntimeError('AIDP call failed. Check CLI authentication and endpoint availability. No rehearsal answer was substituted.')
    outer=json.loads(proc.stdout)
    if not str(outer.get('status','')).startswith('2'):raise RuntimeError('AIDP returned '+str(outer.get('status')))
    raw=outer.get('data',{});txt=extract_text(raw)
    # Agent response contract is JSON. Fail closed on unexpected content.
    txt=re.sub(r'^```(?:json)?\s*|\s*```$','',txt.strip())
    try:result=json.loads(txt)
    except json.JSONDecodeError:raise RuntimeError('AIDP returned an unexpected response format. Inspect the Playground response; no unverified solution was applied.')
    if not isinstance(result,dict) or not isinstance(result.get('answer'),str):raise RuntimeError('Missing AIDP answer')
    labels={'get_portfolio':'Read portfolio exceptions','calculate_account_scenario':'Calculate current scenario','evaluate_transfer':'Calculate warehouse transfer','evaluate_expedite':'Calculate receipt acceleration','evaluate_split':'Calculate split-delivery impact','search_bic_policies':'Retrieve policy sources','get_policy_register':'Check policy version','get_financial_outlook':'Read budget and margin','get_model_performance':'Read model evaluation'}
    activity=[]
    for message in raw.get('output',[]) if isinstance(raw,dict) else []:
        for content in message.get('content',[]):
            if content.get('type')!='trace':continue
            try:trace=json.loads(content.get('text','{}'))
            except (TypeError,json.JSONDecodeError):continue
            for span in trace.get('spans',[]):
                name=span.get('attributes',{}).get('traceloop.entity.name')
                if name in labels and span.get('spanName','').endswith('.tool'):
                    activity.append({'tool':name,'label':labels[name],'seconds':round(max(0,span.get('endTime',0)-span.get('startTime',0))/1e9,1),'failed':span.get('status',{}).get('code')=='ERROR'})
    result['tool_activity']=activity
    return result
