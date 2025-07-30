import requests 
import logging 
import os
from dotenv import load_dotenv
import json
import pandas as pd

#########################################
#validation checks for input params
def input_validation_check(csv_file, access_token, deposition_url):

	#validate csv file exists
	if os.path.isfile(csv_file) is False:
		logging.error("Not able to find CSV file")
		return False
	
	#validate able to get access code from env variables
	if not access_token:
		logging.error(f"Access token not found in environmental variables.")
		return False

	#validate access code allows connection to API
	r = requests.get(deposition_url,
		params=params)

	if r.status_code > 300:
		logging.error(f"Access token or deposition_url failed. Status code: {r.status_code}")
		return False

	logging.info(f"Successful connection to API. Status code: {r.status_code}")
	return True


def check_statuscode(status_code):
	if status_code < 300:
		return True
	else: 
		return False

#########################################
#get metadata from CSV file
def extract_metadata():
	print("")

#########################################
#set up class to handle uploads
class Upload:

	def __init__(self, file_to_upload, metadata_params):

		self.file_to_upload = file_to_upload
		self.metadata_params = metadata_params

	def __str__(self):
		return(f"Upload object fileaname: {self.file_to_upload}, metadata: {self.metadata_params}")

	#########################################
	#send POST request to API to create new empty upload
	def create_empty_upload(self):
		try:

			r = requests.post(deposition_url,
							   params=params,
							   json={},
							   
							   # Headers are not necessary here since "requests" automatically
							   # adds "Content-Type: application/json", because we're using
							   # the "json=" keyword argument
							   # headers=headers, 
							   
							   headers=headers)
			

			if check_statuscode(r.status_code) :
				bucket_url = r.json()["links"]["bucket"]
				deposition_id = r.json()["id"]
				logging.info(f"Empty deposition creation successful.")
				return bucket_url, deposition_id
			else: 
				logging.info(f"Post request not successful. Check access token and HTTPS URL. Status code: {r.status_code}")
				return False, False

		except Exception as e:
			logging.error(f"Error with post request: {e}")

	#########################################
	#create PUT request to populate empty upload with file
	def upload_file(self, bucket_url):
		try:
			''' 
			The target URL is a combination of the bucket link with the desired filename
			seperated by a slash.
			'''
			filename = file_to_upload.split("/")[-1] #splits filepath string by / to get only filename for target URL

			with open(file_to_upload, "rb") as fp:
				r = requests.put(
					"%s/%s" % (bucket_url, filename),
					data=fp,
					params=params,
				)

				if check_statuscode(r.status_code):
					logging.info(f"PUT request successful. Status code: {r.status_code}")
					logging.info(f"PUT request response {r.json()}")
					return True
				else:
					logging.error(f"PUT request to upload file not successful. Status code: {r.status_code}. Message: {r.json()}")
					return False

		except Exception as e:
			logging.error(f"Error uploading file: {e}")

	#########################################
	#create PUT request to add metadata to upload
	def add_metadata(self, deposition_id):
		try:

			data = {
			     'metadata': {
			         'title': row["Title"],
			         'upload_type': row["Resource Type"],
			         'description': row["Description"],
			         'creators': [{'name': row["Creator"]
			                    }],
					 'keywords': [row["Keywords"]] #appends RADx program to keywords list
			    			}
					}

			headers = {"Content-Type": "application/json"}
			r = requests.put(deposition_url + '/%s' % deposition_id,
			                  params=params,
			                  data=json.dumps(data),
			                  headers=headers)

			if check_statuscode(r.status_code):
				logging.info(f"PUT request to add metadata successful. Status code: {r.status_code}")
				logging.info(f"PUT request response {r.json()}")
				return True
			else:
				logging.error(f"PUT request to add metadata not successful. Status code: {r.status_code}. Message: {r.json()}")
				return False

		except Exception as e:
			logging.error(f"Error adding metadata: {e}")

	def add_to_community(self):
		try:
			print(deposition_url + '/%s' % deposition_id + '/communities/' + community_id)
			r = requests.post(deposition_url + '/%s' % deposition_id + '/communities/' + community_id)

			if check_statuscode(r.status_code):
				logging.info(f"POST request to add to community successful. Status code: {r.status_code}")
				logging.info(f"POST request response {r.json()}")
				return True
			else:
				logging.error(f"POST request to add to community failed. Status code: {r.status_code}. Message: {r.json()}")
				return False
			
		except Exception as e:
			logging.error(f"Error adding metadata: {e}")

##################################################################################
############################## main code block ###################################
##################################################################################
if __name__ == "__main__":

	#set up logging 
	log_file_path = "out/log_file.txt"
	logging.basicConfig(
		level=logging.INFO, 
		format='%(asctime)s - %(levelname)s - %(message)s', 
		handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
		)

	#load global variables
	load_dotenv()
	access_token = os.getenv("ZENODO_SANDBOX_API_KEY") #get access token from .env file
	csv_file = "in/backup_csv.csv"
	deposition_url = "https://sandbox.zenodo.org/api/deposit/depositions"
	failed_files = []
	community_id = "aw_test"

	headers = {"Content-Type": "application/json"}
	params = {"access_token": access_token}

	#check if variables loaded correctly and are accurate
	try: 
		if not input_validation_check(csv_file, access_token, deposition_url):
			raise Exception("Input validation failed.")
		
		df = pd.read_csv(csv_file)
		for index, row in df.iterrows():
			#extract metadata from each row
			metadata_params = row.to_dict()
			file_to_upload = row['Filename']

			upload_file = Upload(file_to_upload, metadata_params)

			bucket_url, deposition_id = upload_file.create_empty_upload()
			if not bucket_url:
				failed_files.append(file_to_upload)
				raise Exception(f"POST request to create empty upload failed for file: {file_to_upload}")
			
			if not upload_file.upload_file(
				bucket_url):
				failed_files.append(file_to_upload)
				print("")
				raise Exception(f"PUT request to upload file failed for file: {file_to_upload}.")

			if not upload_file.add_metadata(deposition_id):
				failed_files.append(file_to_upload)
				raise Exception(f"PUT request to add metadata failed for file: {file_to_upload}")
			
			if not upload_file.add_to_community(deposition_id, community_id):
				failed_files.append(file_to_upload)
				raise Exception(f"PUT request to add metadata failed for file: {file_to_upload}")
			
			# actually publish

		#create csv file with list of failed_csvs
		print(f"FAILED FILES:", failed_files)
		failed_dict = {"files": failed_files}
		df = pd.DataFrame(failed_dict)
		df.to_csv("./out/failed_files.csv", index=False)
	except Exception as e:
			logging.error(f"Error: {e}")

##################################################################################