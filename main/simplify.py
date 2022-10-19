import os, sys, json, subprocess, platform, tempfile, gc

pydir = os.path.abspath(os.path.dirname(__file__))
otfccdump = os.path.join(pydir, 'otfcc/otfccdump')
otfccbuild = os.path.join(pydir, 'otfcc/otfccbuild')
if platform.system() in ('Mac', 'Darwin'):
    otfccdump += '1'
    otfccbuild += '1'
if platform.system() == 'Linux':
    otfccdump += '2'
    otfccbuild += '2'

fontver='1.003'
fontid='GWF'

def addvariants():
    with open(os.path.join(pydir, 'datas/Variants.txt'),'r',encoding = 'utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#') or '\t' not in line:
                continue
            vari = line.strip().split('\t')
            codein = 0
            for ch1 in vari:
                if str(ord(ch1)) in font['cmap']:
                    codein = ord(ch1)
                    break
            if codein != 0:
                for ch1 in vari:
                    if str(ord(ch1)) not in font['cmap']:
                        font['cmap'][str(ord(ch1))] = font['cmap'][str(codein)]

def transforme():
    cpgl=(('鍊', '链'), ('鍾', '锺'))
    for cg in cpgl:
        if str(ord(cg[0])) in font['cmap']and str(ord(cg[1])) in font['cmap']:
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

    with open(os.path.join(pydir, 'datas/Chars_ts.txt'),'r',encoding = 'utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#') or '\t' not in line:
                continue
            l1=line.strip().split('\t')
            s, t = l1[0], l1[1]
            s = s.strip()
            t = t.strip()
            if s and t and s != t:
                addunicodest(str(ord(t)), str(ord(s)))

def addunicodest(tunic, sunic):
    if tunic not in font['cmap']:
        return
    if sunic in font['cmap']:
        unu.add(font['cmap'][sunic])
    tname = font['cmap'][tunic]
    font['cmap'][sunic] = tname

def lookuptable():
    print('Building lookups...')
    if not 'GSUB' in font:
        print('Creating empty GSUB!')
        font['GSUB'] = {
                            'languages': 
                            {
                                'hani_DFLT': 
                                {
                                    'features': []
                                }
                            }, 
                            'features': {}, 
                            'lookups': {}, 
                            'lookupOrder': []
                        }
    if not 'hani_DFLT' in font['GSUB']['languages']:
        font['GSUB']['languages']['hani_DFLT'] = {'features': []}
    for table in font['GSUB']['languages'].values():
        table['features'].insert(0, 'liga_st')
    font['GSUB']['features']['liga_st'] = ['wordsc', 'stchars', 'wordtc']
    font['GSUB']['lookupOrder'].append('wordsc')
    font['GSUB']['lookupOrder'].append('stchars')
    font['GSUB']['lookupOrder'].append('wordtc')
    build_char_table()
    build_word_table()

def build_char_table():
    kt = dict()
    with open(os.path.join(pydir, 'datas/TSCharacters.txt'),'r',encoding = 'utf-8') as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#') or '\t' not in line:
                continue
            s, t = line.strip().split('\t')
            s = s.strip()
            t = t.strip()
            if s and t and s != t:
                codesc = ord(s)
                codetc = ord(t)
                if str(ord(s)) in font['cmap'] and str(ord(t)) in font['cmap']:
                    kt[font['cmap'][str(ord(s))]] = font['cmap'][str(ord(t))]
    font['GSUB']['lookups']['stchars'] = {
                                            'type': 'gsub_single',
                                            'flags': {},
                                            'subtables': [kt]
                                         }

def build_word_table():
    stword = list()
    with open(os.path.join(pydir, 'datas/TSPhrases.txt'),'r',encoding = 'utf-8') as f:
        ls = list()
        for line in f.readlines():
            line = line.strip()
            if line.startswith('#') or '\t' not in line:
                continue
            ls.append(line.strip().split(' ')[0])
        for line in ls:
            s, t = line.strip().split('\t')
            s = s.strip()
            t = t.strip()
            if not(s and t):
                continue
            codesc = tuple(str(ord(c)) for c in s)
            codetc = tuple(str(ord(c)) for c in t)
            if all(codepoint in font['cmap'] for codepoint in codesc) \
                    and all(codepoint in font['cmap'] for codepoint in codetc):
                stword.append((s, t))
    if len(stword) + len(font['glyph_order']) > 65535:
        nd=len(stword) + len(font['glyph_order']) - 65535
        raise RuntimeError('Not enough glyph space! You need ' + str(nd) + ' more glyph space!')
    if len(stword) > 0:
        addlookupword(stword)

def addlookupword(stword):
    stword.sort(key=lambda x:len(x[0]), reverse = True)
    subtablesl = list()
    subtablesm = list()
    i, j = 0, 0
    sbs = list()
    sbt = dict()
    wlen = len(stword[0][0])
    while True:
        wds = list()
        wdt = list()
        for s1 in stword[i][0]:
            wds.append(font['cmap'][str(ord(s1))])
        for t1 in stword[i][1]:
            wdt.append(font['cmap'][str(ord(t1))])
        newgname = 'ligast' + str(i)
        font['glyf'][newgname] = {
                                    'advanceWidth': 0, 
                                    'advanceHeight': 1000, 
                                    'verticalOrigin': 880
                                 }
        font['glyph_order'].append(newgname)
        sbs.append({'from': wds, 'to': newgname})
        sbt[newgname] = wdt
        if i >= len(stword) - 1:
            subtablesl.append({'substitutions': sbs})
            subtablesm.append(sbt)
            break
        j += len(stword[i][0] + stword[i][1])
        wlen2 = len(stword[i + 1][0])
        if j >= 20000 or wlen2 < wlen:
            j = 0
            wlen = wlen2
            subtablesl.append({'substitutions': sbs})
            subtablesm.append(sbt)
            sbs = list()
            sbt = dict()
        i += 1
    font['GSUB']['lookups']['wordsc'] = {
                                            'type': 'gsub_ligature',
                                            'flags': {},
                                            'subtables': subtablesl
                                        }
    font['GSUB']['lookups']['wordtc'] = {
                                            'type': 'gsub_multiple',
                                            'flags': {},
                                            'subtables': subtablesm
                                        }

def setinfo():
    font['OS_2']['achVendID']=fontid
    font['head']['fontRevision']=float(fontver)
    nname=list()
    for nj in font['name']:
        if nj['languageID']==2052:
            ns=dict(nj)
            nt=dict(nj)
            nh=dict(nj)
            ns['languageID']=2052
            ns['nameString']=ns['nameString'].replace('思源宋体', '小合简化体 宋体').replace('思源黑体', '小合简化体 黑体').replace('思源等宽', '小合简化体 等宽')
            nt['languageID']=1028
            nt['nameString']=nt['nameString'].replace('思源宋体', '小合简化体 宋体').replace('思源黑体', '小合简化体 黑体').replace('思源等宽', '小合简化体 等宽')
            nh['languageID']=3076
            nh['nameString']=nh['nameString'].replace('思源宋体', '小合简化体 宋体').replace('思源黑体', '小合简化体 黑体').replace('思源等宽', '小合简化体 等宽')
            nname.append(ns)
            nname.append(nt)
            nname.append(nh)
        #elif nj['nameID']>0 and nj['nameID']<7:
        elif nj['nameID']==3:
            ne=dict(nj)
            ne['nameString']=fontver+';'+fontid+';'+ne['nameString'].split(';')[2].replace('SourceHanSansSC', 'XiaoheSimplifySans').replace('SourceHanSerifSC', 'XiaoheSimplifySerif')
            nname.append(ne)
        elif nj['nameID']==5:
            ne=dict(nj)
            ne['nameString']='Version '+fontver
            nname.append(ne)
        elif nj['nameID']==11:
            ne=dict(nj)
            ne['nameString']='https://github.com/GuiWonder/XiaoheSimplifyFonts'
            nname.append(ne)
        elif nj['nameID']!=0 and nj['nameID']!=7 and nj['nameID']!=8:
        #else:
            ne=dict(nj)
            ne['nameString']=ne['nameString'].replace('Source Han Sans SC', 'Xiaohe Simplify Sans').replace('SourceHanSansSC', 'XiaoheSimplifySans').replace('Source Han Serif SC', 'Xiaohe Simplify Serif').replace('SourceHanSerifSC', 'XiaoheSimplifySerif')
            nname.append(ne)
    font['name']=nname
    if 'CFF_' in font:
        font['CFF_']['notice']=''
        font['CFF_']['fontName']=font['CFF_']['fontName'].replace('SourceHanSansSC', 'XiaoheSimplifySans').replace('SourceHanSerifSC', 'XiaoheSimplifySerif')
        font['CFF_']['fullName']=font['CFF_']['fullName'].replace('Source Han Sans Simplified Chinese', 'Xiaohe Simplify Sans').replace('Source Han Serif Simplified Chinese', 'Xiaohe Simplify Serif')
        font['CFF_']['familyName']=font['CFF_']['familyName'].replace('Source Han Sans Simplified Chinese', 'Xiaohe Simplify Sans').replace('Source Han Serif Simplified Chinese', 'Xiaohe Simplify Serif')
        if 'fdArray' in font['CFF_']:
            nfd=dict()
            for k in font['CFF_']['fdArray'].keys():
                nfd[k.replace('SourceHanSansSC', 'XiaoheSimplifySans').replace('SourceHanSerifSC', 'XiaoheSimplifySerif')]=font['CFF_']['fdArray'][k]
            font['CFF_']['fdArray']=nfd
            for gl in font['glyf'].values():
                if 'CFF_fdSelect' in gl:
                    gl['CFF_fdSelect']=gl['CFF_fdSelect'].replace('SourceHanSansSC', 'XiaoheSimplifySans').replace('SourceHanSerifSC', 'XiaoheSimplifySerif')

def rmglyph():
    usedg=set()
    for k in font['cmap_uvs'].keys():
        c, v=k.split(' ')
        if c in font['cmap']:
            usedg.add(font['cmap_uvs'][k])
    usedg.update(font['cmap'].values())
    
    print('Getting locl glyghs lists...')
    loc=set()
    for lang in font['GSUB']['languages'].keys():
        for fs in font['GSUB']['languages'][lang]['features']:
            if fs.split('_')[0]=='locl':
                loc.update(set(font['GSUB']['features'][fs]))
    for subs in loc:
        ftype=font['GSUB']['lookups'][subs]['type']
        for subtable in font['GSUB']['lookups'][subs]['subtables']:
            for j, t in list(subtable.items()):
                if ftype=='gsub_single':
                    unu.add(t)
                    unu.add(j)
        del font['GSUB']['lookups'][subs]
        f1todel = set()
        for f1 in font['GSUB']['features'].keys():
            if subs in font['GSUB']['features'][f1]:
                font['GSUB']['features'][f1].remove(subs)
            if len(font['GSUB']['features'][f1]) == 0:
                f1todel.add(f1)
                continue
        for  f1 in f1todel:
            del font['GSUB']['features'][f1]

    print('Removing glyghs...')
    lpuse=set()
    if 'GSUB' in font:
        for lookup in font['GSUB']['lookups'].values():
            if lookup['type'] == 'gsub_single':
                for subtable in lookup['subtables']:
                    for g1, g2 in list(subtable.items()):
                        if g1 in usedg:
                            lpuse.add(g1)
                            lpuse.add(g2)
            elif lookup['type'] == 'gsub_alternate':
                for subtable in lookup['subtables']:
                    for item in set(subtable.keys()):
                        if item in usedg:
                            lpuse.add(item)
                            lpuse.update(set(subtable[item]))
            elif lookup['type'] == 'gsub_ligature': 
                for subtable in lookup['subtables']:
                    for item in subtable['substitutions']:
                        if set(item['from']).issubset(usedg):
                            lpuse.update(set(item['from']))
                            lpuse.add(item['to'])
            elif lookup['type'] == 'gsub_chaining':
                for subtable in lookup['subtables']:
                    for ls in subtable['match']:
                        for l1 in ls:
                            lpuse.update(set(l1))

    unusegl=set()
    unusegl.update(set(font['glyph_order']))
    notg={'.notdef', '.null', 'nonmarkingreturn', 'NULL', 'NUL'}
    unusegl.difference_update(notg)
    unusegl.difference_update(usedg)
    unusegl.difference_update(lpuse)
    for ugl in unusegl:
        font['glyph_order'].remove(ugl)
        del font['glyf'][ugl]
    print('Checking Lookup tables...')
    if 'GSUB' in font:
        for lookup in font['GSUB']['lookups'].values():
            if lookup['type'] == 'gsub_single':
                for subtable in lookup['subtables']:
                    for g1, g2 in list(subtable.items()):
                        if g1 in unusegl or g2 in unusegl:
                            del subtable[g1]
            elif lookup['type'] == 'gsub_alternate':
                for subtable in lookup['subtables']:
                    for item in set(subtable.keys()):
                        if item in unusegl or len(set(subtable[item]).intersection(unusegl))>0:
                            del subtable[item]
            elif lookup['type'] == 'gsub_ligature': 
                for subtable in lookup['subtables']:
                    s1=list()
                    for item in subtable['substitutions']:
                        if item['to'] not in unusegl and len(set(item['from']).intersection(unusegl))<1:
                            s1.append(item)
                    subtable['substitutions']=s1
            elif lookup['type'] == 'gsub_chaining':
                for subtable in lookup['subtables']:
                    for ls in subtable['match']:
                        for l1 in ls:
                            l1=list(set(l1).difference(unusegl))
    if 'GPOS' in font:
        for lookup in font['GPOS']['lookups'].values():
            if lookup['type'] == 'gpos_single':
                for subtable in lookup['subtables']:
                    for item in list(subtable.keys()):
                        if item in unusegl:
                            del subtable[item]
            elif lookup['type'] == 'gpos_pair':
                for subtable in lookup['subtables']:
                    for item in list(subtable['first'].keys()):
                        if item in unusegl:
                            del subtable['first'][item]
                    for item in list(subtable['second'].keys()):
                        if item in unusegl:
                            del subtable['second'][item]
            elif lookup['type'] == 'gpos_mark_to_base':
                nsb=list()
                for subtable in lookup['subtables']:
                    gs=set(subtable['marks'].keys()).union(set(subtable['bases'].keys()))
                    if len(gs.intersection(unusegl))<1:
                        nsb.append(subtable)
                lookup['subtables']=nsb

if len(sys.argv) > 2:
    print('====Start Build XiaoheSimplify Fonts====\n')
    print('Loading font...')
    fin = sys.argv[1]
    font = json.loads(subprocess.check_output((otfccdump, '--no-bom', fin)).decode("utf-8", "ignore"))
    unu=set()
    print('Adding variants...')
    addvariants()
    print('Transforming codes...')
    transforme()
    print('Removing glyghs...')
    rmglyph()
    print('Checking GSUB...')
    print('Checking variants...')
    addvariants()
    print('Building lookup table...')
    lookuptable()
    print('Setting font info...')
    setinfo()
    print('Generating font...')
    tmpfile = tempfile.mktemp('.json')
    with open(tmpfile, 'w', encoding='utf-8') as f:
        f.write(json.dumps(font))
    del font
    for x in set(locals().keys()):
        if x not in ('os', 'subprocess', 'otfccbuild', 'sys', 'tmpfile', 'gc'):
            del locals()[x]
    gc.collect()
    print('Creating font file...')
    subprocess.run((otfccbuild, '--keep-modified-time', '--keep-average-char-width', '-O3', '-q', '-o', sys.argv[2], tmpfile))
    os.remove(tmpfile)
    print('Finished!')
