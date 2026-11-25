import json,re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.app import create_app
ROOT=Path(__file__).resolve().parents[1]; directory=ROOT/'api-reference/endpoint'
spec=create_app().openapi()
spec['servers']=[{'url':'http://localhost:8300','description':'Servidor local; altere para a URL da sua instância.'}]
for item in spec['paths'].values():
 for operation in item.values():
  if isinstance(operation,dict) and operation.get('security'):
   operation.setdefault('parameters',[]).append({'name':'X-Instance','in':'header','required':False,'description':'ID da sessão; omitido usa a sessão padrão. Também aceita ?session=.', 'schema':{'type':'string'}})
methods={'get','post','put','patch','delete','options','head'}
ops={(m.upper(),p):o for p,v in spec['paths'].items() for m,o in v.items() if m in methods}
def category(path):
 p=path.lower()
 if p.startswith('/logs'): return 'Logs','file-lines'
 if p.startswith('/stats'): return 'Estatísticas','chart-line'
 if p.startswith('/status'): return 'Monitoramento','heart-pulse'
 if p.startswith('/settings/privacy'): return 'Privacidade','shield-halved'
 if p.startswith('/settings/ip-'): return 'Controle de IP','shield-halved'
 if p.startswith('/management/database'): return 'Banco de Dados','database'
 if p.startswith('/messages/send-'): return 'Mensagens Interativas e Mídia','comments'
 for prefix,label,icon in [('experimental','Experimental','flask'),('groups','Grupos','user-group'),('channels','Canais','bullhorn'),('orders','Pedidos','cart-shopping'),('contacts','Contatos','address-book'),('management','Gerenciamento','database'),('settings','Configurações','sliders'),('system','Sistema','gear'),('instance','Instância','server'),('sessions','Sessões','layer-group'),('session','Conexão','qrcode'),('qr','Conexão','qrcode'),('webhooks','Webhooks','bolt'),('ai','Inteligência Artificial','robot'),('messages','Mensagens','message'),('send','Enviar Mensagens','paper-plane')]:
  if p.startswith('/'+prefix): return label,icon
 return 'Sistema','gear'
existing={}; stale=[]
for f in directory.glob('*.mdx'):
 text=f.read_text(encoding='utf-8'); match=re.search(r'^(?:api|openapi):\s*[\"\']?([A-Z]+)\s+([^\"\'\n]+)',text,re.M)
 if match:
  key=(match[1],match[2].strip())
  if key in ops: existing[key]=f
  else: stale.append(str(f))
groups={}
for (method,path),operation in ops.items():
 label,icon=category(path); operation['tags']=[label]
 f=existing.get((method,path))
 if f:
  text=f.read_text(encoding='utf-8'); front=text.split('---',2)[1]
  title=re.search(r'^title:\s*(.+)',front,re.M)
  title=title[1] if title else json.dumps(operation.get('summary',path),ensure_ascii=False)
  body=text.split('---',2)[2].strip()
  # Schema-driven API rendering supplies the authoritative request and response fields.
  spans=[]; depth=0; start=0
  for token in re.finditer(r'</?(?:ParamField|ResponseField|ResponseExample)\b[^>]*>',body):
   if token[0].startswith('</'):
    depth-=1
    if depth==0: spans.append((start,token.end()))
   elif token[0].endswith('/>'):
    if depth==0: spans.append((token.start(),token.end()))
   else:
    if depth==0: start=token.start()
    depth+=1
  if depth: raise ValueError(f'Unbalanced field components: {f}')
  for start,end in reversed(spans): body=body[:start]+body[end:]
 else:
  slug=re.sub('[^a-z0-9]+','-',method.lower()+'-'+path.lower()).strip('-')
  f=directory/(slug+'.mdx'); title=json.dumps(operation.get('summary',path),ensure_ascii=False); body=operation.get('description','')
 body=re.sub(r'(?m)^#{2,3} (?:Corpo da Requisição|Parâmetros da Requisição|Resposta)\s*(?=^#{1,3} |<|\Z)', '', body)
 body='\n'.join(line.rstrip() for line in body.splitlines())
 body=re.sub(r'\n{3,}', '\n\n', body).strip()
 f.write_text('---\ntitle: '+title+'\nicon: '+json.dumps(icon)+'\nopenapi: '+json.dumps(method+' '+path)+'\n---\n\n'+body+'\n' if body else '---\ntitle: '+title+'\nicon: '+json.dumps(icon)+'\nopenapi: '+json.dumps(method+' '+path)+'\n---\n',encoding='utf-8')
 groups.setdefault((label,icon),[]).append('api-reference/endpoint/'+f.stem)
config=json.loads((ROOT/'docs.json').read_text(encoding='utf-8'))
tab=config['navigation']['tabs'][1]
tab['groups']=[{'group':'Configuração','icon':'gear','pages':['api-reference/configuration']}]+[{'group':label,'icon':icon,'pages':pages} for (label,icon),pages in groups.items()]
config['api']['mdx']['server']='http://localhost:8300'
config['api']['openapi']='api-reference/openapi.json'
(ROOT/'docs.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'api-reference/openapi.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(ops)} operations synchronized; {len(existing)} existing pages; {len(ops)-len(existing)} new pages')
print('Unreferenced obsolete API pages:',stale)
