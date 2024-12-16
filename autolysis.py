#importing all the libaries required

import matplotlib.pyplot as plt
import pandas as pd
import os
import json
import requests
import sys
import pathlib 
import time 

#function for saving plots
def saveplots(df, corr_mat, hist_column, box_column, file_name):
	plt.imshow(corr_mat, cmap = 'hot', interpolation = 'nearest')
	plt.title("Correlation of columns of " + file_name)
	plt.savefig("plot1.png")
	plt.clf()
	plt.hist(df[[hist_column]], bins=10)
	plt.axis([0, 10,  0 , df[hist_column].max()])
	plt.title("Histogram Plot of " + hist_column + " Column")
	plt.savefig("plot2.png")
	plt.clf()
	plt.boxplot(df[box_column])
	plt.title("Box and whisker plot of " + box_column + " Column")
	plt.savefig("plot3.png")

#AI proxy token get
file_name = os.path.basename(sys.argv[1])

#dataframe handling
df = pd.read_csv(sys.argv[1], encoding='latin1')
columns = df.columns
nan_values = {}
for column in columns:
	null_num = df[column].isnull().sum() 
	if null_num != 0:
		nan_values[column] = int(null_num)
type_dict = {}
for column in columns:
	type_dict[column] = str(df.dtypes[column])
num_columns = []
unique_values = {}
for column in columns:
	if type_dict[column] == 'int64' or type_dict[column] == 'float64':
		num_columns.append(column)
	else:
		unique_values[column] = len(df[column].unique())
corr_mat = df[num_columns].corr()
summary_stats = df.describe()
outliers_dict = {}

df2 = df.dropna()
for column in num_columns:
	upper_bound = df2[column].quantile(0.75) + 1.5 * (df2[column].quantile(0.75) - df2[column].quantile(0.25))
	lower_bound = df2[column].quantile(0.25) - 1.5 * (df2[column].quantile(0.75) - df2[column].quantile(0.25))
	outliers = df2[(df2[[column]] > upper_bound) | (df2[[column]] < lower_bound)]
	outliers_dict[column] = int(outliers[column].count())

#sending first prompt
prompt_1 = "I have a csv file called " + str(file_name) + " with the following columns and their data types: " + str(type_dict) + ". The number of nan_values in each column are: " + str(nan_values) + ". The number of unique values in each non-numerical column is: " + str(unique_values) +  ". The number of outliers for each numerical column is given by: " + str(outliers_dict) + ". The correlation matrix of numerical columns is: " + str(corr_mat) + " and the summary statistics of each column is: " + str(summary_stats) + "Write a summary and analysis of the data from all the descriptive data given. Give just the name of a single column for which a histogram plot will be suitable and another column for which box and whisker plot will be suitable."

function_desc = [
	{
		"name": "generic_summary",
		"description": "Returns a generic summary along with one column for histogram plot and another column for box and whisker",
		"parameters": {
			"type": "object",
			"properties" : {
				"summary": {
					"type": "string",
					"description": "Short summary from the descriptive data given",
				},
				"analysis" : {
					"type": "string",
					"description": "A general analysis for the data given like outlier and anomaly detection, correlation analysis, time series analysis, cluster analysis, geographic analysis, network analysis etc., if possible"
				},
				"hist_column": {
					"type": "string",
					"description": "Only the name of the column for which histogram plot will be made",
				},
				"box_column":  {
					"type": "string",
					"description": "Only the name of the column for which box and whisker plot will be made",
				},
			},
			"required": ["summary" , "analysis", "hist_column", "box_column"]
		},
	}
]
				

url = "http://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
headers = {"Content-Type": "application/json", "Authorization": "Bearer "+os.environ["AIPROXY_TOKEN"]}
body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_1}], "functions": function_desc, "function_call": "auto"}

r = requests.post(url, headers=headers, data=json.dumps(body))

while(r.status_code != 200):
	time.sleep(10)
	r = requests.post(url, headers=headers, data=json.dumps(body))
response = r.json()
summary = json.loads(response['choices'][0]['message']['function_call']['arguments']).get('summary')
analysis = json.loads(response['choices'][0]['message']['function_call']['arguments']).get('analysis')
hist_column = json.loads(response['choices'][0]['message']['function_call']['arguments']).get('hist_column')
box_column = json.loads(response['choices'][0]['message']['function_call']['arguments']).get('box_column')

saveplots(df2, corr_mat, hist_column, box_column, file_name)

#sending 2nd prompt
prompt_2 = "Write a story in markdown format based on the data generated from a csv file named: " + file_name +  " with the following columns and their data types: " + str(type_dict) + ". The number of nan_values in each column are: " + str(nan_values) + ". The number of unique values in each non-numerical column is: " + str(unique_values) +  ". The number of outliers for each numerical column is given by: " + str(outliers_dict) + "." + "The data was studied for generic descriptive statistics and the following summary was generated by using an LLM: " + str(summary) + "." +" The LLM also did some analysis and found that :" + str(analysis) + ". Remember to briefly describe the data received, the analysis carried out, insights discovered and the implications of said discoveries."

function_desc2 = [
	{
		"name": "story",
		"description": "Returns a story based on descriptive data of a csv file",
		"parameters": {
			"type": "object",
			"properties" : {
				"story": {
					"type": "string",
					"description": "Story in markdown format from the descriptive data, summary and analysis given",
				},
			},
			"required": ["story",]
		},
	}
]
body = {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt_2}], "functions": function_desc2, "function_call": "auto"}
r = requests.post(url, headers=headers, data=json.dumps(body))
while(r.status_code != 200):
	time.sleep(10)
	r = requests.post(url, headers=headers, data=json.dumps(body))
response = r.json()

#saving readme file
tosave = json.loads(response['choices'][0]['message']['function_call']['arguments']).get('story')
filew = open("README.md", "w+")
filew.write(tosave)
filew.close()
