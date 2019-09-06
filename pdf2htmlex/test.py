from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time

exePath = 'D:/pdf2htmlex/pdf2htmlEX.exe'
exeAbsPath = os.path.abspath(exePath)

def getChrome():
	"""打开chrome

	:return: 返回chrome
	"""
	chrome_options = Options()

	#无头浏览器
	chrome_options.add_argument('--headless')
	chrome = webdriver.Chrome(chrome_options=chrome_options)

	#有头浏览器
	chrome = webdriver.Chrome()
	return chrome

def pdf2html(title):
	#pdf文件地址
	pdfPath = './pdf/' + title + '.pdf'

	#输出目录
	destPath = './testOutput/{0}'.format(title)
	if not os.path.exists(destPath):
		os.makedirs(destPath)

	#执行pdf2htmlEX.exe
	command = '{0} --embed-image 0  --dest-dir "./{1}" --optimize-text 1 "{2}"'.format(exeAbsPath, destPath, pdfPath)
	# print(command)
	os.system(command)

	#html2txt
	htmlPath = './testOutput/{0}/{0}.html'.format(title)
	textPath = './testOutput/{0}/{0}.txt'.format(title)
	chrome = getChrome()
	chrome.get(os.path.abspath(htmlPath))
	body = chrome.find_element_by_xpath('//body/div[@id="page-container"]')
	texts = body.find_elements_by_xpath('./div')
	print(len(texts))
	with open(textPath, 'a', encoding='utf-8') as f:
		for i in range(0, len(texts)):
			script = 'document.getElementById("page-container").children[{0}].scrollIntoView()'.format(i)
			time.sleep(1)
			chrome.execute_script(script)
			print(texts[i].text)
			f.write(texts[i].text)

if __name__ == '__main__':
	title = 'A faster optimal register allocator'
	# title = 'A quantitative framework for automated pre-execution thread selection'
	# title = 'Characterizing and predicting value degree of use'
	pdf2html(title)