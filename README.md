# Data Engineering Project Portfolio

This is a complete portfolio of the projects I have designed with a major focus on implementing various cloud services from Azure and AWS.

## 🤾‍♀️ [Tokyo Olympics Analytics Engineering](https://github.com/vedanthv/data-engineering-projects/tree/main/tokyo-olympics-de)

**Brief Overview**

The project utilizes the Tokyo Olympics Dataset from Kaggle  with data from over 11,000 athletes with 47 disciplines, along with 743 Teams taking part in the 2021(2020) Tokyo Olympics. There are different data files for coaches, athletes, medals and teams that was first ingested using KaggleAPI analysed using a variety of Azure Services, finally presented as a neat dashboard on Synapse Studio and PowerBI.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/876cc839-97ec-430d-88d2-f1a04f06698c)

**Stack**
- Azure Data Factory
- Azure Data Lake Gen 2
- Azure Blob Storage
- Azure Databricks
- Synapse Analytics
- PowerBI

## 🏎️ [Formula 1 Race Analytics Data Engineering](https://github.com/vedanthv/data-engineering-projects/tree/main/formula-1-analytics-engg)

**Brief Overview**

This is a complete end to end Formula 1 race analytics project that encompasses extraction of data from ErgastAPI, applying the right schema and using slowly changing dimensions with three different layers for raw, processed and presented data. The data is analysed using **Azure Databricks** after applying SQL filters and transformations to make the data understandable. The data is also subjected to **incremental load** constraints and data ingestion job is run every Sat at 10pm after the race dynamically with rerun pipelines and Email alerts on failure.

**Solution Architecture**

![image](https://github.com/vedanthv/data-engineering-projects/assets/44313631/0eee5f17-7102-4526-b3e3-8fb185a06553)

**Stack**
- Spark SQL
- Azure Databricks
- Postman
- PySpark
- Azure Blob Storage
- Azure Unity Catalog
- Azure Data Factory
- Azure DevOps
- Azure Synapse Studio
- Delta Lake Storage
- PowerBI
