import requests
import time
import os
from dotenv import load_dotenv

API_URL_FIXED_SUBSCRIPTIONS = 'https://api.redislabs.com/v1/fixed/subscriptions'
API_URL_ACL_ROLES = 'https://api.redislabs.com/v1/acl/roles'
API_URL_ACL_USERS = 'https://api.redislabs.com/v1/acl/users'

# Load environment variables
load_dotenv()

API_KEY = os.getenv('REDIS_CLOUD_API_KEY', 'hardcoded-api-key')
API_SECRET_KEY = os.getenv('REDIS_CLOUD_API_SECRET_KEY', 'hardcoded-api-secret-key')

# Get input variables from the environment or default values
subscription_id = os.getenv('SUBSCRIPTION_ID', '2361978')
database_id = os.getenv('DATABASE_ID', '12391054')
user_name = os.getenv('USER_NAME', 'bart-via-api')
role_name = os.getenv('ROLE_NAME', 'bart-via-api')


def delete_user(user_id):
    url = f"{API_URL_ACL_USERS}/{user_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    print(f"Attempting to delete user with ID: {user_id}")
    response = requests.delete(url, headers=headers)
    if response.status_code == 202:
        print(f"User with ID {user_id} deleted successfully")
        return response.json()
    else:
        print(f"Failed to delete user. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def delete_role(role_id):
    print(f"Deleting role with ID: {role_id}")
    url = f"{API_URL_ACL_ROLES}/{role_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    print(f"Attempting to delete role with ID: {role_id}")
    response = requests.delete(url, headers=headers)
    if response.status_code == 202:
        print(f"Role with ID {role_id} deleted successfully")
        return response.json()
    else:
        print(f"Failed to delete role. Status Code: {response.status_code}, Response: {response.content}")
        if response.status_code == 405:
            print("405 Method Not Allowed: The HTTP method used is not supported for this URL.")
        response.raise_for_status()


def delete_database(subscription_id, database_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}/databases/{database_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    print(f"Attempting to delete database with ID: {database_id}")
    response = requests.delete(url, headers=headers)
    if response.status_code == 202:
        print(f"Database with ID {database_id} deleted successfully")
        return response.json()
    else:
        print(f"Failed to delete database. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def delete_subscription(subscription_id):
    url = f"{API_URL_FIXED_SUBSCRIPTIONS}/{subscription_id}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    print(f"Attempting to delete subscription with ID: {subscription_id}")
    response = requests.delete(url, headers=headers)
    if response.status_code == 202:
        print(f"Subscription with ID {subscription_id} deleted successfully")
        return response.json()
    else:
        print(f"Failed to delete subscription. Status Code: {response.status_code}, Response: {response.content}")
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


def get_user_id_by_name(user_name):
    url = f"{API_URL_ACL_USERS}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users = response.json().get('users', [])
        for user in users:
            if user['name'] == user_name:
                return user['id']
        raise Exception(f"User with name {user_name} not found.")
    else:
        print(f"Failed to get users. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def get_role_id_by_name(role_name):
    url = f"{API_URL_ACL_ROLES}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        roles = response.json().get('roles', [])
        for role in roles:
            if role['name'] == role_name:
                return role['id']
        raise Exception(f"Role with name {role_name} not found.")
    else:
        print(f"Failed to get roles. Status Code: {response.status_code}, Response: {response.content}")
        response.raise_for_status()


def wait_for_role_users_empty(role_name):
    print(f"Checking if role {role_name} still has users...")
    url = f"{API_URL_ACL_ROLES}"
    headers = {
        'x-api-key': API_KEY,
        'x-api-secret-key': API_SECRET_KEY
    }

    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            roles = response.json().get('roles', [])
            role = next((r for r in roles if r['name'] == role_name), None)
            if role:
                users = role.get('users', [])
                if not users:
                    print(f"No users found in role {role_name}.")
                    return
                else:
                    print(f"Role {role_name} still has users: {users}. Waiting for users to be removed...")
                    time.sleep(5)
            else:
                raise Exception(f"Role with name {role_name} not found.")
        else:
            response.raise_for_status()


def main():
    try:
        # Get user ID by name
        user_id = get_user_id_by_name(user_name)
        print(f"User ID for {user_name} is {user_id}")

        # Get role ID by name
        role_id = get_role_id_by_name(role_name)
        print(f"Role ID for {role_name} is {role_id}")

        # Deleting user
        user_response = delete_user(user_id)
        task_url = user_response['links'][0]['href']
        print(f"User deletion task started. Task URL: {task_url}")

        # Checking user deletion task status
        task_status = check_task_status(task_url)
        print("User deletion task completed successfully.")
        print(task_status)

        # Wait for role users to be empty
        wait_for_role_users_empty(role_name)

        # Wait for subscription to become active
        wait_for_subscription_active(subscription_id)

        # Deleting role
        role_response = delete_role(role_id)
        print(f"Role response: {role_response}")
        task_url = role_response['links'][0]['href']
        print(f"Role deletion task started. Task URL: {task_url}")


        # Checking role deletion task status
        task_status = check_task_status(task_url)
        print("Role deletion task completed successfully.")
        print(task_status)

        # Wait for subscription to become active
        wait_for_subscription_active(subscription_id)

        # Deleting database
        database_response = delete_database(subscription_id, database_id)
        task_url = database_response['links'][0]['href']
        print(f"Database deletion task started. Task URL: {task_url}")

        # Checking database deletion task status
        task_status = check_task_status(task_url)
        print("Database deletion task completed successfully.")
        print(task_status)

        # Wait for subscription to become active
        wait_for_subscription_active(subscription_id)

        # Deleting subscription
        subscription_response = delete_subscription(subscription_id)
        task_url = subscription_response['links'][0]['href']
        print(f"Subscription deletion task started. Task URL: {task_url}")

        # Checking subscription deletion task status
        task_status = check_task_status(task_url)
        print("Subscription deletion task completed successfully.")
        print(task_status)


    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
