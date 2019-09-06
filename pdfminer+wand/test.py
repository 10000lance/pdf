#!/usr/bin/python

import sys
import os
from binascii import b2a_hex
import time

from pdfminer.pdfparser import PDFParser, PDFDocument, PDFNoOutlines
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import *

from testWand import pdf2jpg, doOnImage

def parseToc (doc):
	'''
	
	:param doc:     解析后的文档 
	:return:        返回pdf目录
	'''
	toc = []
	try:
		outlines = doc.get_outlines()
		for (level,title,dest,a,se) in outlines:
			toc.append( (level, title) )
	except PDFNoOutlines:
		pass
	return toc

def writeFile (imgFolderPath, filename, filedata, flags='w'):
	'''
	
	:param imgFolderPath:   写入目录
	:param filename:        写入文件名
	:param filedata:        写入数据
	:param flags:           写入模式 w\wb\a
	:return: 
	'''
	result = False
	if not os.path.isdir(imgFolderPath):
		os.makedirs(imgFolderPath)

	try:
		file_obj = open(os.path.join(imgFolderPath, filename), flags)
		file_obj.write(filedata)
		file_obj.close()
		result = True
	except IOError:
		pass
	return result

def getImageType (streamFirst4Bytes):
	'''
	
	:param streamFirst4Bytes:   图片字节流的前四位 
	:return:        返回图片类型
	'''
	fileType = None
	# print(streamFirst4Bytes)
	bytesHEX = b2a_hex(streamFirst4Bytes)
	# print(bytesHEX)
	print()
	# print(type(b'ffd8'))
	if bytesHEX.startswith(b'ffd8'):
		fileType = '.jpeg'
	elif bytesHEX == '89504e47':
		fileType = '.png'
	elif bytesHEX == '47494638':
		fileType = '.gif'
	elif bytesHEX.startswith(b'424d'):
		fileType = '.bmp'
	# else:
	# 	fileType = '.jpeg'
	return fileType
	# return '.jpg'

def saveImage (ltImage, pageNumber, imgFolderPath):
	'''
		
	:param ltImage:     Image对象 
	:param pageNumber:  当前解析文档页数
	:param imgFolderPath:   保存图片的目录
	:return:    
	'''
	result = None
	# print(ltImage)
	# print(ltImage.stream.data)
	# print(ltImage.stream.rawdata)
	# print(ltImage.srcsize)
	# print(ltImage.imagemask)
	# print(ltImage.bits)
	# print(ltImage.colorspace)
	# print([hex(x) for x in bytearray(ltImage.stream.get_rawdata())])
	if ltImage.stream:
		fileStream = ltImage.stream.get_rawdata()
		# print(fileStream)
		if fileStream:
			file_ext = getImageType(fileStream[0 : 4])
			if file_ext:
				# print(ltImage)
				file_name = ''.join([str(pageNumber), '_', ltImage.name, file_ext])
				if writeFile(imgFolderPath, file_name, fileStream, flags='wb'):
					result = file_name
	return result

def to_bytestring (s, enc='utf-8'):
	"""Convert the given unicode string to a bytestring, using the standard encoding,
	unless it's already a bytestring"""
	if s:
		if isinstance(s, str):
			return s
		else:
			return s.encode(enc)

def update_page_text_hash (h, ltObj, pct=0.2):
	"""Use the bbox x0,x1 values within pct% to produce lists of associated text within the hash"""

	x0 = ltObj.bbox[0]
	x1 = ltObj.bbox[2]

	key_found = False
	for k, v in h.items():
		hash_x0 = k[0]
		if x0 >= (hash_x0 * (1.0-pct)) and (hash_x0 * (1.0+pct)) >= x0:
			hash_x1 = k[1]
			if x1 >= (hash_x1 * (1.0-pct)) and (hash_x1 * (1.0+pct)) >= x1:
				# the text inside this LT* object was positioned at the same
				# width as a prior series of text, so it belongs together
				key_found = True
				v.append(to_bytestring(ltObj.get_text()))
				h[k] = v
	if not key_found:
		# the text, based on width, is a new series,
		# so it gets its own series (entry in the hash)
		h[(x0,x1)] = [to_bytestring(ltObj.get_text())]

	return h

def parseLTObjs (ltObjs, pageNumber, imgFolderPath, text=None, saveImgs=False):
	'''解析LT*对象

	:param ltObjs:
	:param pageNumber:
	:param imgFolderPath:
	:param text:
	:param saveImgs:
	:return:
	'''

	if text is None:
		text = []

	page_text = {} # k=(x0, x1) of the bbox, v=list of text strings within that bbox width (physical column)
	for ltObj in ltObjs:
		# print(ltObj)
		# print(ltObj.bbox)
		# print(type(ltObj.bbox ))
		if isinstance(ltObj, LTTextBox) or isinstance(ltObj, LTTextLine):
			# text, so arrange is logically based on its column width
			page_text = update_page_text_hash(page_text, ltObj)
		elif isinstance(ltObj, LTImage):
			# an image, so save it to the designated imgFolderPath, and note its place in the text
			if saveImgs:
				saved_file = saveImage(ltObj, pageNumber, imgFolderPath)
				# if saved_file:
					# use html style <img /> tag to mark the position of the image within the text
					# text.append('<img src="'+os.path.join(imgFolderPath, saved_file)+'" />')
				# else:
					# print(sys.stderr, "error saving image on page", pageNumber, ltObj.__repr__)
		elif isinstance(ltObj, LTFigure):
			# LTFigure objects are containers for other LT* objects, so recurse through the children
			text.append(parseLTObjs(ltObj, pageNumber, imgFolderPath, text, saveImgs=saveImgs))

	for k, v in sorted([(key,value) for (key,value) in page_text.items()]):
		# sort the page_text hash by the keys (x0,x1 values of the bbox),
		# which produces a top-down, left-to-right sequence of related columns
		text.append(''.join(v))

	return '\n'.join(text)

def doOnObjs(ltObjs, imgFolderPath, pageNum, pageSize, rotate):
	'''处理LT对象

	:param ltObjs:
	:param imgFolderPath:
	:param pageNum:
	:param pageSize:
	:param rotate:
	:return:
	'''
	filePath = '{0}/{1}.jpg'.format(imgFolderPath, pageNum)

	for ltObj in ltObjs:
		LTType = None
		LtBbox = ltObj.bbox
		# print(ltObj)
		# print(ltObj.bbox)
		# print(type(ltObj.bbox ))
		if isinstance(ltObj, LTTextBox) or isinstance(ltObj, LTTextLine) or isinstance(ltObj, LTTextBoxHorizontal):
			LTType = 'LTText'
		elif isinstance(ltObj, LTImage):
			LTType = 'LTImage'
		elif isinstance(ltObj, LTFigure):
			LTType = 'LTFigure'
			doOnObjs(ltObj, imgFolderPath, pageNum, pageSize, rotate)
		elif isinstance(ltObj, LTRect):
			LTType = 'LTRect'
		elif isinstance(ltObj, LTCurve):
			LTType = 'LTCurve'
		elif isinstance(ltObj, LTLine):
			LTType = 'LTLine'

		if LTType != None:
			doOnImage(filePath, LtBbox, pageSize, rotate, LTType, outputPath='output/{0}.jpg'.format(pageNum))

def parsePages (doc, imgFolderPath, saveImgs=False):
	''' 解析pdf文档页

	:param doc:
	:param imgFolderPath:
	:param saveImgs:
	:return:
	'''
	rsrcmgr = PDFResourceManager()
	laparams = LAParams()
	device = PDFPageAggregator(rsrcmgr, laparams=laparams)
	interpreter = PDFPageInterpreter(rsrcmgr, device)

	text = []
	i = 0
	#遍历每页
	for page in doc.get_pages():
		x0, y0, x1, y1 = page.mediabox
		pageSize = [x1 - x0, y1 - y0]
		# print(pageSize)
		# print(page.rotate)

		interpreter.process_page(page)
		# receive the LTPage object for this page
		layout = device.get_result()
		# layout is an LTPage object which may contain child objects like LTTextBox, LTFigure, LTImage, etc.
		text.append(parseLTObjs(layout, (i+1), imgFolderPath, saveImgs=saveImgs))
		doOnObjs(layout, imgFolderPath, i, pageSize, page.rotate)
		i += 1
	return text

def parsePDF (pdfPath, pdfPwd='', imgFolderPath='/tmp', saveImgs=False):
	"""Process each of the pages in this pdf file and return a list of strings representing the text found in each page"""
	if not os.path.exists(imgFolderPath):
		os.makedirs(imgFolderPath)

	try:
		#打开pdf文档
		fp = open(pdfPath, 'rb')
		#创建pdf解析器
		parser = PDFParser(fp)
		#创建pdf存储器
		doc = PDFDocument()

		#关联pdf解析器和存储器
		parser.set_document(doc)
		doc.set_parser(parser)

		#初始化
		doc.initialize(pdfPwd)

		if doc.is_extractable:
			#处理pdf文档
			text = parsePages(doc, imgFolderPath, saveImgs=saveImgs)

			with open('{0}/text.txt'.format(imgFolderPath), 'w', encoding='utf-8') as f:
				for line in text:
					f.write(line)
				f.close()

		# close the pdf file
		fp.close()
	except IOError:
		# the file doesn't exist or similar problem
		pass

def parse(title, imgFolderPath, saveImgs=False):
	pdfFolderPath = './pdf'
	# imgFolderBasePath = pdfFolderPath

	pdfPath = os.path.join(pdfFolderPath, title+'.pdf')
	# imgFolderPath = os.path.join(imgFolderBasePath, title)

	parsePDF(pdfPath, imgFolderPath=imgFolderPath, saveImgs=saveImgs)

titles = [
	'A faster optimal register allocator',
	# 'A quantitative framework for automated pre-execution thread selection',
	# 'Characterizing and predicting value degree of use',
	# 'Cherry - checkpointed early resource recycling in out-of-order microprocessors',
]

if __name__ == '__main__':
	for title in titles:
		time1 = time.time()
		filename='pdf/{0}.pdf'.format(title)
		outputFolder = 'testOutput/{0}'.format(title)
		if not os.path.exists(outputFolder):
			os.makedirs(outputFolder)

		pdf2jpg(filename, outputFolder)
		parse(title, outputFolder, True)
		time2 = time.time()
		print("总共消耗时间为:",time2-time1)