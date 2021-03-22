import os
import platform
import shutil
from pathlib import Path, PureWindowsPath
import json
import time
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
import selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

from flask import Flask, send_file, request

import qrcode
from io import BytesIO

from pikepdf import Pdf, PdfImage, Name
import zlib

from PIL import Image

DELAY = 3
ATTEST_PATH = "C:/Users/Rock_/Desktop/attestaFion/attestations"

app = Flask(__name__)

def get_date(user_delay):
	now = datetime.now()
	delta = timedelta(minutes=user_delay)
	now -= delta
	date = now.strftime("%d/%m/%y")
	hour = now.strftime("%Hh%M")
	return now, date, hour

def make_qr_code(user, date, hour):
	first_name = user["firstname"]
	last_name = user["lastname"]
	birth_date = user["birthday"]
	birth_city = user["placeofbirth"]
	address = user["address"] + user["zipcode"] + user["city"]
	reasons = ", ".join(user["reasons"])
	data = "Cree le: %s a %s;\
		\nNom: %s;\nPrenom: %s;\
		\nNaissance: %s a %s;\
		\nAdresse: %s;\
		\nSortie: %s a %s;\
		\nMotifs: %s;\n" % (date, hour, first_name, last_name, birth_date, birth_city, address, date, hour, reasons)
	qr = qrcode.QRCode(
		version=1,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		border=1,
	)
	qr.add_data(data.encode("utf-8"))
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	return img

def serve_pil_image(pil_img):
	img_io = BytesIO()
	pil_img.save(img_io, 'JPEG', quality=70)
	img_io.seek(0)
	return send_file(img_io, mimetype='image/jpeg')

@app.route('/qr')
def get_qr_code():
	user = request.args.get('username', None)
	if user:
		# get profiles data
		with open("profiles.json") as f:
			profiles = json.load(f)
		# build data
		if user in profiles.keys():
			now, date, hour = get_date(profiles[user]["delay"])
			img = make_qr_code(profiles[user], date, hour)
			return serve_pil_image(img)
		else:
			return "User not found"
	else:
		return "No user specifyed"

def fill_form(driver, user, now, date, hour):
	# get profile
	with open("profiles.json") as f:
		profiles = json.load(f)
	# fill profile
	firstname_input = driver.find_element_by_id("field-firstname").send_keys(profiles[user]["firstname"])
	lastname_input = driver.find_element_by_id("field-lastname").send_keys(profiles[user]["lastname"])
	birthday_input = driver.find_element_by_id("field-birthday").send_keys(profiles[user]["birthday"])
	placeofbirth_input = driver.find_element_by_id("field-placeofbirth").send_keys(profiles[user]["placeofbirth"])
	address_input = driver.find_element_by_id("field-address").send_keys(profiles[user]["address"])
	citye_input = driver.find_element_by_id("field-city").send_keys(profiles[user]["city"])
	zipcode_input = driver.find_element_by_id("field-zipcode").send_keys(profiles[user]["zipcode"])
	# set hour
	datesortie_input = driver.find_element_by_id("field-datesortie").send_keys(date)
	heuresortie_input = driver.find_element_by_id("field-heuresortie").send_keys(hour)
	if (6 < now.hour < 19):
		type_button = driver.find_element_by_class_name("quarantine-button").click()
	else:
		type_button = driver.find_element_by_class_name("curfew-button").click()
	# set reason
	checkboxes = driver.find_elements_by_xpath("//input[@name='field-reason']")
	for checkbox in checkboxes:
		try:
			if checkbox.get_attribute('value') in profiles[user]["reasons"]:
				checkbox.click()
		except:
			pass
	# submit
	submit_button = driver.find_element_by_id("generate-btn").click()

@app.route('/attestation')
def get_pdf():
	user = request.args.get('username', None).lower()
	if user:
		# get profiles data
		with open("profiles.json") as f:
			profiles = json.load(f)

		if user in profiles.keys():
			# set driver options
			options = webdriver.ChromeOptions()
			options.headless = True
			# download pdf location
			options.add_experimental_option('prefs', {
				"download.default_directory": str(PureWindowsPath(ATTEST_PATH)) if platform.system() == "Windows" else ATTEST_PATH, #Change default directory for downloads
				"download.prompt_for_download": False, #To auto download the file
				"download.directory_upgrade": True,
				"plugins.always_open_pdf_externally": True #It will not show PDF directly in chrome
			})
			driver = webdriver.Chrome(options=options)

			# get page
			driver.get("https://media.interieur.gouv.fr/attestation-deplacement-derogatoire-covid-19/")
			html = driver.page_source
			soup = BeautifulSoup(html, features="lxml")

			# pass the update button
			wait = WebDriverWait(driver, DELAY)
			update_button = wait.until(EC.element_to_be_clickable((By.ID, 'reload-btn')))
			try:
				update_button = driver.find_element_by_id("reload-btn").click()
			except:
				pass

			# fill form
			now, date, hour = get_date(profiles[user]["delay"])
			fill_form(driver, user, now, date, hour)

			# wait file to get there
			time.sleep(DELAY)

			# rename file to avoid duplicates between users
			filename = max([os.path.join(ATTEST_PATH, f) for f in os.listdir(ATTEST_PATH)], key=os.path.getctime)
			new_filename = os.path.join(ATTEST_PATH, user + "_" + os.path.basename(filename))
			shutil.move(filename, new_filename)

			# make QRcode and edit PDF
			img = make_qr_code(profiles[user], date, hour).convert('RGB').resize((590, 590))
			pdf_file = Pdf.open(new_filename, allow_overwriting_input=True)
			page = pdf_file.pages[0]
			page_image = list(page.images.keys())
			rawimage = page.images[page_image[0]]
			rawimage.write(zlib.compress(img.tobytes()), filter=Name("/FlateDecode"))
			rawimage.Width, rawimage.Height = 590, 590
			page.Resources.XObject[page_image[0]] = rawimage
			pdf_file.save(new_filename)

			# send file to user
			return send_file(new_filename, mimetype="application/pdf")
		else:
			return "User not found"
	else:
		return "No user specifyed"

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)