import json

import requests
import time
import os
from dotenv import load_dotenv

API_URL_PAYMENT_METHODS = 'https://api.redislabs.com/v1/payment-methods'
API_URL_FIXED_SUBSCRIPTIONS = 'https://api.redislabs.com/v1/fixed/subscriptions'
API_URL_ACL_ROLES = 'https://api.redislabs.com/v1/acl/roles'
API_URL_ACL_USERS = 'https://api.redislabs.com/v1/acl/users'

# Load environment variables
load_dotenv()

API_KEY = os.getenv('REDIS_CLOUD_API_KEY', 'hardcoded-api-key')
API_SECRET_KEY = os.getenv('REDIS_CLOUD_API_SECRET_KEY', 'hardcoded-api-secret-key')

# Hardcoded variables
PAYMENT_METHOD_ID = 25346
PLAN_ID = 21113
SUBSCRIPTION_NAME = "Essentials - Gabs CF"
DATABASE_NAME = "gabs-fixed-database-example"
ROLE_NAME = "bart-via-api"
USER_NAME = "bart-via-api"
USER_PASSWORD = "Secret@99"


def get_payment_methods():
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    response = requests.get(API_URL_PAYMENT_METHODS, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def create_fixed_subscription(plan_id, payment_method_id):
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "name": SUBSCRIPTION_NAME,
        "planId": plan_id,
        "paymentMethodId": payment_method_id
    }

    response = requests.post(API_URL_FIXED_SUBSCRIPTIONS, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"Failed to create subscription. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def check_task_status(task_url):
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    while True:
        response = requests.get(task_url, headers=headers)
        if response.status_code == 200:
            task_status = response.json()
            status = task_status.get('status')
            if status == 'processing-completed':
                return task_status
            elif status in ['received', 'processing', 'processing-in-progress']:
                print(f"Task is still processing: {status}")
                time.sleep(5)
            elif status == 'processing-error':
                raise Exception(
                    f"Task failed with status: {status}. Error details: {task_status.get('response', {}).get('error', {}).get('description', 'No details provided')}")
            else:
                raise Exception(f"Unexpected task status: {status}")
        else:
            response.raise_for_status()


def wait_for_subscription_active(subscription_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            subscription_status = response.json()
            status = subscription_status.get('status')
            if status == 'active':
                return subscription_status
            elif status in ['pending', 'provisioning']:
                print(f"Subscription status: {status}. Waiting for it to become active...")
                time.sleep(10)
            else:
                raise Exception(f"Subscription cannot become active. Current status: {status}")
        else:
            response.raise_for_status()


def wait_for_database_ready(subscription_id, database_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}/databases/{database_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            database_status = response.json()
            status = database_status.get('status')
            if status == 'active':
                return database_status
            elif status in ['pending', 'provisioning', 'draft']:
                print(f"Database status: {status}. Waiting for it to become active...")
                time.sleep(10)
            else:
                raise Exception(f"Database cannot become active. Current status: {status}")
        else:
            response.raise_for_status()


def create_database(subscription_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}/databases"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "name": DATABASE_NAME,
        "protocol": "stack",
        "dataPersistence": "aof-every-1-second",
        "dataEvictionPolicy": "allkeys-lru",
        "replication": False,
        "enableTls": True,
        "password": "vamos-desativar-o-user-default-anyway",
        "alerts": [
            {
                "name": "datasets-size",
                "value": 80
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"Failed to create database. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def disable_default_user(subscription_id, database_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}/databases/{database_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "enableDefaultUser": False
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"Failed to disable default user. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def create_role(subscription_id, database_id):
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "name": ROLE_NAME,
        "redisRules": [
            {
                "ruleName": "Full-Access",
                "databases": [
                    {
                        "subscriptionId": subscription_id,
                        "databaseId": database_id,
                        "regions": []
                    }
                ]
            }
        ]
    }

    response = requests.post(API_URL_ACL_ROLES, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"Failed to create role. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def create_user(role_name):
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY,
        'Content-Type': 'application/json'
    }
    data = {
        "name": USER_NAME,
        "role": role_name,
        "password": USER_PASSWORD
    }

    response = requests.post(API_URL_ACL_USERS, headers=headers, json=data)

    if response.status_code == 202:
        return response.json()
    else:
        print(f"Failed to create user. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def get_database_details(subscription_id, database_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}/databases/{database_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Failed to get database details. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def main():
    try:
        # Fetching and printing payment methods
        payment_methods = get_payment_methods()
        print("Payment Methods:")
        for method in payment_methods['paymentMethods']:
            print(f"ID: {method['id']}, Type: {method['type']}, Ends With: {method['creditCardEndsWith']}")

        # Creating fixed subscription
        subscription_response = create_fixed_subscription(PLAN_ID, PAYMENT_METHOD_ID)
        task_url = subscription_response['links'][0]['href']
        print(f"Subscription creation task started. Task URL: {task_url}")

        # Checking subscription creation task status
        task_status = check_task_status(task_url)
        subscription_id = task_status['response']['resourceId']
        print(f"Subscription created successfully with ID: {subscription_id}")

        # Waiting for subscription to become active
        wait_for_subscription_active(subscription_id)
        print(f"Subscription with ID {subscription_id} is now active.")

        # Creating database
        database_response = create_database(subscription_id)
        task_url = database_response['links'][0]['href']
        print(f"Database creation task started. Task URL: {task_url}")

        # Checking database creation task status
        task_status = check_task_status(task_url)
        database_id = task_status['response']['resourceId']
        print("Database creation task completed successfully.")
        print(task_status)

        # Waiting for database to become active
        wait_for_database_ready(subscription_id, database_id)
        print(f"Database with ID {database_id} is now active.")

        # Waiting for subscription to become active
        wait_for_subscription_active(subscription_id)
        print(f"Subscription with ID {subscription_id} is now active.")

        # Getting database details
        database_details = get_database_details(subscription_id, database_id)
        database_url = database_details['publicEndpoint']

        # Disabling default user
        disable_user_response = disable_default_user(subscription_id, database_id)
        task_url = disable_user_response['links'][0]['href']
        print(f"Disabling default user task started. Task URL: {task_url}")

        # Checking disable default user task status
        task_status = check_task_status(task_url)
        print("Default user disabling task completed successfully.")
        print(task_status)

        # Waiting for subscription to become active
        wait_for_subscription_active(subscription_id)
        print(f"Subscription with ID {subscription_id} is now active.")

        # Creating role
        role_response = create_role(subscription_id, database_id)
        task_url = role_response['links'][0]['href']
        print(f"Role creation task started. Task URL: {task_url}")

        # Checking role creation task status
        task_status = check_task_status(task_url)
        print("Role creation task completed successfully.")
        print(task_status)

        # Waiting for subscription to become active
        wait_for_subscription_active(subscription_id)
        print(f"Subscription with ID {subscription_id} is now active.")

        # Creating user
        user_response = create_user(ROLE_NAME)
        task_url = user_response['links'][0]['href']
        print(f"User creation task started. Task URL: {task_url}")

        # Checking user creation task status
        task_status = check_task_status(task_url)
        print("User creation task completed successfully.")
        print(task_status)

        # Waiting for subscription to become active
        wait_for_subscription_active(subscription_id)
        print(f"Subscription with ID {subscription_id} is now active.")

        # Output the final JSON object
        output = {
            "subscription_id": subscription_id,
            "database_id": database_id,
            "database_url": database_url,
            "user": USER_NAME,
            "password": USER_PASSWORD
        }

        print(json.dumps(output, indent=4))

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
