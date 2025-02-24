# Dev Diary

## 08.02.2025
- Setup Workspace
- Init Git
- Create repo
- Add readme
- Add changelog

## 10.02.2025
- Finally got deployment to GCP running!
- Main take aways:
  - IAM is difficult!
  - Gemini is only helpful max. 50% of the time
  - Write everything down! (Check CloudFunctionDeployTutorial)
 
## 11.02.2025
- Recreating minimal deployment examples for CloudFunctionDeployTutorial
- IAM is DIFFICULT!
- Devil's in the detail!
  - If you want to create a new cloud-function from scratch using GitHub Actions it's possible!
  - Here's an example snippet from deploy.yml:
    ```yml
    - name: Deploy second hello_world_function
          run: |
            gcloud functions deploy hello_world_function_2 \
            --region europe-west1 \
            --source cloud_functions/hello_world_2 \
            --trigger-http \
            --runtime python39 \
            --entry-point hello_world \
            --allow-unauthenticated \
    ```
    It's super important to specify ``--entry-point`` (and name it that way! not ``entryPoint`` like Gemini suggested)
    Then name the ``--entry-point`` after the first function you want to be executed by GCP.
    That is the name of a function INSIDE your source-code!
    Just to specify - we have 3 names going on:
    1. The name of the GCP cloud function
    2. The name of the folder we've stored our source code in
    3. The name of a function inside the source-code
    4. (actually we also have the name of the individual py-files aswell, like main.py)
   
    To keep things as easy as possible I guess it's best practice to just stick to ONE name:
    Name the folder, the function inside the source code and the GCP-function the same.

    In this case - and only in this case - it's also possible to leave out the ``--entry-point`` specification.
    
## 13.02.2025
- Finished "Deploy Google Cloud Function using GitHub Actions" Tutorial [on Medium](https://medium.com/@theironscavenger/deploy-google-cloud-functions-using-github-actions-pt-1-0f51c714fd59)

- Added "official_stats"-function to project. This scrapes Ausbildung.de and
  gets basic values (number of companies and overall vacancies per type).
  It returns a Python-dict with key-values pairs of the results.

- Added PostgreSQL database to the project to store the scrape-data.
  - Creation on GCP takes quite a few minutes. Need to setup ID/password first.
  - Needs Compute Engine API
  - Database name: AusbildungMiningDatabase
  - Needs additional user/password to access database.
  - Initial database setup:
    ```PostgreSQL
    CREATE SCHEMA "AusbildungMining";
    ```
    ```PostgreSQL
    -- Use AusbildungMining Schema
    SET search_path TO "AusbildungMining";
    -- Create new table allowing NULL values
    CREATE TABLE official_stats (
    date DATE PRIMARY KEY, -- this only stores the date (choose one!)
    date TIMESTAMP WITHOUT TIME ZONE PRIMARY KEY, -- this also stores time
    feature1 INTEGER NULL,
    feature2 INTEGER NULL,
    feature3 INTEGER NULL
    );
    ```

- **Writing to PostgreSQL database from Cloud Run Function**:
  - Cloud Run Service Account needs *Cloud SQL Client* role.
  - Add user to database, select *Cloud IAM*, then copy principal from service account and paste.
  - User needs to be granted priviliges to query or modify database, see [here](https://cloud.google.com/sql/docs/postgres/add-manage-iam-users#grant-db-privileges)
  - Grant service account full priviliges on the database *(careful!)*

    Note: Don't use full service account e-mail here! Use user name as it is displayed in the Users-overview of the database (ending on \*.iam)
    ```PostgreSQL
    -- Careful! Granting rights on schema only might NOT work!
    GRANT ALL ON SCHEMA "AusbildungMining" TO "service@account.mail"

    -- instead grant rights on SPECIFIC TABLES - this worked!
    GRANT ALL ON TABLE "SchemaName".table_name TO "service@account.mail"
    ```
  - Use Cloud Secret Manager to store service account credentials (email, database name, cloud sql connection name)
    - SERVICE_ACCOUNT_USER_NAME (ending on \*.iam)
    - DATABASE_NAME
    - DB_CONNECTION_NAME (found under "Connections" in SQL-overview)

  - Added GCP_PROJECT_ID as secret to GitHub to access secrets in GCP (adding it as environment-var to deploy.yml works perfectly!)

  - Secretmanager in ``official_stats`` currently not yet working.
    Error message excerpt:
    ```
    File "/workspace/main.py", line 6, in main
    from official_stats import get_official_stats, write_to_sql
    File "/workspace/official_stats.py", line 9, in <module>
    from google.cloud import secretmanager
    ImportError: cannot import name 'secretmanager' from 'google.cloud' (unknown location)
    ```

## 14.02.2025
>***The following notes are a bit random. Go to 15.02.25 for a more cleaned up version***

- Secretmanager needs ``google-cloud-secret-manager`` in ``requirements.txt`` to work!
- The ``compute@developer.gserviceaccount.com`` needs to have the role of **Secret Manager Secret Accessor**
  - Can be granted on IAM overview page (easiest).

  - Can also be granted on Secret Manager page *per secret* by selecting the secrets and then pasting the service account's principal on the **permissions** tab.

  - Disabling or destroying secrets will lead to errors.
    The secret remains as a version and the following code will prompt an error, that the secret is in ``disabled`` or ``destroyed`` state. So by default it will NOT resort to the latest working version.
    ```Python
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    ```

- **Connection/Deployment errors:**
``google.cloud.sql.connector`` needs to be put as ``cloud.sql.connector`` in the requirements! Otherwise deployment will fail!

<br>

>***Leaving some of the following explanations here... However they're not really relevant when using Cloud SQL connector.***

*Temporary failure in name resolution*
```
"Database connection error: could not translate host name "ausbildungmining:europe-west1:ausbildung-mining-postgresql-id" to address: Temporary failure in name resolution"
```
Most likely you're connecting using the connection name. However if VPC is active, you need to use the private IP *(internal IP address)*

*Name or service not known*
```
"Database connection error: could not translate host name "ausbildungmining:europe-west1:ausbildung-mining-postgresql-id" to address: Name or service not known"
```
Cloud Run Service is not connected via VPC.

## 15.02.2025

### Program setup for PostgreSQL

**Secrets management**
- There are some secrets needed to setup the connection later:
  - Project ID
  - Instance connection name *(of the Cloud SQL instance)*
  - Service Account user name
  - Database name
- These secrets could all be stored on GitHub. But they are all GCP-related and changing them for the Cloud Function would require redeployment each time. That's where **Google Secret Manager** comes into play.
- Google Secret Manager will store:
  - Connection name
  - Service Account user name
  - Database name
- Inside of GCP, the Cloud Run Function needs to connect to secret manager to obtain the secrets
- To connect to secret manager it needs the project ID. To not store it in public, the project ID is stored as GitHub secret and handed over to the Cloud Run Function as environment variable.
- The Cloud Run Function can then obtain the project ID at runtime as env-variable. It uses it to get the remaining secrets from secret manager.

>**Some notes about Secret Manager**
>- Secrets can be stored in multiple versions *(like code commits)*
>- Secrets can be *disabled* or *destroyed*
>- **But!** Referencing a disabled or destroyed secret will fail.<br>
Best practice for now: Just add a new version in case the secret changes.

<br>

**Connection Setup in code**
- To connect to SQL, **[Google Cloud SQL Connector](https://pypi.org/project/cloud-sql-python-connector/#configuring-the-connector)** is used
- To connect to PostgreSQL, it needs a database driver ([pg8000](https://pypi.org/project/pg8000/))
- The connection uses IAM authentication inside GCP, so no password is needed

---

### Key-points for SQL connection on GCP

[Official documentation to connect from Cloud Run to Cloud SQL](https://cloud.google.com/sql/docs/postgres/connect-run#public-ip-default_1)

**Cloud SQL/PostgreSQL**
- Public IP needs to be enabled (uses IAM authentication)
- No need for private IP and specific network
- Google Cloud Services authorization *not* needed
- Set SSL mode to *Require trusted clients certificates*

**Cloud Run Function**
- The function connects using *Google Cloud SQL Connector*, *pg8000* and *Google Secrets manager*, hence these 3 need to be in the ``requirements.txt``.
- **Note** that the library name for ``requirements.txt`` might differ from the name used for ``import``!
- No VPC needed!
- *Cloud SQL connections* do *not* need to be specifically set in Cloud Run
- Really everything is handled by Google Cloud SQL connectors.

<br>

>Setup a connectivity test to easily ensure connectivity between Cloud Run and Cloud SQL without the need for redeployment.

*Although Google Cloud SQL Connectors make things very easy, it might get a lot more difficult when dealing with added security or more complex connections...*

---

### Some more PostgreSQL basics

- Select schema
  ```SQL
  SET search_path TO schema_name;
  SELECT * FROM table_name
  ```

- Alternatively use prefix:<br>
  **Note!** *You must use double quotation marks to maintain case-sensitivity here!*
  ```SQL
  -- This works:
  SELECT * FROM "SchemaName".table_name
  -- This DOES NOT work:
  SELECT * FROM SchemaName.table_name
  -- because it gets parsed as:
  SELECT * FROM schemaname.table_name
  ```

- Add new value *(in the sense of "creating" it)*
  ```SQL
  SET search_path TO schema_name;
  INSERT INTO table_name (column_name) VALUES (value_to_add);
  ```

- Say a row with primary key is already created. Then you can't ``INSERT`` a new value for another column of that row. Instead it needs to be *updated*:
  ```SQL
  UPDATE table_name
  SET column_name=column_value
  WHERE index_column=index_value
  ```

- Delete values:
  ```SQL
  DELETE FROM your_table_name
  WHERE your_condition;
  ```

- Check user-rights on specific table:
  *(good for troubleshooting in case e.g. inserts don't work)*
  ```SQL
  SELECT grantee, privilege_type
  FROM information_schema.table_privileges
  WHERE table_schema = schema_name
    AND table_name = table_name; 
  ```

**SQL injection!**<br>
*Beware of SQL injection! Here's an example:*

INSERT EXAMPLE!

**Notes**
- SQLalchemy provides some means so make SQL-statements *pythonic*
- For this you can setup a ``Table``-object and than perform methods on it, like ``table.insert()``


---

### Work notes/summary
- Service Account must be granted rights ***specifically to SQL Table - NOT schema***!

- Also make sure that Service Account has *Cloud SQL Client* and *Cloud SQL instance user* roles in IAM.

- Rights are granted by logging in Cloud SQL studio with *postgres*-user.<br>
  Then ``GRANT ALL ON "SchemaName".table_name TO service_account_name``.

- Check rights to specific table using code-example above!

- Ideally ``sqlalchemy`` expression language is used for access.

- For simple tests make sure to not supply column-name as *sqlalchemy-parameter*. It only works when supplied either directly or using f-string *(beware of sql-injection)*.

- ``commit()``-statement must follow after all ``execute()``-statements or data will not be written to database!

<br>

- ***Established connection and data-transfer from Cloud Run Function to Cloud SQL PostgreSQL database*** 🎉🥳🍻

<br>

**Next steps**
- Add cron-job so Cloud Run Function is executed daily

- Setup dedicated API endpoint for Cloud SQL that handles datatransfer. Should provide the following:

  - Using ``requests.post()`` should enable easy data transfer to database by providing python-dict/JSON data.<br>
  *Example transfer:*
    ```Python
    url = "google.cloud.api-endpoint.mockup.url"
    params = {
      table_name:'official_stats',
      date:datetime.date(2025, 2, 15),
      company_count:5512,
      ...
      total_count:152421
    }
    requests.post(url,params)
    ```
  - In the same way, the endpoint should enable data-extraction using ``requests.get()``

  - For this, the endpoint needs to "deconstruct" the incoming data and pass it to the database. Tables and incoming data need to be correctly structured for this.

  - Dependent on the provided ``table_name`` the endpoint needs to "know what to do"

- Add additional Cloud Run Functions that use the API endpoint to add various new data to the database

- Add data analysis, visualization, dashboard, ML, AI stuff!

---

Okay, I'm quickly adding CRON scheduler!

- Enable **CRON scheduler API**

- Create new job

- Give it a name, select your region

- Use [cron-expression](https://crontab.cronhub.io/) to define interval

- For testing the scheduler uses the public address of the Cloud Run Function

- Apparently **"workflows"** can enable GCP-internal communication between scheduler an Cloud Run Function

- Function now runs daily at 3am CET

## 17.02.2025

### Testing GCP functions locally

- Setup for local development with Google's ``functions-framework``: [Link](https://cloud.google.com/blog/topics/developers-practitioners/how-to-develop-and-test-your-cloud-functions-locally)

- ``functions-framework`` on PyPi: [Link](https://pypi.org/project/functions-framework/)

- Install ``functions-framework`` (see above).

- Run ``functions-framework`` on the function you'd like to test:<br>
  ***Note:** The ``target`` is the entry point of your main-file. This means it refers to a function-name in source-code, not a py-file name!*
  ```bash
  functions-framework --target=main
  ```
  This will start a development-server.

- For super basic testing enter ``http://localhost:8080/`` into a browser to perform a ``GET``-request on the function.

- Seems to be a bit laborious. I'm skipping this for now...

<br>

---

### Setup CI/CD

- I'm using two different YAML-files: ``tests.yml`` and ``deploy.yml``

- ``tests.yml`` performs basic linting, integrity tests etc.<br>
  Is triggered upon pushes to repo or can be triggered manually.

- ``deploy.yml`` deploys functions to GCP.<br>
  It is triggered upon succesful run of ``tests.yml`` or can be triggered manually.

- To reference one workflow from another, ``workflow_run`` is used. [Also look here](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#workflow_run).

- **Note!** When referencing workflows, you need to provide the ``name`` of the workflow used inside the yml-code. Don't use the name of the yml-file!

>*Referencing workflows using ``workflow_run`` only works if the specified workflows are present in the ``main``-branch of the project!*

<br>

---

### Testing

- I'm using ``pylint`` for linting

- Ensure existence of ``__init__.py`` (even if empty) in any directory where py-files are, ***including their parent-directories!***

- Using ``pytests`` for testing

- Use ``os`` and ``sys`` to  manage module-paths, because both ``pylint`` and ``pytest`` sometimes struggle with the filepaths (probably because of multiple drives).

<br>

### Next steps

- Create database API endpoint on GCP (see last notes)
- Maybe add simple scraper for Arbeitsagentur Jobs

## 18.02.2025

- Last night's execution failed because ``def main()`` was missing the input variable!<br>
  ***It needs to be applied, even if it's not used in code!***<br>
  Correct version: ``def main(request)``

- Created project diagram and added to ``README``

- Cloud SQL is ***expensive!*** Reduce costs by starting/stopping instance only for the time of scraping.<br>
To do this, use two Cloud Run Functions with a service account in ``Cloud SQL admin`` role.<br>
These Functions start the instance right before scraping and stop it shortly afterwards.

An example function looks like this:
```Python
from google.cloud import sqladmin

def start_cloud_sql(request):
    client = sqladmin.SqlAdminServiceClient()
    project_id = "your-project-id"  # Replace with your GCP project ID
    instance_name = "your-instance-name"  # Replace with your Cloud SQL instance name

    try:
        # Replace with client.stop to stop instance
        operation = client.start(project=project_id, instance=instance_name)
        operation_name = operation.name
        print(f"Starting Cloud SQL instance: {instance_name}")
        return "Instance start initiated"  # Return success message

    except Exception as e:
        print(f"Error starting Cloud SQL instance: {e}")
        return f"Error: {e}", 500  # Return error message with 500 status code
```

## 19.02.2025

- Python SQL client: https://cloud.google.com/sql/docs/mysql/admin-api/libraries#python

## 21.02.2025

### Handling URL-requests

You can perform typical requests like ``GET`` or ``POST`` on your cloud-function.<br>
To send parameters via URL, you can append them using ``?parameter_name=parameter_value``.

So if your function's URL is<br>
``https://test-func-1234.europe-west1.run.app``<br>
and you wanna pass a parameter ``username``,<br>
then your call would be<br>
``https://test-func-1234.europe-west1.run.app?username=testuser``

Inside the function-code, you can get these parameters using ``.args``.

```Python
import functions_framework

@functions_framework.http
def main(request):
    # Return the value of "username" that's passed by URL
    request_type = request.args.get('username')
    return username,200
```

<br>

---

### Automatically starting/stopping Cloud SQL instance

[This Google tutorial](https://cloud.google.com/blog/topics/developers-practitioners/lower-development-costs-schedule-cloud-sql-instances-start-and-stop) explains how to setup Cloud Run Functions with Pub/Sub and Cloud Scheduler to automate starting and stopping of the Cloud SQL instance.

It's not using Python unfortunately, but it works.<br>
*(Regarding Python: I searched all possible repos, tutorials or forum threads. There's currently no way to set this up with Python as there's no way to setup ``sqladmin`` with Python on GCP)*

## 24.02.2025

### Structure of custom API endpoint

A manual statement currently looks like this:<br>
``INSERT INTO "SchemaName".tableName (columnName) VALUES (:variableName)``

That means a custom API endpoint should receive the following parameters:

- Schema name
- Table name
- Column name(s) and corresponding value(s)

*The database name is stored as Google Secret and hence is not to be changed dynamically. If values should be posted to another database, a second instance using another Secret needs to be used.*

- Some helpful info about mocking a context manager for testing: https://stackoverflow.com/questions/28850070/python-mocking-a-context-manager

<br>

---

This is where GCP tries to connect and authenticate: ``with Connector(refresh_strategy="lazy") as connector:``
