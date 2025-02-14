# Dev Diary

## 08.02.25
- Setup Workspace
- Init Git
- Create repo
- Add readme
- Add changelog

## 10.02.25
- Finally got deployment to GCP running!
- Main take aways:
  - IAM is difficult!
  - Gemini is only helpful max. 50% of the time
  - Write everything down! (Check CloudFunctionDeployTutorial)
 
## 11.02.25
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
    -- Create new table
    CREATE TABLE official_stats (
    date DATE PRIMARY KEY,
    feature1 INTEGER,
    feature2 INTEGER,
    feature3 INTEGER
    );
    ```

- **Writing to PostgreSQL database from Cloud Run Function**:
  - Cloud Run Service Account needs *Cloud SQL Client* role.
  - Add user to database, select *Cloud IAM*, then copy principal from service account and paste.
  - User needs to be granted priviliges to query or modify database, see [here](https://cloud.google.com/sql/docs/postgres/add-manage-iam-users#grant-db-privileges)
  - Grant service account full priviliges on the database *(careful!)*

    Note: Don't use full service account e-mail here! Use user name as it is displayed in the Users-overview of the database (ending on \*.iam)
    ```PostgreSQL
    GRANT ALL ON SCHEMA "AusbildungMining" TO "service@account.mail"
    ```
  - Use Cloud Secret Manager to store service account credentials (email, database name, cloud sql connection name)
    - SERVICE_ACCOUNT_USER_NAME (== email ending on \*.iam)
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
- Secretmanager needs ``google-cloud-secret-manager`` in ``requirements.txt`` to work!
- The ``compute@developer.gserviceaccount.com`` needs to have the role of **Secret Manager Secret Accessor**
  - Can be granted on IAM overview page (easiest).

  - Can also be granted on Secret Manager page *per secret* by selecting the secrets and then pasting the service account's principal on the **permissions** tab.

  - Disabling or destroying secrets will lead to errors.
    The secret remains as a version and the following code will prompt an error, that the secret is in ``disabled`` or ``destroyed`` state. So by default it will NOT resort to the latest working version.
    ```Python
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    ```
  
  - Setup connection between Cloud Run Function and PostgreSQL:

    - In PostgreSQL **Connections->NETWORKING**:
      - Activate *Private IP*. You'll create a new *default* network (might take up to 5/6 min. to complete)
      - Enable Google Cloud services authorization/Enable private path
    
    - In PostgreSQL **Connections->SUMMARY**:
      - Private IP connectivity should now be *Enabled*
      - There should be an Internal IP address visible

    - In your **Cloud Run Function->EDIT**:
      - Go to *Runtime, build, connections and security settings*
      - Then go to *CONNECTIONS*
      - Under *Egress settings*, **ADD NEW VPC CONNECTOR**
      - Give it an arbitrary name (e.g. ``vpc-connector``), select the newly created *default* network
      - As subnet choose *Custom IP Range* and for *IP range* enter the suggested ``10.8.0.0/28``
      - Finally choose *Route only requests to private IPs through the VPC connector*
      - Deploy a new revision of your function

    - In PostgreSQL **CONNECTIVITY TESTS**:
      - Create a new test
      - Give it an arbitrary name (e.g. ``test-cloud-run``)
      - Set *Source* to *Other*, *Source endpoint* to *Cloud Run* and as *Cloud Run service* select your Cloud Run Function
      - Set *Destination* to *Current Cloud SQL Instance* and as port choose ``5432`` (apparently default PostgreSQL port)
      - Run the test
      - If succesful, test should end with *trace0 - Packet could be delivered*
      - Make sure to use the latest revision of your Cloud Run Function. The test might still be set to an older variant that wasn't setup correctly and fail!

    - **Secrets**:
      - ``DATABASE_NAME`` - The actual name of the database
      - ``DATABASE_PASSWORD`` - The general password to access the DB (not a user's PW)
      - ``DATABASE_CONNECTION_NAME`` - The internal IP address (listed under *Private IP connectivity*)
      - ``SERVICE_ACCOUNT_USER_NAME`` - The custom service account's principal
  
    SERVICE_ACCOUNT_USER_NAME is wrong!!! You need to use the database account's id that is related to the database password!

- **Connection errors:**
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