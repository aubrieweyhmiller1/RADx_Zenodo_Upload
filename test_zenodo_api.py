import requests 
import logging 
import os
import re
import json

#########################################
#validation checks for input params
def input_validation_check(csv_filename, access_token, deposition_url):
	
	#validate csv file exists
	if os.path.isfile(csv_filename) is False:
		logging.error("Not able to find CSV file")
		return False
	
	#validate able to get access code from env variables
	if not access_token:
		logging.error(f"Access token not found in environmental variables.")
		return False

	#validate access code allows connection to API
	r = requests.get(deposition_url,
		params={'access_token': access_token})

	if r.status_code > 300:
		logging.error(f"Access token failed. Status code: {r.status_code}")
		return False

	logging.info(f"Access token successful. Status code: {r.status_code}")
	return True

#########################################
#get metadata from CSV file
def extract_metadata():
	print("")

#########################################
#send POST request to API to create new empty upload
def create_empty_upload(access_token, deposition_url):
	try:

		headers = {"Content-Type": "application/json"}
		params = {'access_token': access_token}
		r = requests.post(deposition_url,
						   params=params,
						   json={},
						   
						   # Headers are not necessary here since "requests" automatically
						   # adds "Content-Type: application/json", because we're using
						   # the "json=" keyword argument
						   # headers=headers, 
						   
						   headers=headers)

		if 199 < r.status_code < 300:
			logging.info(f"Post request successful. Status code: {r.status_code}")
			logging.info(f"Post request response {r.json()}")
			bucket_url = r.json()["links"]["bucket"]
			deposition_id = r.json()["id"]
			return bucket_url, deposition_id
		else: 
			logging.error(f"Post request not successful. Check access token and HTTPS URL. Status code: {r.status_code}")
			return False, False

	except Exception as e:
		logging.error(f"Error with post request: {e}")

#########################################
#create PUT request to populate empty upload with file
def upload_file(access_token, bucket_url, deposition_id, file_to_upload):
	try:
		
		''' 
		The target URL is a combination of the bucket link with the desired filename
		seperated by a slash.
		'''
		filename = file_to_upload.split("/")[-1] #splits filepath string by / to get only filename for target URL
		params = {'access_token': access_token}

		with open(file_to_upload, "rb") as fp:
			r = requests.put(
				"%s/%s" % (bucket_url, filename),
				data=fp,
				params=params,
			)

			if 199 < r.status_code < 300:
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
def add_metadata(access_token, deposition_url, deposition_id, metadata_params):
	try:
		data = {
		     'metadata': {
		         'title': 'Test Upload',
		         'upload_type': 'dataset',
		         'description': 'This is a test upload',
		         'creators': [{'name': 'Doe, John',
		                       'affiliation': 'Zenodo'}]
		    			}
				}

		headers = {"Content-Type": "application/json"}
		r = requests.put(deposition_url + '/%s' % deposition_id,
		                  params={'access_token': access_token},
		                  data=json.dumps(data),
		                  headers=headers)

		if 199 < r.status_code < 300:
			logging.info(f"PUT request to add metadata successful. Status code: {r.status_code}")
			logging.info(f"PUT request response {r.json()}")
			return True
		else:
			logging.error(f"PUT request to add metadata not successful. Status code: {r.status_code}. Message: {r.json()}")
			return False

	except Exception as e:
		logging.error(f"Error adding metadata: {e}")


##################################################################################
############################## main code block ###################################
##################################################################################
def main():

	#set up logging 
	log_file_path = "out/log_file.txt"
	logging.basicConfig(
		level=logging.INFO, 
		format='%(asctime)s - %(levelname)s - %(message)s', 
		handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()]
		)

	#load variables
	access_token = os.getenv("ZENODO_SANDBOX_API_KEY")
	csv_filename = "in/radx-up-asset-index.csv"
	test_uploadfile = "in/test.txt"
	deposition_url = "https://sandbox.zenodo.org/api/deposit/depositions"

	try: 
		if not input_validation_check(csv_filename, access_token, deposition_url):
			raise Exception("Input validation failed.")

		#main loop. for each row in CSV, extract metadata, then create POST and PUT request to upload item
		bucket_url, deposition_id = create_empty_upload(access_token, deposition_url)
		if not bucket_url:
			raise Exception("POST request to create empty upload failed.")

		
		if not upload_file(access_token, bucket_url, deposition_id, test_uploadfile):
			raise Exception("PUT request to upload file failed.")

		metadata_params = []	
		
		if not add_metadata(access_token, deposition_url, deposition_id, metadata_params):
			raise Exception("PUT request to add metadata failed.")

			

	except Exception as e:
			logging.error(f"Error: {e}")

##################################################################################
if __name__ == "__main__":
	main()

	


