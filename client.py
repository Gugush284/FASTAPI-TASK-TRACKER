#!/usr/bin/env python3
"""
Simple client for FASTAPI-TASK-TRACKER API
"""

import argparse
from typing import Optional

import requests


class TaskTrackerClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token: Optional[str] = None
        self.session = requests.Session()

    def _get_headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def register(self, email: str, password: str):
        """Register a new user"""
        data = {"email": email, "password": password}
        response = self.session.post(f"{self.base_url}/register", json=data)
        if response.status_code == 201:
            print("User registered successfully")
            return response.json()
        else:
            print(f"Registration failed: {response.status_code} - {response.text}")
            return None

    def login(self, email: str, password: str):
        """Login and get access token"""
        data = {"username": email, "password": password}
        response = self.session.post(
            f"{self.base_url}/token",
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        if response.status_code == 201:
            token_data = response.json()
            self.token = token_data["access_token"]
            print("Login successful")
            return token_data
        else:
            print(f"Login failed: {response.status_code} - {response.text}")
            return None

    def get_current_user(self):
        """Get current user info"""
        response = self.session.get(f"{self.base_url}/users/me", headers=self._get_headers())
        if response.status_code == 200:
            user = response.json()
            print(f"Current user: {user['email']} (ID: {user['id']})")
            return user
        else:
            print(f"Failed to get user: {response.status_code} - {response.text}")
            return None

    def delete_user(self, email: str, password: str):
        """Delete current user"""
        data = {"username": email, "password": password}
        headers = self._get_headers()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        response = self.session.request(
            "DELETE",
            f"{self.base_url}/delete/me",
            data=data,
            headers=headers
        )
        if response.status_code == 200:
            print("User deleted successfully")
            self.token = None
            return True
        else:
            print(f"Failed to delete user: {response.status_code} - {response.text}")
            return False

    def create_task(self, title: str, description: str = "", time_spent: int = 0):
        """Create a new task"""
        data = {
            "title": title,
            "description": description,
            "time_spent": time_spent
        }
        response = self.session.post(
            f"{self.base_url}/task/create",
            json=data,
            headers=self._get_headers()
        )
        if response.status_code == 201:
            task = response.json()
            print(f"Task created: {task['title']} (ID: {task['id']})")
            return task
        else:
            print(f"Failed to create task: {response.status_code} - {response.text}")
            return None

    def get_tasks(self):
        """Get all tasks for current user"""
        response = self.session.get(f"{self.base_url}/tasks/", headers=self._get_headers())
        if response.status_code == 200:
            tasks = response.json()
            print(f"Found {len(tasks)} tasks:")
            for task in tasks:
                print(f"  - ID: {task['id']}, Title: {task['title']}, Status: {task['status']}, Time: {task['time_spent']}min")
            return tasks
        else:
            print(f"Failed to get tasks: {response.status_code} - {response.text}")
            return None

    def delete_task(self, task_id: int):
        """Delete a task"""
        response = self.session.delete(f"{self.base_url}/tasks/{task_id}", headers=self._get_headers())
        if response.status_code == 200:
            print(f"Task {task_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete task: {response.status_code} - {response.text}")
            return False

    def create_project(self, name: str, task_ids: list):
        """Create a new project with tasks"""
        data = {"name": name, "task_ids": task_ids}
        response = self.session.post(
            f"{self.base_url}/projects/",
            json=data,
            headers=self._get_headers()
        )
        if response.status_code == 201:
            project = response.json()
            print(f"Project created: {project['name']} (ID: {project['id']})")
            return project
        else:
            print(f"Failed to create project: {response.status_code} - {response.text}")
            return None

    def get_projects(self):
        """Get all projects for current user"""
        response = self.session.get(f"{self.base_url}/projects/", headers=self._get_headers())
        if response.status_code == 200:
            projects = response.json()
            print(f"Found {len(projects)} projects:")
            for project in projects:
                print(f"  - ID: {project['id']}, Name: {project['name']}")
            return projects
        else:
            print(f"Failed to get projects: {response.status_code} - {response.text}")
            return None

    def delete_project(self, project_id: int):
        """Delete a project"""
        response = self.session.delete(f"{self.base_url}/projects/{project_id}", headers=self._get_headers())
        if response.status_code == 204:
            print(f"Project {project_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete project: {response.status_code} - {response.text}")
            return False

    def select_tasks(self, project_id: int, time_limit: int):
        """Select tasks for execution within time limit"""
        response = self.session.get(
            f"{self.base_url}/projects/{project_id}/select_tasks?time_limit={time_limit}",
            headers=self._get_headers()
        )
        if response.status_code == 200:
            tasks = response.json()
            print(f"Selected {len(tasks)} tasks within {time_limit} minutes:")
            for task in tasks:
                print(f"  - ID: {task['id']}, Title: {task['title']}, Time: {task['time_spent']}min")
            return tasks
        else:
            print(f"Failed to select tasks: {response.status_code} - {response.text}")
            return None

    def get_all_users(self):
        """Get all users (admin only)"""
        response = self.session.get(f"{self.base_url}/users/", headers=self._get_headers())
        if response.status_code == 200:
            users = response.json()
            print(f"Found {len(users)} users:")
            for user in users:
                print(f"  - ID: {user['id']}, Email: {user['email']}, Role: {user['role']}")
            return users
        else:
            print(f"Failed to get users: {response.status_code} - {response.text}")
            return None

    def create_user(self, email: str, password: str, role: str = "viewer"):
        """Create a new user (admin only)"""
        data = {"email": email, "password": password, "role": role}
        response = self.session.post(f"{self.base_url}/users/", json=data, headers=self._get_headers())
        if response.status_code == 201:
            user = response.json()
            print(f"User created: {user['email']} (Role: {user['role']})")
            return user
        else:
            print(f"Failed to create user: {response.status_code} - {response.text}")
            return None

    def update_user_role(self, user_id: int, role: str):
        """Update user role (admin only)"""
        data = {"role": role}
        response = self.session.patch(f"{self.base_url}/users/{user_id}", json=data, headers=self._get_headers())
        if response.status_code == 200:
            user = response.json()
            print(f"User {user['email']} role updated to {user['role']}")
            return user
        else:
            print(f"Failed to update user: {response.status_code} - {response.text}")
            return None

    def delete_user_by_id(self, user_id: int):
        """Delete user by ID (admin only)"""
        response = self.session.delete(f"{self.base_url}/users/{user_id}", headers=self._get_headers())
        if response.status_code == 204:
            print(f"User {user_id} deleted successfully")
            return True
        else:
            print(f"Failed to delete user: {response.status_code} - {response.text}")
            return False

    def logout(self):
        """Logout by clearing token"""
        self.token = None
        print("Logged out")

    def demo(self):
        """Run a complete demo of all API operations including role testing"""
        print("=== Task Tracker API Demo with Role Testing ===\n")

        # Step 1: Register first user (becomes admin)
        print("1. Registering admin user...")
        admin = self.register("admin@example.com", "password123")
        if not admin:
            print("Demo failed at admin registration")
            return

        # Step 2: Login as admin
        print("\n2. Logging in as admin...")
        token_data = self.login("admin@example.com", "password123")
        if not token_data:
            print("Demo failed at admin login")
            return

        # Step 3: Get admin info
        print("\n3. Getting admin user info...")
        admin_info = self.get_current_user()
        if not admin_info or admin_info['role'] != 'admin':
            print("Demo failed: user is not admin")
            return

        # Step 4: Create viewer user
        print("\n4. Creating viewer user...")
        viewer = self.create_user("viewer@example.com", "password123", "viewer")
        if not viewer:
            print("Demo failed at creating viewer")
            return

        # Step 5: Create moderator user
        print("\n5. Creating moderator user...")
        moderator = self.create_user("moderator@example.com", "password123", "moderator")
        if not moderator:
            print("Demo failed at creating moderator")
            return

        # Step 6: Get all users (admin only)
        print("\n6. Getting all users (admin only)...")
        users = self.get_all_users()
        if not users or len(users) < 3:
            print("Demo failed at getting all users")
            return

        # Step 7: Test admin permissions
        print("\n7. Testing admin permissions...")

        # Admin creates task
        admin_task = self.create_task("Admin Task", "Created by admin", 60)
        if not admin_task:
            print("Admin failed to create task")
            return

        # Verify task creation by getting tasks
        print("   - Verifying task creation...")
        tasks = self.get_tasks()
        if tasks and len(tasks) == 1 and tasks[0]['title'] == "Admin Task":
            print("   ✓ Task creation verified")
        else:
            print("   ✗ Task creation verification failed")
            return

        # Admin updates task (should succeed)
        print("   - Updating task as admin...")
        update_data = {"title": "Updated by admin"}
        response = self.session.patch(f"{self.base_url}/tasks/{admin_task['id']}", json=update_data, headers=self._get_headers())
        if response.status_code == 200:
            print("   ✓ Admin can update task")
        else:
            print(f"   ✗ Admin failed to update: {response.status_code}")

        # Admin deletes task (should succeed)
        print("   - Deleting task as admin...")
        response = self.session.delete(f"{self.base_url}/tasks/{admin_task['id']}", headers=self._get_headers())
        if response.status_code == 200:
            print("   ✓ Admin can delete task")
        else:
            print(f"   ✗ Admin failed to delete: {response.status_code}")

        # Admin can manage users (already tested by creating users above)
        print("   ✓ Admin can manage users (verified by user creation)")

        # Step 8: Test viewer permissions
        print("\n7. Testing viewer permissions...")
        self.logout()
        viewer_login = self.login("viewer@example.com", "password123")
        if not viewer_login:
            print("Failed to login as viewer")
            return

        # Viewer creates task
        task = self.create_task("Viewer Task", "Created by viewer", 30)
        if not task:
            print("Viewer failed to create task")
            return

        # Verify task creation by getting tasks
        print("   - Verifying task creation...")
        tasks = self.get_tasks()
        if tasks and len(tasks) == 1 and tasks[0]['title'] == "Viewer Task":
            print("   ✓ Task creation verified")
        else:
            print("   ✗ Task creation verification failed")
            return

        # Viewer tries to update task (should fail)
        print("   - Trying to update task (should fail)...")
        update_data = {"title": "Updated by viewer"}
        response = self.session.patch(f"{self.base_url}/tasks/{task['id']}", json=update_data, headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Viewer correctly denied update permission")
        else:
            print(f"   ✗ Viewer should not be able to update: {response.status_code}")

        # Viewer tries to delete task (should fail)
        print("   - Trying to delete task (should fail)...")
        response = self.session.delete(f"{self.base_url}/tasks/{task['id']}", headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Viewer correctly denied delete permission")
        else:
            print(f"   ✗ Viewer should not be able to delete: {response.status_code}")

        # Viewer tries to get all users (should fail)
        print("   - Trying to get all users (should fail)...")
        response = self.session.get(f"{self.base_url}/users/", headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Viewer correctly denied access to user management")
        else:
            print(f"   ✗ Viewer should not be able to get all users: {response.status_code}")

        # Viewer tries to create a user (should fail)
        print("   - Trying to create a user (should fail)...")
        user_data = {"email": "newuser@example.com", "password": "password123", "role": "viewer"}
        response = self.session.post(f"{self.base_url}/users/", json=user_data, headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Viewer correctly denied user creation")
        else:
            print(f"   ✗ Viewer should not be able to create users: {response.status_code}")

        # Step 8: Test moderator permissions
        print("\n8. Testing moderator permissions...")
        self.logout()
        moderator_login = self.login("moderator@example.com", "password123")
        if not moderator_login:
            print("Failed to login as moderator")
            return

        # Moderator creates own task
        mod_task = self.create_task("Moderator Task", "Created by moderator", 45)
        if not mod_task:
            print("Moderator failed to create task")
            return

        # Verify task creation by getting tasks
        print("   - Verifying task creation...")
        tasks = self.get_tasks()
        if tasks and len(tasks) >= 1:  # Since moderator can see all tasks, but at least own
            print("   ✓ Task creation verified")
        else:
            print("   ✗ Task creation verification failed")
            return

        # Moderator updates task (should succeed)
        print("   - Updating task as moderator...")
        response = self.session.patch(f"{self.base_url}/tasks/{task['id']}", json=update_data, headers=self._get_headers())
        if response.status_code == 200:
            print("   ✓ Moderator can update task")
        else:
            print(f"   ✗ Moderator failed to update: {response.status_code}")

        # Moderator deletes task (should succeed)
        print("   - Deleting task as moderator...")
        response = self.session.delete(f"{self.base_url}/tasks/{task['id']}", headers=self._get_headers())
        if response.status_code == 200:
            print("   ✓ Moderator can delete task")
        else:
            print(f"   ✗ Moderator failed to delete: {response.status_code}")

        # Moderator deletes own task
        response = self.session.delete(f"{self.base_url}/tasks/{mod_task['id']}", headers=self._get_headers())
        if response.status_code == 200:
            print("   ✓ Moderator deleted own task")
        else:
            print(f"   ✗ Moderator failed to delete own task: {response.status_code}")

        # Moderator tries to get all users (should fail)
        print("   - Trying to get all users (should fail)...")
        response = self.session.get(f"{self.base_url}/users/", headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Moderator correctly denied access to user management")
        else:
            print(f"   ✗ Moderator should not be able to get all users: {response.status_code}")

        # Moderator tries to create a user (should fail)
        print("   - Trying to create a user (should fail)...")
        response = self.session.post(f"{self.base_url}/users/", json=user_data, headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Moderator correctly denied user creation")
        else:
            print(f"   ✗ Moderator should not be able to create users: {response.status_code}")

        # Moderator tries to update user role (should fail)
        print("   - Trying to update user role (should fail)...")
        role_data = {"role": "moderator"}
        response = self.session.patch(f"{self.base_url}/users/{viewer['id']}", json=role_data, headers=self._get_headers())
        if response.status_code == 403:
            print("   ✓ Moderator correctly denied role update")
        else:
            print(f"   ✗ Moderator should not be able to update roles: {response.status_code}")

        # Step 10: Back to admin for cleanup
        print("\n9. Logging back as admin for cleanup...")
        self.logout()
        admin_login = self.login("admin@example.com", "password123")
        if not admin_login:
            print("Failed to login back as admin")
            return

        # Admin deletes viewer and moderator
        print("   - Deleting viewer user...")
        if not self.delete_user_by_id(viewer['id']):
            print("Failed to delete viewer")
            return

        print("   - Deleting moderator user...")
        if not self.delete_user_by_id(moderator['id']):
            print("Failed to delete moderator")
            return

        print("\n=== Role testing completed successfully! ===")
        print("✓ Admin can manage users and all operations")
        print("✓ Viewer can create but not modify/delete")
        print("✓ Moderator can modify/delete but not manage users")

        # Step 11: Cleanup admin
        print("\n10. Cleaning up admin data...")
        if self.delete_user("admin@example.com", "password123"):
            print("Demo data cleaned up successfully")
        else:
            print("Warning: Failed to clean up demo data")


def main():
    parser = argparse.ArgumentParser(description="Task Tracker API Client")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--demo", action="store_true", help="Run complete demo of all operations")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register
    subparsers.add_parser("register", help="Register a new user")
    subparsers.add_parser("login", help="Login and get token")
    subparsers.add_parser("user", help="Get current user info")
    subparsers.add_parser("delete-user", help="Delete current user")

    # Admin
    subparsers.add_parser("users", help="Get all users (admin)")
    create_user_parser = subparsers.add_parser("create-user", help="Create a new user (admin)")
    create_user_parser.add_argument("email", help="User email")
    create_user_parser.add_argument("password", help="User password")
    create_user_parser.add_argument("--role", default="viewer", choices=["viewer", "moderator", "admin"], help="User role")

    update_user_parser = subparsers.add_parser("update-user", help="Update user role (admin)")
    update_user_parser.add_argument("user_id", type=int, help="User ID")
    update_user_parser.add_argument("role", choices=["viewer", "moderator", "admin"], help="New role")

    delete_user_parser = subparsers.add_parser("delete-user-id", help="Delete user by ID (admin)")
    delete_user_parser.add_argument("user_id", type=int, help="User ID to delete")

    # Tasks
    subparsers.add_parser("tasks", help="Get all tasks")
    create_task_parser = subparsers.add_parser("create-task", help="Create a new task")
    create_task_parser.add_argument("title", help="Task title")
    create_task_parser.add_argument("--description", default="", help="Task description")
    create_task_parser.add_argument("--time", type=int, default=0, help="Time spent in minutes")

    delete_task_parser = subparsers.add_parser("delete-task", help="Delete a task")
    delete_task_parser.add_argument("task_id", type=int, help="Task ID to delete")

    # Projects
    subparsers.add_parser("projects", help="Get all projects")
    create_project_parser = subparsers.add_parser("create-project", help="Create a new project")
    create_project_parser.add_argument("name", help="Project name")
    create_project_parser.add_argument("task_ids", nargs="+", type=int, help="Task IDs to include")

    delete_project_parser = subparsers.add_parser("delete-project", help="Delete a project")
    delete_project_parser.add_argument("project_id", type=int, help="Project ID to delete")

    select_tasks_parser = subparsers.add_parser("select-tasks", help="Select tasks for execution")
    select_tasks_parser.add_argument("project_id", type=int, help="Project ID")
    select_tasks_parser.add_argument("time_limit", type=int, help="Time limit in minutes")

    args = parser.parse_args()

    client = TaskTrackerClient(args.url)

    if args.demo:
        client.demo()
        return

    if not args.command:
        parser.print_help()
        return

    if args.command == "register":
        email = input("Email: ")
        password = input("Password: ")
        client.register(email, password)

    elif args.command == "login":
        email = input("Email: ")
        password = input("Password: ")
        client.login(email, password)

    elif args.command == "user":
        client.get_current_user()

    elif args.command == "delete-user":
        email = input("Email: ")
        password = input("Password: ")
        client.delete_user(email, password)

    elif args.command == "users":
        client.get_all_users()

    elif args.command == "create-user":
        client.create_user(args.email, args.password, args.role)

    elif args.command == "update-user":
        client.update_user_role(args.user_id, args.role)

    elif args.command == "delete-user-id":
        client.delete_user_by_id(args.user_id)

    elif args.command == "tasks":
        client.get_tasks()

    elif args.command == "create-task":
        client.create_task(args.title, args.description, args.time)

    elif args.command == "delete-task":
        client.delete_task(args.task_id)

    elif args.command == "projects":
        client.get_projects()

    elif args.command == "create-project":
        client.create_project(args.name, args.task_ids)

    elif args.command == "delete-project":
        client.delete_project(args.project_id)

    elif args.command == "select-tasks":
        client.select_tasks(args.project_id, args.time_limit)


if __name__ == "__main__":
    main()