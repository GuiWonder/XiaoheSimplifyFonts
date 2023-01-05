import os, json, threading
from shutil import copy, rmtree
shurl=[
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Bold.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-ExtraLight.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Heavy.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Light.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Medium.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Normal.otf", 
	"https://github.com/adobe-fonts/source-han-sans/raw/release/OTF/SimplifiedChinese/SourceHanSansSC-Regular.otf", 
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-Bold.otf",
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-ExtraLight.otf",
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-Heavy.otf",
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-Light.otf", 
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-Medium.otf", 
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-Regular.otf", 
	"https://github.com/adobe-fonts/source-han-serif/raw/release/OTF/SimplifiedChinese/SourceHanSerifSC-SemiBold.otf"
]
os.makedirs('./src')
for u1 in shurl:
	os.system(f'wget -P src {u1}') 

os.makedirs('./ttfs')
def tottf(stl):
	for item in os.listdir('./src'):
		if stl in item and item.lower().split('.')[-1]=='otf':
			ttfout=item.split('.')[0]+'.ttf'
			os.system(f'otf2ttf -o ./ttfs/{ttfout} ./src/{item}')

thsans=threading.Thread(target=tottf, args=('Sans', ))
thserif=threading.Thread(target=tottf, args=('Serif', ))
thserif.start()
thsans.start()
thserif.join()
thsans.join()

cfg=json.load(open(os.path.join(os.path.abspath(os.path.dirname(__file__)), './main/config.json'), 'r', encoding = 'utf-8'))
fnm=cfg['fontName'].replace(' ', '')
aa=(f'{fnm}Sans', f'{fnm}Serif')
for fod in aa:
	os.makedirs(f'./fonts/{fod}')
	copy('./LICENSE.txt', f'./fonts/{fod}/')

tosp='python3 ./main/simplify.py'
for item in os.listdir('./ttfs'):
	if item.lower().split('.')[-1] in ('otf', 'ttf'):
		aan=item.replace('SourceHanSansSC', aa[0]).replace('SourceHanSerifSC', aa[1])
		os.system(f"{tosp} ./ttfs/{item} ./fonts/{aan.split('-')[0]}/{aan}") 
os.system(f'7z a ./{fnm}Sans.7z ./fonts/{fnm}Sans/*') 
os.system(f'7z a ./{fnm}Serif.7z ./fonts/{fnm}Serif/*') 
rmtree('./src')
rmtree('./ttfs')
rmtree('./fonts')
