## Tokyo Olympics Data Engineering Project

![download](https://github.com/vedanthv/data-engineering-projects/assets/44313631/d8ddf328-5010-4e41-8dc4-5e695def87e3)
![download](https://github.com/vedanthv/data-engineering-projects/assets/44313631/3b86995c-9fe9-467c-bd67-48481b97e674)
![download](https://github.com/vedanthv/data-engineering-projects/assets/44313631/21ccd96d-17d4-4328-bd56-85ce69b26c72)

### About the Data

This contains the details of over 11,000 athletes, with 47 disciplines, along with 743 Teams taking part in the 2021(2020) Tokyo Olympics.

This dataset contains the details of the Athletes, Coaches, Teams participating as well as the Entries by gender. It contains their names, countries represented, discipline, gender of competitors, name of the coaches.

### Tech Stack

- Azure Data Factory
- Azure Data Lake Gen 2
- Azure Blob Storage
- Azure Databricks
- Synapse Analytics
- PowerBI

### Pipeline

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/d0eeb64e-b6c9-40c8-bfde-413981d5fe0e)

#### Setup

- Setup an Azure Account with Github Student Pack.
  
- Keep the GitHub Repository with the Olympics raw data ready.

- Azure Databricks is SSO authenticated with Azure so no need separate setup.

- A storage account has to be created on Azure to load resources.

- While using Databricks "Azure Blob Storage Container" has to be given write,read access on the IAM console for the container.

#### Data Ingestion

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/e432b1af-4513-402e-865e-430404046de1)

#### Data Transformation

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/05cbdf20-926c-4c67-a046-ec6f8ea2ed60)

**Transformed Data in Azure Datalake Gen2 Storage**

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/6003970a-dd0b-45e7-80d9-696b64b4774b)

#### Data Analytics

#### Dashboards and Reporting

### Transformation Code

The Databricks dataset transformation code is [here](https://github.com/vedanthv/data-engineering-projects/blob/main/tokyo-olympics/data-transformation-final.ipynb)

