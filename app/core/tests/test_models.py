from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()


class UserManagerTests(TestCase):

    def test_create_user(self):
        """Test creating a new user is successful."""
        email = 'test@example.com'
        nome = 'Test User'
        password = 'password123'
        role = 'ALUNO'
        user = User.objects.create_user(email=email, nome=nome, password=password, role=role)

        self.assertEqual(user.email, email)
        self.assertEqual(user.nome, nome)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role, role)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_no_email_fails(self):
        """Test creating user without email raises error."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(email='', nome='test', password='password123', role='ALUNO')

    def test_create_user_no_role_fails(self):
        """Test creating user without role raises error."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(email='test@example.com', nome='test', password='password123', role='')

    def test_create_user_no_password_fails(self):
        """Test creating user without password raises error."""
        with self.assertRaises(ValidationError):
            User.objects.create_user(email='test@example.com', nome='test', password='', role='ALUNO')

    def test_create_superuser(self):
        """Test creating a new superuser is successful."""
        email = 'admin@example.com'
        nome = 'Admin User'
        password = 'password123'
        user = User.objects.create_superuser(email=email, nome=nome, password=password)

        self.assertEqual(user.email, email)
        self.assertEqual(user.nome, nome)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.role, 'ADMIN')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
