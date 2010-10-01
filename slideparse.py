#!/usr/bin/python

# 
#  slideparse.py
#  <slide donwloader>
#  
#  Created by zhili hu on 2010-09-28.
#  Copyright 2010 . All rights reserved.
#  huzhili@gmail.com

import sys
import urllib
from sgmllib import SGMLParser
from urlparse import urlparse
from xml.etree.ElementTree import parse
import os
import gfx
from reportlab.pdfgen import canvas 
from reportlab.lib.pagesizes import portrait,A4
import urllib2
import re
import zlib
from reportlab.lib.utils import ImageReader
from PIL import Image

def parseDocFileNameFromSlideshare(fileurl='http://www.slideshare.net/sonia_ai/facebook-twitter-email'): 
	docName = ''
	usock = urllib.urlopen(fileurl)

	class URLLister(SGMLParser):
	    def reset(self):                              
	        SGMLParser.reset(self)
	        self.urls = []

	    def start_link(self, attrs):    #start with <link ..> tab                 
	        href = [v for k, v in attrs if k=='href']  
	        if href:
	            self.urls.extend(href)
	parser = URLLister()
	parser.feed(usock.read())         
	usock.close()                     
	parser.close()


	for url in parser.urls:
		o = urlparse(url)
		com = o.query.split("&")
		for c in com:
			if len(c.split("=")) == 2 and c.split("=")[0]== 'doc':
				docName = c.split("=")[1]
	return docName



def parseAndSaveSwfFilesFromSlideshare(fileName):
	localswfs = []
	swflist_url = "http://cdn.slidesharecdn.com/%s.xml" % fileName
	rss = parse(urllib.urlopen(swflist_url)).getroot()
	num_slide=1
	for element in rss.findall('Slide'):
		# print element.attrib['Src']
		localSwfName = "%s-%d.swf" % (fileName,num_slide)
		print "retriving file: %s..." % localSwfName
		try :
			urllib.urlretrieve (element.attrib['Src'], localSwfName)
		except (OSError, IOError) as e: 
			print e
			continue
		localswfs.append(localSwfName)
		num_slide+=1;
	return localswfs

def parseAndSaveSwfFilesFromBaidu(fileId ='c9dd8b254b35eefdc8d33309'):
	localSwfs = []
	tempSwfFiles = []
	tempFileNum = 1
	print "http://ai.wenku.baidu.com/play/%s?pn=1&rn=5" % fileId
	req = urllib2.Request("http://ai.wenku.baidu.com/play/%s?pn=1&rn=5" % fileId)
	response = urllib2.urlopen(req)
	# pageinfo = response.read(106)
	swfdata = response.read()
	pageinfo = swfdata.split("CWS")[0].rstrip()
	local_file = open("temp%d" % tempFileNum, "wb")
	local_file.write(swfdata)
	local_file.close()
	tempSwfFiles.append("temp%d" % tempFileNum)
	tempFileNum += 1
	regex = re.compile(r'^{("\w+"):("\d+"),("\w+"):("\d+"),("\w+"):("\d+")}$')

	match = regex.search(pageinfo)
	pageinfo_dict = {eval(match.group(1)):eval(match.group(2)),
				eval(match.group(3)):eval(match.group(4)),
				eval(match.group(5)):eval(match.group(6))}
	# print pageinfo_dict
	remain_pages = int(pageinfo_dict['totalPage']) - 5
	pn = 1
	print 'downloading...'
	while (remain_pages > 0):
		pn += 5
		if remain_pages > 5:
			rn = 5
		else:
			rn = remain_pages
		req = urllib2.Request('http://ai.wenku.baidu.com/play/%s?pn=%d&rn=%d' % (fileId,pn,rn))
		response = urllib2.urlopen(req)
		# pageinfo = response.read(106)
		swfdata = response.read()
		remain_pages -= rn
		local_file = open("temp%d" % tempFileNum, "wb")
		local_file.write(swfdata)
		local_file.close()
		tempSwfFiles.append("temp%d" % tempFileNum)
		tempFileNum += 1

	print 'spliting...'
	for iswf in tempSwfFiles:
		f = open(iswf, 'rb')
		contents = f.read()
		count = 1
		start = contents.find('CWS')
		if start < 0:
		    print 'not a swf file'
		end = start
		while 1:
		    # This is swf part of swf head after v.6.
		    # baidu's flash version is 09 and 0x43 0x57 0x53 is standing
		    # for CWS, compressed swf.
		        #end = start+1
		    # print  contents[start:start+4].encode('hex') 
			ft = open('%s-%d.swf' % (iswf,count), 'wb')
			end = contents.find('CWS', end+1)
			if end < 0:
				ft.write(contents[start:])
				localSwfs.append('%s-%d.swf' % (iswf,count))
				ft.close()
				break
			if contents[end:end+4].encode('hex') != '43575309':
				continue 
			ft.write(contents[start:end])
			localSwfs.append('%s-%d.swf' % (iswf,count))
			count += 1
			ft.close()
			start = end
		f.close()
		os.remove(iswf)
	return localSwfs
	
def parseDocFileNameFromBaidu(fileUrl='http://wendang.baidu.com/view/c9dd8b254b35eefdc8d33309.html'):
	"""docstring for parseDocFileNameFromBaidu"""
	docId = ''
	o = urlparse(fileUrl)
	docId = o.path.split('/')[2][:-5]
	return docId

def mhtonl(v):
	seq = []
	c = 0
	while v > 0:
		d = v & 0xff
		v >>= 8
		seq.append('%c'%d)
		c+=1
	while (4-c) > 0:
	    seq.append('%c' % 0)
	    c+=1
	return ''.join(seq) 

def reverseInBytes(content):
    seq = [] 
    l = len(content)
    #print l
    while(l > 0):
        seq.append(content[l-1])
        l -= 1
    rev = ''.join(seq)
    return int (rev.encode('hex'), 16)
	
chunk = 4
swfSignature = '\x46\x57\x53\x09'
		
def parseAndSaveSwfFilesFromDocin(fileUrl = 'http://www.docin.com/p-35443942.html'):
	localSwfs = []
	docSegNum = 2
	docId = 0
	docTitle = 'empty'
	req = urllib2.Request(fileUrl)
	response = urllib2.urlopen(req)
	for line in response.readlines():
		if line.strip().startswith('var playcontent'):
			for seg in line[1:].split(','):
				if seg.split(':')[0] == '"pageNum"':
					docSegNum = int(seg.split(':')[1][1:2])
				if seg.split(':')[0] == '"pdtTitle"':
					docTitle = seg.split(':')[1][2:-2]
		if line.strip().startswith('fo.addVariable') and 'productId' in line.strip():
			docId = line.strip().split(",")[1][:-2]
	docNum = 1
	while docNum <= docSegNum:
		tempSwfName = "%d-docin" % docNum
		print "retriving file: %s..." % tempSwfName
		try :
			if docNum == 1:
				urllib.urlretrieve ('http://file1.yimk.com/docin_%s.docin' % docId, tempSwfName)
			else:
				urllib.urlretrieve ('http://file1.yimk.com/docin_%s_%d.docin' % (docId,docNum), tempSwfName)
		except (OSError, IOError) as e: 
			print e
			continue
		docNum+=1
	
	pageCount = 0	
	for ii in range(1, docSegNum+1):
		currentIndex = 0
		f = open('%d-docin' % ii, 'rb')
		width = reverseInBytes(f.read(chunk))
		currentIndex += chunk
		print width
		height = reverseInBytes(f.read(chunk))
		currentIndex += chunk
		print height
		totalPages = reverseInBytes(f.read(chunk))
		currentIndex += chunk
		print totalPages
		headerLen = reverseInBytes(f.read(chunk))
		currentIndex += chunk
		print headerLen 
		print currentIndex
		headerContent = zlib.decompress(f.read(headerLen))
		currentIndex += headerLen

		while 1:
		    lenBuffer = f.read(chunk)
		    if lenBuffer == '':
		        break
		    swfContentLen = reverseInBytes(lenBuffer)    
		    #print swfContentLen
		    swfContent = zlib.decompress(f.read(swfContentLen))
		    pageCount += 1
		    fileLen = mhtonl(len(headerContent+swfContent) + 8)
		    fp = open('my_%d.swf' % pageCount, 'wb')
		    fp.write(swfSignature+fileLen+headerContent+swfContent)
		    fp.close()
		    currentIndex += swfContentLen
		    localSwfs.append('my_%d.swf' % pageCount)
		f.close()
		os.remove('%d-docin' % ii)
	return docTitle, localSwfs
# fileName = parseDocFileNameFromSlideshare()
# swfslides = parseAndSaveSwfFilesFromSlideshare(fileName)
#fileName = parseDocFileNameFromBaidu('http://wendang.baidu.com/view/c9dd8b254b35eefdc8d33309.html')
#swfslides = parseAndSaveSwfFilesFromBaidu(fileName)
#fileName, swfslides = parseAndSaveSwfFilesFromDocin('http://www.docin.com/p-61946408.html')
# print swfslides

def convertImageToPDF(_fileName, _swfslides, isDocin):
	print "convecting files to pdf..."
	pdfCanvas = canvas.Canvas('%s.pdf' % _fileName, pagesize=portrait(A4))
	pdfCanvas.drawString(150,700,"Welcome to flash slides downloader");
	pdfCanvas.drawString(180,680,"contact: huzhili@gmail.com");
	pdfCanvas.showPage()
	numberOfSlides = 1
	for iswf in _swfslides:
		doc = gfx.open("swf", iswf)
		print iswf
		if doc:
			if isDocin == False:		
				for pagenr in range(1,doc.pages+1): 
					page1 = doc.getPage(pagenr) 
					print "Page", pagenr, "has dimensions", page1.width, "x", page1.height
					pdfCanvas.setPageSize((page1.width*2, page1.height*2))
					imageName = 'image-%s-%s.png'%(numberOfSlides, pagenr)
					imgRGBBuf = page1.asImage(page1.width*2, page1.height*2)
					im = Image.fromstring("RGB", (page1.width*2,page1.height*2), imgRGBBuf) # convert to PIL Object
					# img = gfx.ImageList()
					# 				img.setparameter("antialise", "4") # turn on antialisin
					# img.setparameter("zoom", "100")
					# img.startpage(page1.width,page1.height) 
					# 				page1.render(img)
					# 				img.endpage()
					# pageNumOfThisSwf+=1"thumbnail%s.png" % pagenr
					# img.save(imageName)
					# pdfCanvas.drawImage(imageName,0,0,width= page1.width,height= page1.height,mask='auto') 
					pdfCanvas.drawImage(ImageReader(im),0,0,width=page1.width*2,height=page1.height*2,mask='auto') 
					pdfCanvas.showPage()
					# os.remove(imageName) # delete temp image
			else:
				# damn docins bad header.
				page1 = doc.getPage(1) 
				print "Page %d" % numberOfSlides, "has dimensions", page1.width, "x", page1.height
				pdfCanvas.setPageSize((page1.width*2, page1.height*2))
				imageName = 'image-%s-%s.png'%(numberOfSlides, 1)
				imgRGBBuf = page1.asImage(page1.width*2, page1.height*2)
				im = Image.fromstring("RGB", (page1.width*2,page1.height*2), imgRGBBuf) # convert to PIL Object
				# img = gfx.ImageList()
				# img.setparameter("antialise", "4") # turn on antialisin
				# img.setparameter("zoom", "100")
				# img.startpage(page1.width,page1.height) 
				# page1.render(img)
				# img.endpage()
				# pageNumOfThisSwf+=1"thumbnail%s.png" % pagenr
				# img.save(imageName)
				# pdfCanvas.drawImage(imageName,0,0,width= page1.width,height= page1.height,mask='auto') 
				pdfCanvas.drawImage(ImageReader(im),0,0,width=page1.width*2,height=page1.height*2,mask='auto') 
				pdfCanvas.showPage()
				# os.remove(imageName) # delete temp image
		numberOfSlides += 1
		os.remove(iswf) # delete temp swf
	pdfCanvas.save()
# print 'cleaning up'
# convertImageToPDF(fileName, swfslides, True)
def main(argv=None):
  if argv is None or len(argv) != 3:
      print >> sys.stderr, "slidepasrse -[s:b:d] url"
      return 1
  fileUrl = ''
  swfslides = []
  fileName = 'empty'
  if argv[1] == '-s':
    fileName = parseDocFileNameFromSlideshare(argv[2])
    swfslides = parseAndSaveSwfFilesFromSlideshare(fileName)
    convertImageToPDF(fileName, swfslides, False)
  if argv[1] == '-b':
    fileName = parseDocFileNameFromBaidu(argv[2])
    swfslides = parseAndSaveSwfFilesFromBaidu(fileName)
    convertImageToPDF(fileName, swfslides, False)
  if argv[1] == '-d':
    fileName, swfslides = parseAndSaveSwfFilesFromDocin(argv[2])
    convertImageToPDF(fileName, swfslides, True)
  print 'done'
  return 0

if __name__ == "__main__":
  sys.exit(main(sys.argv))
