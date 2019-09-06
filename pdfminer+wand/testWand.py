from wand.image import Image
from wand.drawing import Drawing
from wand.color import Color
from wand.display import display
import os

IMAGECOLOR = 'red'
RECTCOLOR = 'green'
FIGURECOLOR = 'blue'
TEXTCOLOR = 'yellow'
CURVECOLOR = 'pink'
LINECOLOR = 'brown'

LTTYPE2COLOR = {
	'LTImage': IMAGECOLOR,
	'LTRect': RECTCOLOR,
	'LTFigure': FIGURECOLOR,
	'LTText': TEXTCOLOR,
	'LTCurve': CURVECOLOR,
	'LTLine': LINECOLOR,
}

def pdf2jpg(filename, outputFolder):
	image_pdf = Image(filename=filename,resolution=300)
	image_jpeg = image_pdf.convert('jpg')
	# wand已经将PDF中所有的独立页面都转成了独立的二进制图像对象。我们可以遍历这个大对象，并把它们加入到req_image序列中去。
	req_image = []
	for img in image_jpeg.sequence:
		img_page = Image(image=img)
		# print(img_page.size)
		req_image.append(img_page.make_blob('jpg'))

	#若输出文件夹不存在则创建
	if not os.path.exists(outputFolder):
		os.makedirs(outputFolder)

	# 遍历req_image,保存为图片文件
	i = 0
	for img in req_image:
		ff = open('{0}/{1}.jpg'.format(outputFolder, i),'wb')
		ff.write(img)
		ff.close()
		i += 1

def draw(img, LtBbox, strokeColor='black', width=2):
	x0, y0, x1, y1 = LtBbox[0 : 4]
	print(LtBbox)
	with Drawing() as draw:
		draw.stroke_color = Color(strokeColor)
		draw.stroke_width = width
		draw.fill_color=Color('transparent')
		draw.rectangle(x0, y0, x1, y1)
		draw.draw(img)

def crop(img, LtBbox):
	x0, y0, x1, y1 = LtBbox[0 : 4]
	img.crop(int(x0), int(y0), int(x1), int(y1))

def doOnImage(filePath, LtBbox, pageSize, rotate=0, LTType='LtRect', width=2, outputPath='temp.jpg'):
	x0, y0, x1, y1 = LtBbox[0 : 4]
	strokeColor = LTTYPE2COLOR[LTType]
	# print(rotate)
	with Image(filename=filePath) as img:
		#从原来pdf坐标到图片坐标的缩放
		x0, x1 = [x * img.width / pageSize[0] for x in [x0, x1]]
		y0, y1 = [y * img.height / pageSize[1] for y in [pageSize[1] - y1, pageSize[1] - y0]]
		# img.rotate(rotate)

		draw(img, [x0, y0, x1, y1], strokeColor, width)

		# img.rotate(-rotate)
		# display(img)
		img.save(filename=filePath)


if __name__ == '__main__':
	# title = 'A faster optimal register allocator'
	title = 'Characterizing and predicting value degree of use'
	# title = 'A quantitative framework for automated pre-execution thread selection'

	filename = 'pdf/{0}.pdf'.format(title)
	outputFolder = 'testWand/{0}'.format(title)
	# pdf2jpg(filename, outputFolder)
	doOnImage('{0}/0.jpg'.format(outputFolder), LtBbox=(153.700,680.632,458.290,696.774), pageSize=[612, 792], LTType='LTText')