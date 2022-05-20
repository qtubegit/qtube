app: *.py
	pyinstaller main.py --windowed --noconsole --noconfirm --icon=icon.ico --clean --name QTube --add-data="http/player.html:http" --hidden-import=pynput.keyboard

clean:
	rm -rf build dist