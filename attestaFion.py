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

from flask import Flask, send_file, request, render_template, flash, redirect, after_this_request
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, DateField
from wtforms.fields import html5 as h5fields
from wtforms.widgets import html5 as h5widgets
from wtforms.validators import DataRequired
import logging

import qrcode
from io import BytesIO

from pikepdf import Pdf, PdfImage, Name
import zlib

from PIL import Image

app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)

import string
import random
from google.cloud import secretmanager

DEBUG = True # pass it to True to run locally

if DEBUG:
	letters = string.ascii_lowercase
	app.config['SECRET_KEY'] = ''.join(random.choice(letters) for i in range(64))
else:
	secrets = secretmanager.SecretManagerServiceClient()
	app.config['SECRET_KEY'] = secrets.access_secret_version(request={"name": "projects/647590483524/secrets/secret_key/versions/1"}).payload.data.decode("utf-8")

DELAY = 3
ATTEST_PATH = os.path.join(Path(__file__).parent.absolute(), "attestations")

def get_date(user_delay):
	now = datetime.now()
	delta = timedelta(minutes=user_delay)
	now -= delta - timedelta(hours=1)
	date = now.strftime("%d/%m/%Y")
	hour = now.strftime("%Hh%M")
	return now, date, hour

def make_qr_code(profile, now, date, hour):
	first_name = profile["firstname"]
	last_name = profile["lastname"]
	birth_date = profile["birthday"]
	address = profile["address"] + profile["zipcode"] + profile["city"]
	reason = profile["reason"]
	data = "Cree le: %s a %s;\
		\nNom: %s;\nPrenom: %s;\
		\nNaissance: %s;\
		\nAdresse: %s;\
		\nSortie: %s a %s;\
		\nMotifs: %s;\n" % (date, hour, first_name, last_name, birth_date, address, date, hour, reason)
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
	driver.find_element_by_id("field-firstname").send_keys(profile["firstname"])
	driver.find_element_by_id("field-lastname").send_keys(profile["lastname"])
	driver.find_element_by_id("field-birthday").send_keys(profile["birthday"])
	driver.find_element_by_id("field-address").send_keys(profile["address"])
	driver.find_element_by_id("field-city").send_keys(profile["city"])
	driver.find_element_by_id("field-zipcode").send_keys(profile["zipcode"])
	# set hour
	driver.execute_script("document.getElementById('field-datesortie').valueAsDate = new Date(%s, %s, %s);" % (date.split("/")[2], str(int(date.split("/")[1]) - 1), date.split("/")[0]))
	driver.execute_script("document.getElementById('field-heuresortie').valueAsDate = new Date(1970, 1, 1, %s, %s);" % (hour.split("h")[0], hour.split("h")[1]))
	
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
	try:
		submit_button = driver.find_element_by_id("generate-btn").click()
		app.logger.info("Download started...")
	except Exception as e:
		app.logger.error("Error: %s" % str(e))

@app.route('/attestation', methods=['GET', 'POST'])
def get_pdf():
	form = UserForm()
	if form.validate_on_submit():

		profile = {}
		profile["firstname"] = form.firstname.data
		profile["lastname"] = form.lastname.data
		profile["birthday"] = form.birthday.data.strftime("%d/%m/%Y")
		profile["address"] = form.address.data
		profile["city"] = form.city.data
		profile["zipcode"] = form.zipcode.data
		profile["reason"] = form.reason.data
		profile["delay"] = form.delay.data

		now, date, hour = get_date(profile["delay"])

		if profile["reason"] == "achats" and (19 <= now.hour or now.hour < 6):
			flash("Des achats pendant le couvre-feu ? T'es magique toi !")
			return redirect("/")

		fp = webdriver.FirefoxProfile()
		fp.set_preference("browser.download.folderList", 2)
		fp.set_preference("browser.download.dir", str(PureWindowsPath(ATTEST_PATH)) if platform.system() == "Windows" else ATTEST_PATH)
		fp.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf, attachment/pdf")
		fp.set_preference("browser.download.manager.showWhenStarting",False)
		fp.set_preference("browser.helperApps.neverAsk.openFile","application/pdf")
		fp.set_preference("browser.helperApps.alwaysAsk.force", False)
		fp.set_preference("browser.download.manager.useWindow", False)
		fp.set_preference("browser.download.manager.focusWhenStarting", False)
		fp.set_preference("browser.download.manager.alertOnEXEOpen", False)
		fp.set_preference("browser.download.manager.showAlertOnComplete", False)
		fp.set_preference("browser.download.manager.closeWhenDone", True)
		fp.set_preference("pdfjs.disabled", True)

		options = webdriver.firefox.options.Options()
		options.add_argument("--headless")
		
		try:
			driver = webdriver.Firefox(options=options, firefox_profile=fp)
		except Exception as e:
			app.logger.error("Error: %s" % str(e))
			flash("Woopsy, une erreur s'est produite...")
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

		files_nb = len(os.listdir(ATTEST_PATH))

		# fill form
		fill_form(driver, profile, now, date, hour)

		# wait file to get there
		i = 5
		while i:
			if len(os.listdir(ATTEST_PATH)) <= files_nb:
				i -= 1
				time.sleep(DELAY)
			else:
				break
			if i == 0:
				app.logger.error("Error: file not downloaded.")
				flash("Woopsy, une erreur s'est produite...")
				return redirect("/")

		# rename file to avoid duplicates between users
		try:
			filepath = max([os.path.join(ATTEST_PATH, f) for f in os.listdir(ATTEST_PATH)], key=os.path.getctime)
			filename = profile["lastname"] + "_" + profile["firstname"] + os.path.basename(filepath)
			new_filename = os.path.join(ATTEST_PATH, filename)
			shutil.move(filepath, new_filename)
		except Exception as e:
			app.logger.error("Error: %s" % str(e))
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
		file_handle = open(new_filename, 'rb')

		# This *replaces* the `remove_file` + @after_this_request code above
		def stream_and_remove_file():
			yield from file_handle
			file_handle.close()
			os.remove(new_filename)

		return app.response_class(
			stream_and_remove_file(),
			mimetype='application/pdf',
			headers={'Content-Disposition': 'attachment', 'filename': filename}
		)
	return redirect("/")

reasons = ["achats_culte_culturel", "travail", "sante", "famille", "convocation_demarches", "demenagement", "sport"]
class UserForm(FlaskForm):
	firstname = StringField('Prénom', validators=[DataRequired()])
	lastname = StringField('Nom', validators=[DataRequired()])
	birthday = DateField('Date de naissance', validators=[DataRequired()], format="%d/%m/%Y")
	address = StringField('Adresse', validators=[DataRequired()])
	city = StringField('Ville', validators=[DataRequired()])
	zipcode = StringField('Code postal', validators=[DataRequired()])
	reason = SelectField('Motif', choices=reasons, validators=[DataRequired()])
	delay = IntegerField('Délai (minutes)', default=0)
	delay = h5fields.IntegerField('Délai (minutes)', widget=h5widgets.NumberInput(), default=0)
	submit = SubmitField('Générer')

@app.route('/')
def main():
	form = UserForm()
	return render_template('template.html', title='AttestaFion', form=form)

if __name__ == "__main__":
	app.run(host="0.0.0.0", port=8080)