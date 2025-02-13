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
