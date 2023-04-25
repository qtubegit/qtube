app: *.py
	pyinstaller main.py --windowed --noconsole --noconfirm --icon=icon.ico --clean --name QTube --add-data="http/player.html:http" 

py2app: clean
	rm setup.py
	py2applet --resources=http --iconfile=images/icon.icns --make-setup main.py
	python3 setup.py py2app -A

clean:
	rm -rf build dist