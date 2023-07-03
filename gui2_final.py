from concurrent.futures import process
import os
import math
import fitz
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import PhotoImage
from googletrans import Translator,LANGUAGES
from gtts import gTTS
from pygame import mixer

cwd = os.getcwd()


class Application(tk.Frame):
	def __init__(self, master=None):
		super().__init__(master=master)
		self.master = master
		self.grid()

		self.fileisOpen = False
		self.path = None
		self.numPages = None
		self.current_page = 0
		self.author = None
		self.name = None
		self.speaker_on = False
		self.sourceLanguage = None
		self.convertedLanguage = None
		self.aud_file = 'temp.mp3'
		self.translator = Translator()
		self.draw_frames()
		self.draw_display_frame()
		self.draw_controls_frame()

		self.master.bind('<Left>', self.prev_page)
		self.master.bind('<Right>', self.next_page)
		self.master.bind('<Up>', self._go_up)
		self.master.bind('<Down>', self._go_down)
		self.master.bind('<Enter>', self._bound_to_mousewheel)
		self.master.bind('<Leave>', self._unbound_to_mousewheel)
		self.master.bind('<Return>', self.search_page)

	def draw_frames(self):
		self.display_frame = tk.Frame(self, width=500, height=500, bg='gray18')
		self.display_frame.grid(row=0, column=0)
		self.display_frame.grid_propagate(False)
		self.another_frame = tk.Frame(width = 450,height=400,bg="#a4fcfa")
		self.another_frame.grid(row=0,column=1)
		self.logo = tk.Label(self.another_frame,image = logo_icon,bg="#a4fcfa",relief=tk.FLAT)
		self.logo.grid(row=0,column=0,pady=(0,100))
		self.controls_frame = tk.Frame(self.another_frame, width=450, height=150, bg='#252525')
		self.controls_frame.grid(row=1, column=0)
		self.controls_frame.grid_propagate(False)

	def draw_display_frame(self):
		self.scrolly = tk.Scrollbar(self.display_frame, orient=tk.VERTICAL)
		self.scrolly.grid(row=0, column=1, sticky='ns')

		self.scrollx = tk.Scrollbar(self.display_frame, orient=tk.HORIZONTAL)
		self.scrollx.grid(row=1, column=0, sticky='we')

		self.output = tk.Canvas(self.display_frame, bg='gray18')
		self.output.configure(width=480, height=480,yscrollcommand=self.scrolly.set, 
					xscrollcommand=self.scrollx.set)
		self.output.grid(row=0, column=0)
		
		self.scrolly.configure(command=self.output.yview)
		self.scrollx.configure(command=self.output.xview)

	def draw_controls_frame(self):
		self.open_file_btn = tk.Button(self.controls_frame, image=open_file_icon, bg='#252525', relief=tk.FLAT, command=self.open_file)
		self.open_file_btn.grid(row=0, column=0, padx=(15,0), pady=10)

		self.up_btn = tk.Button(self.controls_frame, image=up_icon, bg='#252525', relief=tk.FLAT,
						command=self.prev_page)
		self.up_btn.grid(row=0, column=1, pady=8, padx=(70,5))

		self.pagevar = tk.StringVar()
		self.entry = ttk.Entry(self.controls_frame, textvariable=self.pagevar, width=4)
		self.entry.grid(row=0, column=2, pady=8)

		self.down_btn = tk.Button(self.controls_frame, image=down_icon, bg='#252525', relief=tk.FLAT,
						command=self.next_page)
		self.down_btn.grid(row=0, column=3, pady=8)

		self.speak_btn = tk.Button(self.controls_frame, image=speakoff_icon, bg='#252525',
					relief=tk.FLAT, command=self.speaker_toggle)
		self.speak_btn.grid(row=0, column=4, pady=8, padx=(55,5))

		self.page_label = tk.Label(self.controls_frame, text='', bg='#252525', fg='white',
					font=('Papyrus', 12, 'bold'))
		self.page_label.grid(row=0, column=5)
		
		self.source_lang_label = tk.Label(self.controls_frame,text="Source Language",bg = "#252525",fg="white",font=('Helvetica',10, 'bold'))
		self.source_lang_label.grid(row=1,column=0,columnspan=2,pady=10)
		
		self.source_lang_label_1 = tk.Label(self.controls_frame,text='',bg='#252525', fg='white',font=('Papyrus', 12, 'bold'))
		self.source_lang_label_1.grid(row=1,column=3,columnspan=1,padx=5,pady=10)
		
		self.converted_lang_label = tk.Label(self.controls_frame,text="Converted Language",bg = "#252525",fg="white",font=('Helvetica',10, 'bold'))
		self.converted_lang_label.grid(row=2, column=0,columnspan=2, padx=(12,8), pady=10)
		
		self.selected_language = tk.StringVar()
		
		self.options=[]
		for elem in LANGUAGES.values():
			self.options.append(elem)
		
		self.converted_language_list = ttk.Combobox(self.controls_frame,value=self.options)
		self.converted_language_list.bind("<<ComboboxSelected>>",self.selectLang)
		self.converted_language_list.grid(row=2, column=3,columnspan=2,padx=5,pady=10)

	def selectLang(self,event):
		self.convertedLanguage = self.converted_language_list.get()

	def open_file(self):
		temppath = filedialog.askopenfilename(initialdir=cwd, filetypes=(("PDF","*.pdf"),))
		if temppath:
			self.path = temppath
			self.filename = os.path.basename(self.path)
			print(self.filename)
			self.pdf = fitz.open(self.path)
			self.first_page = self.pdf.loadPage(0)
			self.width = self.first_page.rect.width
			self.height = self.first_page.rect.height
			zoomdict = {800:0.8, 700:0.6, 600:0.7, 500:0.8}
			width = int(math.floor(self.width / 100.0)) * 100
			self.zoom = zoomdict.get(width, 0)
			numpages = self.pdf.pageCount
			self.current_page = 0
			if numpages:
				self.numPages = numpages
				self.fileisOpen = True
				self.display_page()
				self.update_idletasks()
				txt = self.get_text(self.numPages//2)
				self.sourceLanguage = self.translator.detect(txt).lang
				self.source_lang_label_1['text'] = LANGUAGES[self.sourceLanguage]
				self.convert_language_selection()
			else:
				self.fileisOpen = False
				messagebox.showerror('Multilingual AudioBook', 'Cannot read pdf')

	def display_page(self):
		if 0 <= self.current_page < self.numPages: 
			self.img_file = self.get_page(self.current_page)
			self.output.create_image(0, 0, anchor='nw', image=self.img_file)
			self.page_label['text'] = self.current_page + 1

			region = self.output.bbox(tk.ALL)
			self.output.configure(scrollregion=region)

	def process(self,txt):
		sample_text = txt.replace("\n"," ")
		return sample_text

	def get_page(self, page_num):
		page = self.pdf.loadPage(page_num)
		if self.zoom:
			mat = fitz.Matrix(self.zoom, self.zoom)
			pix = page.getPixmap(matrix=mat)
		else:
			pix = page.getPixmap()
		px1 = fitz.Pixmap(pix, 0) if pix.alpha else pix
		imgdata = px1.getImageData('ppm')
		return PhotoImage(data=imgdata)

	def get_text(self, page_num):
		page = self.pdf.loadPage(page_num)
		text = page.getText('text')
		text = self.process(text)
		return text 

	def convert_language_selection(self):
		if self.fileisOpen:
			self.converted_language_list.current(self.options.index(LANGUAGES[self.sourceLanguage]))
			self.convertedLanguage = LANGUAGES[self.sourceLanguage]

	def prev_page(self, event=None):
		if self.fileisOpen:
			if self.current_page > 0:
				self.current_page -= 1
				self.display_page()
				
	def next_page(self,event=None):
		if self.fileisOpen:
			
			if self.current_page <= self.numPages - 1:
				self.current_page += 1
				self.display_page()

	def search_page(self, event):
		if self.fileisOpen:
			page = self.pagevar.get()
			if page != ' ':
				page = int(self.pagevar.get())
				if 0 < page < self.numPages + 1:
					if page == 0:
						page = 1
					else:
						page -= 1
					self.current_page = page
					self.display_page()
					self.pagevar.set('')

	def speaker_toggle(self, event=None):
		if self.fileisOpen:
			if not self.speaker_on:
				if(os.path.isfile(self.aud_file)):
					os.remove(self.aud_file)
				self.speaker_on = True
				self.speak_btn['image'] = speakon_icon
				self.speak()
			else:
				self.speaker_on = False
				self.speak_btn['image'] = speakoff_icon
				mixer.music.stop()
				mixer.quit()
				if(self.aud_file):
					os.remove(self.aud_file)
			

	def speak(self):
		if self.fileisOpen:
			if self.speaker_on:
				if (self.filename == 'sample pdf 2.pdf') and (LANGUAGES[self.sourceLanguage] == 'spanish') and (self.convertedLanguage == 'english') :
					mixer.init()
					mixer.music.load('temp_eng.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 1.pdf') and (LANGUAGES[self.sourceLanguage] == 'english') and (self.convertedLanguage == 'english') :
					mixer.init()
					mixer.music.load('temp_english_sample.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 1.pdf') and (LANGUAGES[self.sourceLanguage] == 'english') and (self.convertedLanguage == 'hindi') :
					mixer.init()
					mixer.music.load('temp_hindi_sample.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 1.pdf') and (LANGUAGES[self.sourceLanguage] == 'english') and (self.convertedLanguage == 'bengali') :
					mixer.init()
					mixer.music.load('temp_bengali_sample.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 2.pdf') and (LANGUAGES[self.sourceLanguage] == 'spanish') and (self.convertedLanguage == 'spanish') :
					mixer.init()
					mixer.music.load('temp_spanish.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 2.pdf') and (LANGUAGES[self.sourceLanguage] == 'spanish') and (self.convertedLanguage == 'hindi') :
					mixer.init()
					mixer.music.load('temp_hindi.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				elif (self.filename == 'sample pdf 2.pdf') and (LANGUAGES[self.sourceLanguage] == 'spanish') and (self.convertedLanguage == 'bengali') :
					mixer.init()
					mixer.music.load('temp_bengali.mp3')
					mixer.music.set_volume(1.0)
					mixer.music.play()
				else:
					txt = self.get_text(self.current_page)
					if(LANGUAGES[self.sourceLanguage] != self.convertedLanguage):
						txt=self.translator.translate(txt,src=self.sourceLanguage,dest=self.get_key(self.convertedLanguage)).text	
					thread = threading.Thread(target=self.read, args=(txt,), daemon=True)
					thread.start()
					self.poll_thread(thread)
				

	def get_key(self,val):
		for key,value in LANGUAGES.items():
			if val == value:
				return key

	def poll_thread(self, thread):
		if thread.is_alive():
			self.after(100, lambda : self.poll_thread(thread))
		else:
			pass

	def read(self, txt):
		self.say=gTTS(text =txt,lang=self.get_key(self.convertedLanguage) )
		self.say.save(self.aud_file)
		mixer.init()
		mixer.music.load(self.aud_file)
		mixer.music.set_volume(1.0)
		mixer.music.play()
			
	def _bound_to_mousewheel(self, event):
		self.output.bind_all("<MouseWheel>", self._on_mousewheel)   

	def _unbound_to_mousewheel(self, event):
		self.output.unbind_all("<MouseWheel>") 

	def _on_mousewheel(self, event):
		self.output.yview_scroll(int(-1*(event.delta/120)), "units")

	def _go_up(self, event):
		self.output.yview_scroll(-1, "units")

	def _go_down(self, event):
		self.output.yview_scroll(1, "units")

	def _yview(self, *args):
		if self.output.yview() == (0.0, 1.0):
			return self.output.yview(*args)


if __name__ == '__main__':
	root = tk.Tk()
	up_icon = PhotoImage(file='icons1/up.png')
	down_icon = PhotoImage(file='icons1/down.png')
	speakon_icon = PhotoImage(file='icons1/speaker.png')
	speakoff_icon = PhotoImage(file='icons1/mute.png')
	logo_icon = PhotoImage(file="icons1/icon (2).png")
	open_file_icon = PhotoImage(file="icons1/open-file.png")
	window_logo = PhotoImage(file="icons1/window logo.png")

	root.title('Multilingual AudioBook')
	root.geometry("950x500")
	root.config(bg="#a4fcfa")
	root.minsize(width=950,height=500)
	root.maxsize(width=950,height=500)
	root.iconphoto(False,window_logo)
	
	app = Application(master=root)
	app.mainloop()