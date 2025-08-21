#########################################
#########################################
# STEP 2 IN TRANSITION PROCESS (1) CREATE DRAFT UPLOADS IN SANDBOX TO CONFIRM WORKING (2) SUBMIT TO PROD ENVIRONMENT AND PUBLISH (WILL GO TO COMMUNITY)
# UPLOADS AND PUBLISHES FILES TO PRODUCTION ZENODO
# OUTPUTS A FAILED AND SUCCESSFUL SUBMISSION FILE WITH DEPOSITION IDS
#########################################
#########################################
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

	r = requests.get(deposition_url, params=params)

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
#set up class to handle uploads
class Upload:

	def __init__(self, file_to_upload, metadata_params):
		self.file_to_upload = file_to_upload
		self.metadata_params = metadata_params
		self.deposition_id = None

	def __str__(self):
		return(f"Upload object filename: {self.file_to_upload}, metadata: {self.metadata_params}")

	#########################################
	#send POST request to API to create new empty upload
	def create_empty_upload(self):
		try:
			r = requests.post(deposition_url, params=params, json={}, headers=headers)
			if not check_statuscode(r.status_code):
				logging.error(f"Post request not successful. Status code: {r.status_code}, Message: {r.text}")
				return None, None, f"Post request failed. Status code: {r.status_code}, Message: {r.text}"

			bucket_url = r.json()["links"]["bucket"]
			deposition_id = r.json()["id"]
			self.deposition_id = deposition_id
			logging.info(f"Empty deposition creation successful. Deposition ID: {deposition_id}")
			return True, bucket_url, deposition_id, None
		except Exception as e:
			logging.error(f"Error with post request: {e}")
			return None, None, None, f"Error with post request: {e}"

	#########################################
	#create PUT request to populate empty upload with file
	def upload_file(self, bucket_url):
		try:
			filename = self.file_to_upload.split("/")[-1]
			with open(self.file_to_upload, "rb") as fp:
				r = requests.put(f"{bucket_url}/{filename}", data=fp, params=params)
				if not check_statuscode(r.status_code):
					logging.error(f"PUT request to upload file not successful. Status code: {r.status_code}. Message: {r.text}")
					return False, f"PUT request failed. Status code: {r.status_code}, Message: {r.text}"
				logging.info(f"PUT request successful. Status code: {r.status_code}")
				return True, None
		except Exception as e:
			logging.error(f"Error uploading file: {e}")
			return False, f"Error uploading file: {e}"

	#########################################
	#create PUT request to add metadata to upload
	def add_metadata(self, deposition_id, row):
		try:
			data = {
				 'metadata': {
					 'title': row["Title"],
					 'upload_type': row["Resource Type"],
					 'description': row["Description"],
					 'creators': [{'name': row["Creators"]}],
					 'keywords': [row["Keywords"]],
					 'communities': [{"identifier": community_id}]
				 }
			}
			r = requests.put(f"{deposition_url}/{deposition_id}", params=params,
							 data=json.dumps(data), headers={"Content-Type": "application/json"})
			if not check_statuscode(r.status_code):
				logging.error(f"PUT request to add metadata not successful. Status code: {r.status_code}. Message: {r.text}")
				return False, f"Metadata PUT failed. Status code: {r.status_code}, Message: {r.text}"
			logging.info(f"PUT request to add metadata successful. Status code: {r.status_code}")
			return True, None
		except Exception as e:
			logging.error(f"Error adding metadata: {e}")
			return False, f"Error adding metadata: {e}"

	#########################################
	#create POST request to publish. will publish to community
	def publish(self, deposition_id):
		try:
			publish_url = f"{deposition_url}/{deposition_id}/actions/publish"
			r = requests.post(publish_url, params={'access_token': access_token})
			if not check_statuscode(r.status_code):
				logging.error(f"POST request to publish failed. Status code: {r.status_code}. Message: {r.text}")
				return False, f"Publish failed. Status code: {r.status_code}, Message: {r.text}"
			logging.info(f"POST request to publish successful. Status code: {r.status_code}")
			return True, None
		except Exception as e:
			logging.error(f"Error publishing: {e}")
			return False, f"Error publishing: {e}"
	
	#########################################
	#add failed file info to failed output csv
	def add_to_failed(self, row, error):
		failed_files.append(self.file_to_upload)
		failed_depositions.append(getattr(self, "deposition_id", None))
		failed_titles.append(row['Title'])
		error_messages.append(str(error))
	
##################################################################################
############################## main code block ###################################
##################################################################################
if __name__ == "__main__":

	#set up logging 
	log_file_path = "out/UP/log_file.txt"
	logging.basicConfig(
		level=logging.INFO, 
		format='%(asctime)s - %(levelname)s - %(message)s', 
		handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
		)

	#load global variables
	load_dotenv()
	access_token = os.getenv("ZENODO_PROD_ACCESS_TOKEN") #get access token from .env file
	csv_file = "in/UP/radx_UP_asset_inv_w_filenames.csv"
	deposition_url = "https://zenodo.org/api/deposit/depositions"
	failed_files = []
	failed_depositions = []
	failed_titles = []
	error_messages = []
	success_files = []
	success_depositions = []
	success_titles = []
	community_id = "radx" #CHANGE TO MATCH YOUR DESIRED COMMUNITY. FIND VIA COMMUNITY PAGE URL. FOR EXAMPLE, https://zenodo.org/communities/YOUR_COMMUNITY_ID/records?q=&l=list&p=1&s=10&sort=newest

	headers = {"Content-Type": "application/json"}
	params = {"access_token": access_token}

	#check if variables loaded correctly and are accurate
	try: 
		if not input_validation_check(csv_file, access_token, deposition_url):
			raise Exception("Input validation failed.")
		
		df = pd.read_csv(csv_file)
		for index, row in df.iterrows():

			if index >= 130:
				#extract metadata from each row
				metadata_params = row.to_dict()
				file_to_upload = row['Filename']

				if "RADx_rad" in csv_file:
					file_to_upload = "./in/rad/" + file_to_upload
				elif "radx_UP" in csv_file:
					file_to_upload = "./in/UP/" + file_to_upload
				elif "RADx_DataHub" in csv_file:
					file_to_upload = "./in/DataHub/" + file_to_upload

				upload_file = Upload(file_to_upload, metadata_params)
				logging.info("##########################################################")
				logging.info(f"Beginning upload for file {index + 1} / {len(df)}")
				logging.info("##########################################################")

				try:
					# Step 1: Create empty upload
					ok, bucket_url, deposition_id, err = upload_file.create_empty_upload()
					if not ok:
						upload_file.add_to_failed(row, err)
						continue

					# Step 2: Upload file
					ok, err = upload_file.upload_file(bucket_url)
					if not ok:
						upload_file.add_to_failed(row, err)
						continue

					# Step 3: Add metadata
					ok, err = upload_file.add_metadata(deposition_id, row)
					if not ok:
						upload_file.add_to_failed(row, err)
						continue
					
					# Step 4: Publish
					# ONLY RUN THIS STEP IF YOU ARE CONFIDENT IN YOUR UPLOAD AND INPUT FILES. IN ZENODO, YOU CANNOT DELETE FILES ONCE PUBLISHED, YOU HAVE TO REQUEST FOR THEM TO BE DELETED
					ok, err = upload_file.publish(deposition_id)
					if not ok:
						upload_file.add_to_failed(row, err)
						continue

					# Log successful files
					success_depositions.append(deposition_id)
					success_files.append(file_to_upload)
					success_titles.append(row['Title'])
					logging.info(f"Upload successful for file: {file_to_upload}")
					
				#catch non-handled errors
				except Exception as e:
					upload_file.add_to_failed(row, e)
					logging.error(f"FAILED for file {file_to_upload} Error: {e}")
					continue

	finally:
		success_dict = {"files": success_files, "depositon_ids": success_depositions, "titles": success_titles}
		df = pd.DataFrame(success_dict)
		df.to_csv("./out/UP/successful_PUBLISHED_files_r2.csv", index=False)
		print(success_dict)

		failed_dict = {"files": failed_files, "depositon_ids": failed_depositions, "titles": failed_titles, "error message": error_messages}
		df = pd.DataFrame(failed_dict)
		df.to_csv("./out/UP/failed_PUBLISHED_files_r2.csv", index=False)
		print(failed_dict)

##################################################################################
