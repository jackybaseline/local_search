# -*- coding: utf-8 -*-
import math,sys,os,zipfile
from collections import defaultdict
try:
	from xml.etree.cElementTree import XML
except ImportError:
	from xml.etree.ElementTree import XML

WORD_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
PARA = WORD_NAMESPACE + 'p'
TEXT = WORD_NAMESPACE + 't'
_end = '\0'
doc_max_log=0.0
IDF = lambda k: doc_max_log-math.log10(k)

class Trie:
	def __init__(self):
		self.root=dict()
		self.doc_len=dict()
	def insert(self,word,path):
		current_dict=self.root
		for letter in word:
			current_dict = current_dict.setdefault(letter, {})
		current_dict.setdefault(_end,[])
		current_dict[_end].append(path)
	def search(self,query,rank):
		ans=[]
		for word in query.split(','):
			#print(word)
			current_dict=self.root
			for letter in word:
				current_dict = current_dict.setdefault(letter, {})
			if(_end in current_dict):
				for path in current_dict[_end]:
					ans.append(path)
		ans=self.nonrepeat_ans(ans)
		if rank:
			print_flow('Start ranking...\n')
			qv=query.split(',')
			ans=self.rank_search(ans,qv)
			print_flow('Rank done...\n')
		for path in ans:
			print(path)
	
	def rank_search(self,ans,qv):
		cos_sim = defaultdict(float)
		for path in ans:
			for word in qv:
				cos_sim[path]+=self.tfidf(word,path)
		#print(cos_sim)
		return list(sorted(cos_sim, key=cos_sim.__getitem__, reverse=True))

	def tfidf(self,word,path):
		current_dict=self.root
		tf=defaultdict(int)
		tf[path]=0
		for letter in word:
			current_dict = current_dict.setdefault(letter, {})
		if(_end in current_dict):
			for node in current_dict[_end]:
				tf[node]+=1
		return tf[path]/self.doc_len[path]*IDF(len(tf))

	def insert_doc_len(self,path,len):
		self.doc_len[os.path.abspath(path)]=len

	def output(self):
		for k,v in self.root.items():
			print(v)
	def nonrepeat_ans(self,ans):
		seen = set()
		seen_add = seen.add
		return [ x for x in ans if not (x in seen or seen_add(x))]

def print_flow(str):
	print(str, end='', file=sys.stderr,flush=True)

def traverse_file(begin_path,trie):
	file_num=0
	for root, dirs, files in os.walk(begin_path):
		#path = root.split('/')
		#print(os.path.basename(root))	   
		for file in files:
			file_num+=1
			print_flow('*')
			string_spilt(file,os.path.abspath(os.path.join(root, file)),trie)
			trie.insert_doc_len(os.path.join(root, file),len(file))
			read_file(file,os.path.join(root, file),trie)
	global doc_max_log
	if file_num != 0:
		doc_max_log=math.log10(file_num)


def read_file(file,path,trie):
	filename, fileext = os.path.splitext(file)
	#print(path)
	if(fileext==".docx"):
		try:
			document = zipfile.ZipFile(path)
		except zipfile.BadZipfile:
			return 
		read_docx(file,document,path,trie)
	else:
		try:
			filedata = open(path, encoding='UTF-8').read()
			string_spilt(filedata,path,trie)
			trie.insert_doc_len(path,len(file)+len(filedata))
		except:
			return

def read_docx(file,document,path,trie):
	xml_content = document.read('word/document.xml')
	document.close()
	tree = XML(xml_content)
	paragraphs = ""
	for paragraph in tree.getiterator(PARA):
		texts=""
		for node in paragraph.getiterator(TEXT):
			if node.text:
				texts += node.text.replace('\u7460',"")
		if texts:
			paragraphs+=str(texts)
	#print(paragraphs)
	string_spilt(paragraphs,path,trie)
	trie.insert_doc_len(path,len(file)+len(paragraphs))

def string_spilt(content,path,trie):
	vocab=""
	for i in range(len(content)-1):
		if(i+1==len(content)-1 and vocab):#content end
			vocab+=content[i]+content[i+1]
			trie.insert(vocab,os.path.abspath(path))
		elif(is_english(ord(content[i])) and is_english(ord(content[i+1]))):
			vocab+=content[i]
		elif(is_english(ord(content[i])) and not is_english(ord(content[i+1])) and len(vocab)>1):
			vocab+=content[i]
			#print(vocab)
			trie.insert(vocab,os.path.abspath(path))
			vocab=""
		else:
			trie.insert(content[i]+content[i+1],os.path.abspath(path))

def is_english(char_index):
	if(65<=char_index and char_index<=122):
		return True
	else:
		return False
def ready():
	trie=Trie()
	rank=False
	directory="."
	query="俊瑋,resume"
	i=0
	while i< len(sys.argv):
		if sys.argv[i]=='-r':
			rank=True
		elif sys.argv[i]=='-d':
			i+=1
			directory=sys.argv[i]
		elif sys.argv[i]=='-q':
			i+=1
			query=sys.argv[i]
		i+=1
	return [rank,directory,query,trie]

def main():
	[rank,directory,query,trie]=ready()
	print_flow('Start traversing...\n')
	traverse_file(directory,trie)
	print_flow('\nTraverse done...\n')
	print_flow('Start searching...\n')
	trie.search(query,rank)
	print_flow('Search done...\n')
	#trie.output()
if __name__ == '__main__':
	exit(main())