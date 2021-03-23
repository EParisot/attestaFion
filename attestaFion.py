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

from flask import Flask, send_file, request, render_template, flash, redirect, after_this_request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField
from wtforms.validators import DataRequired

import qrcode
from io import BytesIO

from pikepdf import Pdf, PdfImage, Name
import zlib

from PIL import Image

import string
import random

DELAY = 3
ATTEST_PATH = "C:/Users/Rock_/Desktop/attestaFion/attestations"

app = Flask(__name__)

letters = string.ascii_lowercase
app.config['SECRET_KEY'] = ''.join(random.choice(letters) for i in range(64))


def get_date(user_delay):
	now = datetime.now()
	delta = timedelta(minutes=user_delay)
	now -= delta
	date = now.strftime("%d/%m/%y")
	hour = now.strftime("%Hh%M")
	return now, date, hour

def make_qr_code(profile, now, date, hour):
	first_name = profile["firstname"]
	last_name = profile["lastname"]
	birth_date = profile["birthday"]
	birth_city = profile["placeofbirth"]
	address = profile["address"] + profile["zipcode"] + profile["city"]
	reason = profile["reason"]
	data = "Cree le: %s a %s;\
		\nNom: %s;\nPrenom: %s;\
		\nNaissance: %s a %s;\
		\nAdresse: %s;\
		\nSortie: %s a %s;\
		\nMotifs: %s;\n" % (date, hour, first_name, last_name, birth_date, birth_city, address, date, hour, reason)
	qr = qrcode.QRCode(
		version=1,
		error_correction=qrcode.constants.ERROR_CORRECT_M,
		border=1,
	)
	qr.add_data(data.encode("utf-8"))
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	return img

def fill_form(driver, profile, now, date, hour):
	# fill profile
	firstname_input = driver.find_element_by_id("field-firstname").send_keys(profile["firstname"])
	lastname_input = driver.find_element_by_id("field-lastname").send_keys(profile["lastname"])
	birthday_input = driver.find_element_by_id("field-birthday").send_keys(profile["birthday"])
	placeofbirth_input = driver.find_element_by_id("field-placeofbirth").send_keys(profile["placeofbirth"])
	address_input = driver.find_element_by_id("field-address").send_keys(profile["address"])
	citye_input = driver.find_element_by_id("field-city").send_keys(profile["city"])
	zipcode_input = driver.find_element_by_id("field-zipcode").send_keys(profile["zipcode"])
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
			if checkbox.get_attribute('value') == profile["reason"]:
				checkbox.click()
		except:
			pass
	# submit
	submit_button = driver.find_element_by_id("generate-btn").click()

@app.route('/attestation', methods=['GET', 'POST'])
def get_pdf():
	form = UserForm()
	if form.validate_on_submit():

		profile = {}
		profile["firstname"] = form.firstname.data
		profile["lastname"] = form.lastname.data
		profile["birthday"] = form.birthday.data
		profile["placeofbirth"] = form.placeofbirth.data
		profile["address"] = form.address.data
		profile["city"] = form.city.data
		profile["zipcode"] = form.zipcode.data
		profile["reason"] = form.reason.data
		profile["delay"] = form.delay.data

		now, date, hour = get_date(profile["delay"])
		

		if profile["reason"] == "achats" and (19 <= now.hour or now.hour < 6):
			flash("Des achats pendant le couvre-feu ? T'es magique toi !")
			return redirect("/")
		
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
		if platform.system() == "Windows":
			webdriver_path = "webdrivers/chromedriver_win.exe"
		elif platform.system() == "Linux":
			webdriver_path = "webdrivers/chromedriver_linux"
		elif platform.system() == "Darwin":
			webdriver_path = "webdrivers/chromedriver_mac"
		else:
			app.logger.error("Error: server's system not identified...")
			flash("Woopsy, une erreur s'est produite...")
			return redirect("/")
		webdriver_path = os.path.join(Path(__file__).parent.absolute(), webdriver_path)
		try:
			driver = webdriver.Chrome(executable_path=webdriver_path, options=options)
		except:
			app.logger.error("Error, Chrome not found on system, please install Chrome 89 on server...")
			return redirect("/")

		# get page	
		driver.get("https://media.interieur.gouv.fr/attestation-deplacement-derogatoire-covid-19/")
		html = driver.page_source
		soup = BeautifulSoup(html, features="lxml")

		# pass the update button
		wait = WebDriverWait(driver, DELAY)
		try:
			update_button = wait.until(EC.element_to_be_clickable((By.ID, 'reload-btn')))
			update_button = driver.find_element_by_id("reload-btn").click()
		except:
			pass

		# fill form
		fill_form(driver, profile, now, date, hour)

		# wait file to get there
		time.sleep(DELAY)

		# rename file to avoid duplicates between users
		try:
			filename = max([os.path.join(ATTEST_PATH, f) for f in os.listdir(ATTEST_PATH)], key=os.path.getctime)
			new_filename = os.path.join(ATTEST_PATH, profile["firstname"] + "_" + os.path.basename(filename))
			shutil.move(filename, new_filename)
		except:
			app.logger.error("Error: renaming file failed.")
			flash("Woopsy, une erreur s'est produite...")
			return redirect("/")

		# make QRcode and edit PDF
		img = make_qr_code(profile, now, date, hour).convert('RGB').resize((590, 590))
		pdf_file = Pdf.open(new_filename, allow_overwriting_input=True)
		page = pdf_file.pages[1]
		page_image = list(page.images.keys())
		rawimage = page.images[page_image[0]]
		rawimage.write(zlib.compress(img.tobytes()), filter=Name("/FlateDecode"))
		rawimage.Width, rawimage.Height = 590, 590
		page.Resources.XObject[page_image[0]] = rawimage
		pdf_file.save(new_filename)

		# program file cleaner
		if platform.system() == "Linux":
			file_handle = open(new_filename)
			@after_this_request
			def remove_file(response):
				try:
					os.remove(new_filename)
					file_handle.close()
				except:
					app.logger.error("Error removing file")
				return response
		# send file to user
			return send_file(file_handle, mimetype="application/pdf")
		else:
			return send_file(new_filename, mimetype="application/pdf")
	return redirect("/")

reasons = ["achats", "travail", "sante", "famille", "handicap", "transit", "missions", "judiciaire"]
class UserForm(FlaskForm):
	firstname = StringField('Prénom:', validators=[DataRequired()])
	lastname = StringField('Nom:', validators=[DataRequired()])
	birthday = StringField('Date de naissance (XX/XX/XXXX):', validators=[DataRequired()])
	placeofbirth = StringField('Lieu de naissance:', validators=[DataRequired()])
	address = StringField('Adresse:', validators=[DataRequired()])
	city = StringField('Ville:', validators=[DataRequired()])
	zipcode = StringField('Code postal:', validators=[DataRequired()])
	reason = SelectField('Motif:', choices=reasons, validators=[DataRequired()])
	delay = IntegerField('Délai (minutes):')
	submit = SubmitField('Générer')

@app.route('/')
def main():
	form = UserForm()
	return render_template('template.html', title='AttestaFion', form=form)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)