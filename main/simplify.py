import os, sys, json, subprocess, platform, tempfile, gc

pydir=os.path.abspath(os.path.dirname(__file__))
otfccdump=os.path.join(pydir, 'otfcc/otfccdump')
otfccbuild=os.path.join(pydir, 'otfcc/otfccbuild')
if platform.system() in ('Mac', 'Darwin'):
	otfccdump+='1'
	otfccbuild+='1'
if platform.system() == 'Linux':
	otfccdump+='2'
	otfccbuild+='2'

cfg=json.load(open(os.path.join(pydir, 'config.json'), 'r', encoding='utf-8'))

def cpchs():
	cpgl=(('鍊', '链'), ('鍾', '锺'), ('鉅', '钜'))
	for cg in cpgl:
		if str(ord(cg[0])) in font['cmap'] and str(ord(cg[1])) in font['cmap']:
			gt=font['cmap'][str(ord(cg[0]))]
			gs=font['cmap'][str(ord(cg[1]))]
			gnew=dict()
			if 'CFF_fdSelect' in font['glyf'][gt]:
				gnew['CFF_fdSelect']=font['glyf'][gt]['CFF_fdSelect']
			if 'CFF_CID' in font['glyf'][gt]:
				gnew['CFF_CID']=font['glyf'][gt]['CFF_CID']
			for k in font['glyf'][gs].keys():
				if k not in ('CFF_fdSelect', 'CFF_CID'):
					gnew[k]=font['glyf'][gs][k]
			font['glyf'][gt]=gnew
	with open(os.path.join(pydir, 'tsoneo.dt'),'r',encoding='utf-8') as f:
		for txl in f.readlines():
			litm=txl.split('#')[0].strip()
			if '-' not in litm:
				continue
			s, t=litm.split(' ')[0].split('-')
			s=s.strip()
			t=t.strip()
			if s and t and s != t and str(ord(t)) in font['cmap']:
				font['cmap'][str(ord(s))]=font['cmap'][str(ord(t))]

def mklks():
	assert 'hani_DFLT' in font['GSUB']['languages']
	for t in font['GSUB']['languages'].values():
		t['features'].insert(0, 'ccmp_ts')
	font['GSUB']['features']['ccmp_ts']=['mult', 'sigl']
	font['GSUB']['lookupOrder']=['sig1','sig2','sig3','sig4','mult','sigl']+font['GSUB']['lookupOrder']
	with open(os.path.join(pydir, 'tsonem.dt'),'r',encoding='utf-8') as f:
		sig1, sig2, sig3, sig4, ltc=(dict() for i in range(5))
		sbtbs=list()
		for txl in f.readlines():
			litm=txl.split('#')[0].strip()
			if '-' not in litm:
				continue
			sb=dict()
			sb['match']=list()
			ls=litm.strip().split(' ')
			s, t=ls[0].split('-')
			dchs=ls[1:]
			sg=font['cmap'][str(ord(s))]
			tg=font['cmap'][str(ord(t))]
			if sg!=tg and tg not in ltc:
				if sg not in sig1:
					sig1[sg]=tg
					ltc[tg]='sig1'
				elif sg not in sig2:
					sig2[sg]=tg
					ltc[tg]='sig2'
				elif sg not in sig3:
					sig3[sg]=tg
					ltc[tg]='sig3'
				elif sg not in sig4:
					sig4[sg]=tg
					ltc[tg]='sig4'
				else:
					raise
			chat=dchs.index(s)
			for strs in dchs:
				lw=list()
				for ch in strs:
					codch=str(ord(ch))
					if codch in font['cmap'] and font['cmap'][codch] not in lw:
						lw.append(font['cmap'][codch])
				assert len(lw)>0
				sb['match'].append(lw)
			assert s and t and chat>-1
			if sg==tg:
				sb['apply']=[]
			else:
				sb['apply']=[{'at':chat, 'lookup':ltc[tg]}]
			sb['inputBegins']=chat
			sb['inputEnds']=chat+1
			sbtbs.append(sb)
		for ss in ('sig1', 'sig2', 'sig3', 'sig4', 'sigl'):
			font['GSUB']['lookups'][ss]=dict()
			font['GSUB']['lookups'][ss]['type']='gsub_single'
			font['GSUB']['lookups'][ss]['flags']=dict()
		font['GSUB']['lookups']['sig1']['subtables']=[sig1]
		font['GSUB']['lookups']['sig2']['subtables']=[sig2]
		font['GSUB']['lookups']['sig3']['subtables']=[sig3]
		font['GSUB']['lookups']['sig4']['subtables']=[sig4]
		font['GSUB']['lookups']['mult']={'type':'gsub_chaining','flags':{},'subtables':sbtbs}

def stinf():
	fpsn=str()
	for n1 in font['name']:
		if n1['nameID']==6 and '-' in n1['nameString']:
			fpsn=n1['nameString']
			break
	wt=str()
	for n1 in font['name']:
		if n1['nameID']==2:
			wt=n1['nameString']
		elif n1['nameID']==17:
			wt=n1['nameString']
			break
	cpsp, cpurl=str(), str()
	for n1 in font['name']:
		if n1['nameID']==13:
			cpsp=n1['nameString']
		elif n1['nameID']==14:
			cpurl=n1['nameString']
		if cpsp and cpurl:
			break
	isit='Italic' in wt
	wt=wt.replace('Italic', '').strip()
	if not wt: wt='Regular'
	ishw='HW' in fpsn
	itml, itm, hwm=str(), str(), str()
	if ishw: hwm=' HW'
	if isit: itml, itm=' Italic', 'It'
	if 'Sans' in fpsn:
		fmlName=cfg['fontName']+' Sans'+hwm
		zhName=cfg['fontNameZH']+' 黑体'+hwm
	elif 'Serif' in fpsn:
		fmlName=cfg['fontName']+' Serif'+hwm
		zhName=cfg['fontNameZH']+' 宋体'+hwm
	elif 'Mono' in fpsn:
		fmlName=cfg['fontName']+' Mono'+hwm
		zhName=cfg['fontNameZH']+' 等宽'+hwm
	else:
		raise
	ftName=fmlName
	ftNamezh=zhName
	if wt not in ('Regular', 'Bold'):
		ftName+=' '+wt
		ftNamezh+=' '+wt
	subfamily='Regular'
	if isit:
		if wt=='Bold':
			subfamily='Bold Italic'
		else:
			subfamily='Italic'
	elif wt=='Bold':
		subfamily='Bold'
	psName=fmlName.replace(' ', '')+'-'+fpsn.split('-')[-1].replace('It', '')+itm
	uniqID=cfg['fontVersion']+';'+cfg['fontID'].strip()+';'+psName
	if wt=='Bold':
		fullName=ftName+' '+wt+itml
		fullNamezh=ftNamezh+' '+wt+itml
	else:
		fullName=ftName+itml
		fullNamezh=ftNamezh+itml
	newname=list()
	newname+=[
		{'languageID': 1033,'nameID': 0,'nameString': cfg['fontCopyright']}, 
		{'languageID': 1033,'nameID': 1,'nameString': ftName}, 
		{'languageID': 1033,'nameID': 2,'nameString': subfamily}, 
		{'languageID': 1033,'nameID': 3,'nameString': uniqID}, 
		{'languageID': 1033,'nameID': 4,'nameString': fullName}, 
		{'languageID': 1033,'nameID': 5,'nameString': 'Version '+cfg['fontVersion']}, 
		{'languageID': 1033,'nameID': 6,'nameString': psName}, 
		{'languageID': 1033,'nameID': 9,'nameString': cfg['fontDesigner']}, 
		{'languageID': 1033,'nameID': 10,'nameString': cfg['fontDiscript']}, 
		{'languageID': 1033,'nameID': 11,'nameString': cfg['fontVURL']}, 
		{'languageID': 1033,'nameID': 13,'nameString': cpsp}, 
		{'languageID': 1033,'nameID': 14,'nameString': cpurl}
		]
	if wt not in ('Regular', 'Bold'):
		newname+=[
			{'languageID': 1033,'nameID': 16,'nameString': fmlName}, 
			{'languageID': 1033,'nameID': 17,'nameString': wt+itml}
			]
	for lanid in (1028, 2052, 3076):
		newname+=[
			{'languageID': lanid,'nameID': 1,'nameString': ftNamezh}, 
			{'languageID': lanid,'nameID': 2,'nameString': subfamily}, 
			{'languageID': lanid,'nameID': 4,'nameString': fullNamezh}
			]
		if wt not in ('Regular', 'Bold'):
			newname+=[
				{'languageID': lanid,'nameID': 16,'nameString': zhName}, 
				{'languageID': lanid,'nameID': 17,'nameString': wt+itml}
				]
	for nl in newname:
		nl['platformID']=3
		nl['encodingID']=1
	font['name']=newname
	font['OS_2']['achVendID']=cfg['fontID']
	font['head']['fontRevision']=float(cfg['fontVersion'])
	if 'CFF_' in font:
		font['CFF_']['notice']=''
		font['CFF_']['fontName']=psName
		font['CFF_']['fullName']=fmlName+' '+wt
		font['CFF_']['familyName']=fmlName
		if 'fdArray' in font['CFF_']:
			nfd=dict()
			for k in font['CFF_']['fdArray'].keys():
				nfd[psName+'-'+k.split('-')[-1]]=font['CFF_']['fdArray'][k]
			font['CFF_']['fdArray']=nfd
			for gl in font['glyf'].values():
				if 'CFF_fdSelect' in gl:
					gl['CFF_fdSelect']=psName+'-'+gl['CFF_fdSelect'].split('-')[-1]

def chkungl():
	gtgls=set()
	for k in font['cmap_uvs'].keys():
		c, v=k.split(' ')
		if c in font['cmap']:
			gtgls.add(font['cmap_uvs'][k])
	gtgls.update(font['cmap'].values())
	loc=set()
	for lang in font['GSUB']['languages'].keys():
		for fs in font['GSUB']['languages'][lang]['features']:
			if fs.split('_')[0]=='locl':
				loc.update(set(font['GSUB']['features'][fs]))
	for subs in loc:
		del font['GSUB']['lookups'][subs]
		f1todel=set()
		for f1 in font['GSUB']['features'].keys():
			if subs in font['GSUB']['features'][f1]:
				font['GSUB']['features'][f1].remove(subs)
			if len(font['GSUB']['features'][f1]) == 0:
				f1todel.add(f1)
		for  f1 in f1todel:
			del font['GSUB']['features'][f1]
	if 'GSUB' in font:
		for lkn in font['GSUB']['lookupOrder']:
			if lkn in font['GSUB']['lookups']:
				lookup=font['GSUB']['lookups'][lkn]
				if lookup['type'] == 'gsub_single':
					for subtable in lookup['subtables']:
						for g1, g2 in list(subtable.items()):
							if g1 in gtgls:
								gtgls.add(g2)
				elif lookup['type'] == 'gsub_alternate':
					for subtable in lookup['subtables']:
						for item in set(subtable.keys()):
							if item in gtgls:
								gtgls.update(set(subtable[item]))
				elif lookup['type'] == 'gsub_ligature': 
					for subtable in lookup['subtables']:
						for item in subtable['substitutions']:
							if set(item['from']).issubset(gtgls):
								gtgls.add(item['to'])
				elif lookup['type'] == 'gsub_chaining':
					for subtable in lookup['subtables']:
						for ls in subtable['match']:
							for l1 in ls:
								gtgls.update(set(l1))
	unugls=set()
	unugls.update(set(font['glyph_order']))
	notg={'.notdef', '.null', 'nonmarkingreturn', 'NULL', 'NUL'}
	unugls.difference_update(notg)
	unugls.difference_update(gtgls)
	for ugl in unugls:
		font['glyph_order'].remove(ugl)
		del font['glyf'][ugl]
	for lookup in font['GSUB']['lookups'].values():
		if lookup['type'] == 'gsub_single':
			for subtable in lookup['subtables']:
				for g1, g2 in list(subtable.items()):
					if g1 in unugls or g2 in unugls:
						del subtable[g1]
		elif lookup['type'] == 'gsub_alternate':
			for subtable in lookup['subtables']:
				for item in set(subtable.keys()):
					if item in unugls or len(set(subtable[item]).intersection(unugls))>0:
						del subtable[item]
		elif lookup['type'] == 'gsub_ligature': 
			for subtable in lookup['subtables']:
				s1=list()
				for item in subtable['substitutions']:
					if item['to'] not in unugls and len(set(item['from']).intersection(unugls))<1:
						s1.append(item)
				subtable['substitutions']=s1
		elif lookup['type'] == 'gsub_chaining':
			for subtable in lookup['subtables']:
				for ls in subtable['match']:
					for l1 in ls:
						l1=list(set(l1).difference(unugls))
	for lookup in font['GPOS']['lookups'].values():
		if lookup['type'] == 'gpos_single':
			for subtable in lookup['subtables']:
				for item in list(subtable.keys()):
					if item in unugls:
						del subtable[item]
		elif lookup['type'] == 'gpos_pair':
			for subtable in lookup['subtables']:
				for item in list(subtable['first'].keys()):
					if item in unugls:
						del subtable['first'][item]
				for item in list(subtable['second'].keys()):
					if item in unugls:
						del subtable['second'][item]
		elif lookup['type'] == 'gpos_mark_to_base':
			nsb=list()
			for subtable in lookup['subtables']:
				gs=set(subtable['marks'].keys()).union(set(subtable['bases'].keys()))
				if len(gs.intersection(unugls))<1:
					nsb.append(subtable)
			lookup['subtables']=nsb

if len(sys.argv) > 2:
	print('====Start Build XiaoheSimplify Fonts====\n')
	print('Loading font...')
	font=json.loads(subprocess.check_output((otfccdump, '--no-bom', sys.argv[1])).decode("utf-8", "ignore"))
	print('Processing...')
	cpchs()
	chkungl()
	mklks()
	stinf()
	tpf=tempfile.mktemp('.json')
	print('Saving font...')
	with open(tpf, 'w', encoding='utf-8') as f:
		f.write(json.dumps(font))
	del font
	gc.collect()
	subprocess.run((otfccbuild, '-s', '--keep-modified-time', '--keep-average-char-width', '-O3', '-q', '-o', sys.argv[2], tpf))
	os.remove(tpf)
	print('Finished!')
