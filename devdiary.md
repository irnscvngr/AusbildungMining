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

<br>

---

### Arbeitsagentur Scraping

- Scraping this page: [Link](https://www.arbeitsagentur.de/jobsuche/suche?angebotsart=1)

- There are 4 types of vacancies:
  - 1 - ``Arbeit``
  - 2 - ``Ausbildung/Duales Studium``
  - 3 - ``Praktikum/Trainee/Werkstudent``
  - 4 - ``Selbstständigkeit``

- Using hidden API - results are returned as JSON!

- Primary keys are:<br>
*(secondary keys sublisted)*
  - ``stellenangebote``
  - ``maxErgebnisse`` - the total number of vacancies per type
  - ``page``
  - ``size``
  - ``facetten`` - Contains detailed lists, like vacancy count per city, industry etc.
    - ``befristung``
      - ``1`` - befristet
      - ``2`` - unbefristet
      - ``3`` - keine Angabe
    - ``externestellenboersen``
    - ``branche``
    - ``beruf``
    - ``arbeitsort``
    - ``arbeitgeber``
    - ``veroeffentlichtseit``
    - ``arbeitszeit``
      - ``ho`` - Home Office
      - ``mj`` - Minijob
      - ``snw`` - Schicht/Nacht/Wochenende
      - ``tz`` - Teilzeit
      - ``vz`` - Vollzeit
    - ``arbeitsort_plz``

- ``branche``
  ```Python
  {
    "1":"Bau, Architektur",
    "2":"Chemie, Pharma, Biotechnologie",
    "3":"Elektro, Feinmechanik, Optik, Medizintechnik",
    "4":"Bildung, Erziehung, Unterricht",
    "5":"Fahrzeugbau, Fahrzeuginstandhaltung",
    "6":"Banken, Finanzdienstleistungen, Immobilien, Versicherungen",
    "7":"Gesundheit, Soziales",
    "8":"Rohstoffverarbeitung, Glas, Keramik, Kunststoff, Holz"
    "9":"Einzelhandel, Großhandel, Außenhandel",
    "10":"Hotel, Gaststätten, Tourismus, Kunst, Kultur, Freizeit",
    "11":"IT, Computer, Telekommunikation",
    "12":"Landwirtschaft, Forstwirtschaft, Gartenbau",
    "13":"Management, Beratung, Recht, Steuern",
    "14":"Medien, Informationsdienste",
    "15":"Metall, Maschinenbau, Anlagenbau",
    "16":"Konsum- und Gebrauchsgüter",
    "17":"Nahrungs- / Genussmittelherstellung",
    "18":"Öffentlicher Dienst, Organisationen",
    "19":"Papier, Druck, Verpackung",
    "20":"Rohstoffgewinnung, Rohstoffaufbereitung",
    "21":"Logistik, Transport, Verkehr",
    "22":"Abfallwirtschaft, Energieversorgung, Wasserversorgung",
    "23":"Sicherheits-, Reinigungs- oder Reparaturdienstleistungen",
    "24":"Werbung, Öffentlichkeitsarbeit",
    "25":"Wissenschaft, Forschung, Entwicklung",
    "26":---
    "27":"Arbeitsvermittlung, privat",
    "28":"Arbeitnehmerüberlassung, Zeitarbeit",
    "29":"Sonstige Dienstleistungen",
   }
  ```

## 23.02.2025

- A quick check shows: Starting/Stopping the SQL instance to write new values over night works!



## 24.02.2025

### Structure of custom API endpoint

>**Remember!** The service account running the API endpoint needs to be granted write-priviliges on the respective database-table for everything to work!

A manual statement currently looks like this:<br>
``INSERT INTO "SchemaName".tableName (columnName) VALUES (:variableName)``

A custom API endpoint should receive the following parameters:

- Schema name
- Table name
- Column name(s) and corresponding value(s)

*The database name is stored as Google Secret and hence is not to be changed dynamically. If values should be posted to another database, a second instance using another Secret needs to be used.*

<br>

---

### Some words about testing

Some helpful info about mocking a context manager for testing: https://stackoverflow.com/questions/28850070/python-mocking-a-context-manager

**Linting**
- To keep linting from breaking your deploying don't just use ``pylint``.
- Instead, use ``pylint --fail-under=8`` to use a threshold for code-quality
- Otherwise it will only work if the code is 10/10

<br>

**GCP authentication**
- Since GitHub runs the code on it's own virtual machine, GCP authentication will not work
- This is where GCP tries to connect and authenticate: ``with Connector(refresh_strategy="lazy") as connector:``
- The failed authentication will throw an error and fail your test
- Use the following (for an example function located in ``database_endpoint``) to correctly mock the GCP ``Connector``:
  ```Python
  mock_connector = Mock()
  mock_connector.__enter__ = mock_connector
  mock_connector.__exit__ = mock_connector
  con_mock = mocker.patch('database_endpoint.Connector',return_value=mock_connector)
  ```
- Print the ``Connector`` object in your function and check if it's returning the ``Mock``-class. You can test this locally without uploading to GitHub. If it's not the ``Mock``-class, GCP will try to authenticate and fail on GitHub!

<br>

---

<br>

- Add "proper" API key to access API endpoint from local dev-environment

- Take care of access management (other cloud functions to API endpoint)

## 25.02.2025

A helpful documentation on service-to-service connection on GCP:
https://cloud.google.com/run/docs/authenticating/service-to-service#run-service-to-service-example-python

Also a bit helpful, but not 100%:<br>
https://cloud.google.com/run/docs/securing/private-networking#from-other-services

That's also interesting but potentially not needed.<br>
As I understand it, *private service connect* is only needed if you wanna build connections between two VPCs or two GCP projects.<br>
https://cloud.google.com/vpc/docs/configure-private-service-connect-apis

---

### Connecting two cloud run services

To connect a Cloud Run Service to another, the following must be set:

- The receiving service must be set to **Internal Ingress** (found under ``NETWORKING``).

- Under security ``SECURITY`` set authentication to **Require authentication**

- For the sending service, select ``EDIT & REDEPLOY``. Then under ``NETWORKING`` activate **Connect to a VPC for outbound traffic**.

-  Activate **Use Serverless VPC Access connectors** (might maybe also work for *
Send traffic directly to a VPC*). Then select the default network.

- For **Traffic routing** select **Route all traffic to the VPC**.

- Make sure both services use the correct service accounts at runtime! The service account of the sending service needs the **Cloud Run Invoker** role.

- The VPC has a subnet that can be selected when setting *Connect to a VPC for outbound traffic*. This subnet needs **Private Google Access** to be activated (possible under VPC-settings->subnets->and then the subnet for the corresponding region, e.g. 
europe-west1).<br><br>
It might be that this is not needed when using *serverless VPC access connectors*. Need to check the whole procedure again...

- Now a general connection should be possible, however you might still receive an authentication error. This is because besides being connected through VPC, the calling service still needs to send an **ID token**.<br>
Check [here](https://cloud.google.com/run/docs/authenticating/service-to-service#use_the_authentication_libraries) under **use the authentication libraries** on how to make the calling service provide that ID token.

- Now the connection should generally work. You can test it by adding ``auth_header = request.headers.get("Authorization")`` to the called service and having it print that ``auth_header``, then check the logs (not elegant, but works).

<br>

---

You might stumble upon this error:
```
TypeError: The view function did not return a valid response. The return type must be a string, dict, list, tuple with headers or status, Response instance, or WSGI callable, but it was a Response.
```
This happens when your Cloud Run Function does not send the proper return-value.<br>
Try out a standard response like:
```Python
return "Hello World!",200
```
This should work. **Careful!** What *-does not-* work is chaining responses!<br>
So imagine having a function A returning something like this:
```Python
return "This is a response from function A", 200
```
And then in another function B using that very same response as return:
```Python
response = requests.get(url,headers=headers,timeout=20)
return response
```
**This** will lead to exactly the error mentioned above!

That's because ``requests.get()`` returns a ``requests.response`` object, which is none of the valid types listed in the error message above.<br>
You might say ``Response instance`` counts, but this refers to a ``Flask`` response. That's the reason you can not just chain responses as shown above.

---

### Cloud Run Service connection summed up

- It's all about setting up authentication again:
  - VPC
  - Service account role
  - ID token for IAM authentication

- The called service's URL is used twice: As so called audience (that's a result of the "require authentication" security setting) and as actual service-URL to connect

- All cloud functions to connect with the DB endpoint will need to provide the ID token.

- The DB endpoint URL is stored as google secret.

- Maybe generate ``headers`` containing the ID token in a separate function to declutter code.

- **REMEMBER** For all new type of data, a separate table needs to be created on Cloud SQL. For these tables the service account of DB endpoint needs to be granted access rights!

<br>

---

## 26.02.2025

### The continued story of service connectivity

Okay so to connect a service to another service (that is set to internal ingress only), there are 4 possible setup-options. However the services also need to be able to connect to the public internet. Let's see:

| | ``Send traffic``<br>``directly to a VPC`` | ``Use Serverless VPC``<br>``Access connectors`` |
| --- | --- | --- |
| ``Route only requests to``<br>``private IPs to the VPC`` | Public internet: ✔<br>Internal connect: ❌ | Public internet: ✔<br>Internal connect: ❌ |
| ``Route all traffic to the VPC`` | Public internet: ❌<br>Internal connect: ✔ | Public internet: ❌<br>Internal connect: ✔ |

*Apparently using a serverless VPC access connector is not necessary for service-to-service connections!*

<br>

The following tutorial explains how to setup a service-to-service connection while also maintaining a public internet connection:<br>
*It works! But it's using ``gloud`` CLI...*

https://codelabs.developers.google.com/codelabs/how-to-access-internal-only-service-while-retaining-internet#2

#### About DNS zoning

So apparently it works like this:

- The calling service is set to:
  - ``Send traffic directly to a VPC``
  - ``Route only requests to private IPs to the VPC``

- This means (as I understand) that traffic is generally send to the VPC, however only requests that are resolved to private IPs are actually routed to the VPC.

- When the service sends requests to a domain (say ``https://www.example.com``) this domain gets resolved into an IP address.<br>
GCP then checks if this IP address counts as private or public. For this example the IP is public and the request would "travel" to the public web.

- If the calling service would be set to ``Route all traffic to the VPC`` then even though ``https://www.example.com`` is public, the request would be "trapped" inside the VPC which usually results in a timeout-error.

- The problem: The service we are trying to call is set ``Internal Ingress``, meaning it only allows access to requests coming from internal/private addresses.

- When we call the service with it's ``*.run.app``-URL the domain is **not** resolved into a private IP. This means the request is also **not** routed through the VPC, but "travels" through the public internet. Hence the service we are calling receives a **public** request, which of course does not work. This results in an error.

- This sounds as if both routing only requests to private IP to VPC **as well as** routing **all** traffic to VPC does not work. Enter: DNS zones!

#### Setup DNS zoning

- So we set the calling service to ``Send traffic directly to a VPC``.<br>
  Then using Cloud DNS we create a new DNS zone of type *private*.<br>

- The DNS name is the ``*.run.app``-URL of our service, *but **without** ``https:// ``* in the beginning.<br>
So just: ``SERVICE-NAME-PROJECT-ID.REGION-NAME.run.app``

- We can leave ``Options`` at default (private).

- Then we add our network (usually ``default``) to the new DNS zone.

- This now means, that the ``*.run.app``-URL of our service gets resolved into a *private* IP address by GCP, which is important!<br>
As I said earlier, if it's not resolved to be private (which happens by default), it becomes a public IP which won't work with our private service.

- **But:** This will still not work.<br>
  Apparently our new zone needs a type ``A`` record-set *(whatever that is!)*.

- Fortunately, this also happens in the tutorial linked above.<br>
  So, what to do? Click on the newly created DNS zone.

- It should display two record-sets, of type ``SOA`` and type ``NS``. Clicking ``Add Standard`` allows us to add an additional set.

- For DNS name we - again - choose our service's ``*.run.app``-URL, which should already be entered for us (so actually we do not need to paste it again).

- ``Resource record type`` must of course be set to ``A`` now.

- ``TTL`` is apparently some type of cache and we can set a storage duration. The tutorial says 60 minutes, however I've had it set to 5 min. (default value) and it still worked.

- Now comes the tricky part:<br>
  We need to add 4 IP addresses to this new record set *(where ever they're coming from - I don't know!)*<br>
  These IP addresses are:
  - ``199.36.153.8``
  - ``199.36.153.9``
  - ``199.36.153.10``
  - ``199.36.153.11``

- After adding these addresses we can try and execute our calling service again. It should now successfully be able to call **both** the internal, private service **and** a public URL on the internet.<br>
*Remember that the calling service still needs to authenticate itself using ``google-auth``!*

<br>

---

### Using a VM for troubleshooting

- You can create a new VM in GCP

- Click on the VM and under ``DETAILS`` -> ``Network interfaces`` check if the VM is using the VPC-network

- Click on the VM and use SSH to open a terminal (just click on ``SSH``)

- Enter ``Python3 --version`` to check the python version
  - Should Python not be installed:
    ```Bash
    sudo apt update
    sudo apt install python3 python3-pip
    ```

- Enter ``Python3`` to start Python

- Import ``requests``, then enter ``requests.get("https://curlmyip.org/", timeout=20)`` to check if the VM can perform a public connection (meaning ``Response[200]``)

<br>

>***ALWAYS MAKE SURE TO STOP THE VM TO AVOID COSTS!!!***

- Try to resolve the hostname of the Cloud Run service (the one with internal access only):<br>
  - First, update the machine and install ``dnsutils``:
    ```Bash
    sudo apt update
    sudo apt install dnsutils
    ```
  - Then, execute the following:<br>
  ``nslookup SERVICE-NAME-PROJECT-ID.europe-west1.run.app``<br>
  ``dig SERVICE-NAME-PROJECT-ID.europe-west1.run.app``<br>

  - If you've setup VPC and DNS zoning succesfully, the first command should return:<br>
    *(of course with respective naming instead of those placeholders)*
    ```Bash
    Server:         127.0.0.53
    Address:        127.0.0.53#53

    Non-authoritative answer:
    Name:   SERVICE-NAME-PROJECT-ID.REGION-NAME.run.app
    Address: 199.36.153.10
    Name:   SERVICE-NAME-PROJECT-ID.REGION-NAME.run.app
    Address: 199.36.153.9
    Name:   SERVICE-NAME-PROJECT-ID.REGION-NAME.run.app
    Address: 199.36.153.8
    Name:   SERVICE-NAME-PROJECT-ID.REGION-NAME.run.app
    Address: 199.36.153.11
    ```

>***ALWAYS MAKE SURE TO STOP THE VM TO AVOID COSTS!!!***

<br>

---

Some final words and summary of the connection process:

- Private connection from service to service needs VPC!

- The VPC's subnet needs to have *Private Google Access* enabled

- If only private connection is needed, it's sufficient to set the calling service to use direct ingress via VPC and route **all** outbound traffic to VPC.

- The calling service's service account needs the *Cloud Run Invoker* role.

- If the calling service shall also be able to call the public internet, some adjustments are needed:
  - The calling service still uses direct ingress via VPC.
  - But it routes only traffic to private IPs to VPC.
  - To make this possible, a DNS zone needs to be created in the VPC.

## 27.02.2025

### Yay, new errors! Deployment fails

Error message:
```
ERROR: (gcloud.functions.deploy) ResponseError: status=[409], code=[Ok], message=[Could not create Cloud Run service ba-official-stats. A Cloud Run service with this name already exists. Please redeploy the function with a different name.]
```

Need to add ``--no-gen2 \`` as flag to ``gcloud functions deploy`` because it now adds ``--gen2`` by default to new deployments (GCP went from Cloud Functions to Cloud **Run** Functions only a few days ago...).<br>
My existing functions are thereby ``gen1`` and I guess that's why it fails to update with ``gen2``.

-> Now deployment does not fail, however cloud run function is **not** updated!

<br>

---

### Grants on Postgres to successful write to tables

The service account of the database endpoint needs to have access to **both** the schema **and** table to be able to write data.

That means:

```SQL
GRANT ALL ON SCHEMA "SchemaName" TO "service-acc@mail-address.iam"
GRANT ALL ON TABLE "SchemaName".TableName TO "service-acc@mail-address.iam"
```

## 28.02.2025

### Some words on Streamlit

Say a repo structure is like this:
```
my-repo/
├── README.md
├── cloud_functions/
│   ├── foo.py
│   └── bar.py
├── streamlit_folder/
│   ├── main.py
│   ├── requirements.txt
│   └── data/
│       └── testdata.csv
└── devdiary.md
```

Then streamlit launches the app like this:
```
streamlit run streamlit_folder/main.py
```
Which means for streamlit, root equals repo-root.<br>
That means filepaths **don't** start on the level of the streamlit-subfolder.

If you'd want to access ``testdata.csv`` in the example-structure above, the path would be ``streamlit_folder/data/testdata.csv``.
<br>
<br>

**Module loading errors**

There might be an error where the frontend py-file wants to load a function from the backend and streamlit says "no attribute", e.g. like:
```
module 'streamlit_backend' has no attribute 'add_geoinfo_to_vacancies'
```
That might be due to caching.

On the streamlit-app-page's upper right corner click the three dots icon and choose ``Clear cache (C)``.

Then in the lower right corner click ``Manage app``, then click the three dots icon and choose ``Reboot app``.

That should get rid of the import error.


<br>

---

### Cloud Run Functions

- Somehow updating the scraper for Bundesagentur für Arbeit stopped working.

- I blame this on Google updating from Cloud Functions + Cloud Run to Cloud **Run** Functions only.

- Problems:
  - Couldn't use IAM authenticated access because audience was always `None`.
  - Only had ``run.app`` URLs.
  - Deployment via GitHub actions displayed as successful, however no actual new revisions on GCP.

- Deployed a completely new function under new name and now everything runs smoothly.

- Here's the reference for ``gcloud`` CLI:
  https://cloud.google.com/sdk/gcloud/reference/functions/deploy

<br>

---

### PostreSQL

- Column names:<br>
  *(Source: https://www.postgresql.org/docs/7.0/syntax525.htm)*
  - must begin with letter (a-z) or underscore (_)
  - subsequent characters can be letters, digits (0-9) or underscores
  - default max. length of names is 31

<br>

---

### Additional notes

- curlmyip.org had a bad certificate! Hence public requests failed. Replaced it with ``https://www.example.com`` - now it works again!

<br>

## 02.03.2025

- Fixed Streamlit app (didn't load backend, see "Module loading errors" above)

- Added custom theme to streamlit app

- Added state-specific scraping to BA_scraping, but need to finish

## 03.02.2025

### A flexible PostgreSQL table for future scraping

Currently tables have "date" (being date *and* time) as primary key. This means there can always be just one row per timestamp.

Adding e.g. vacancies for all German states for a specific timestamp won't work this way. Instead, the following sort of table should be used:

```SQL
CREATE TABLE "SchemaName".mock_table (
id SERIAL PRIMARY KEY,
-- timestamp DATE, (this allows for date only)
timestamp TIMESTAMP WITHOUT TIME ZONE, -- date AND time
branche_a INTEGER,
branche_b INTEGER
);
```

This creates a table with an "id"-column that automatically increments for each new insert.

| id  | timestamp | branche_a | branche_b |
| --- | --- | --- | --- |
| - | - | - | - |


You can enter specific values directly *(which is unlikely, but just to show it)*:

```SQL
INSERT INTO "SchemaName".mock_table(branche_a) VALUES (25);
```

| id  | timestamp | branche_a | branche_b |
| --- | --- | --- | --- |
| 1 | - | 25 | - |

As you see, id starts with 1. Let's add another value:

```SQL
INSERT INTO "SchemaName".mock_table(branche_b) VALUES (67);
```

| id  | timestamp | branche_a | branche_b |
| --- | --- | --- | --- |
| 1 | - | 25 | - |
| 2 | - | - | 67 |

Okay, now let's add a proper row:

```SQL
INSERT INTO "SchemaName".mock_table(timestamp,branche_a,branche_b) VALUES (CURRENT_DATE, 12345, 54321);
```

| id  | timestamp | branche_a | branche_b |
| --- | --- | --- | --- |
| 1 | - | 25 | - |
| 2 | - | - | 67 |
| 3 | 2025-03-03T06:24:46.478891Z | 12345 | 54321 |

Nice thing is, we can also alter the table after it's creation. Let's add another column:

```SQL
ALTER TABLE "SchemaName".mock_table
ADD COLUMN branche_c INTEGER;
```

We'll add a value to the new column and inspect the results:

```SQL
INSERT INTO "SchemaName".mock_table(timestamp,branche_a,branche_b,branche_c) VALUES (CURRENT_DATE, 12345, 54321,777);
```

| id  | timestamp | branche_a | branche_b | branche_c |
| --- | --- | --- | --- | --- |
| 1 | - | 25 | - | - |
| 2 | - | - | 67 | - |
| 3 | 2025-03-03T06:24:46.478891Z | 12345 | 54321 | - |
| 4 | 2025-03-03T06:26:48.478891Z | 12345 | 54321 | 777 |