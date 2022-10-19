import os
from shutil import copy
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
	os.system(f'wget -P src {u1} || exit 1') 
aa=('XiaoheSimplifySans', 'XiaoheSimplifySerif')
for fod in aa:
	os.makedirs(f'./fonts/{fod}')
	os.makedirs(f'./fonts/{fod}SC')
	copy('./LICENSE.txt', f'./fonts/{fod}/')
	copy('./LICENSE.txt', f'./fonts/{fod}SC/')

tocl='python3 ./main/simplify.py'
for item in os.listdir('./src'):
	if item.lower().split('.')[-1] in ('otf', 'ttf'):
		aan=item.replace('SourceHanSansSC', aa[0]).replace('SourceHanSerifSC', aa[1])
		os.system(f"{tocl} ./src/{item} ./fonts/{aan.split('-')[0]}/{aan}") 
os.system(f'7z a ./XiaoheSimplifySans.7z ./fonts/XiaoheSimplifySans/*') 
os.system(f'7z a ./XiaoheSimplifySerif.7z ./fonts/XiaoheSimplifySerif/*') 
rmtree('./src')
rmtree('./fonts')
