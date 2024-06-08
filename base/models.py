from django.db import models
from django.contrib.auth.models import AbstractUser
from datetime import datetime

from .validators import *

class User(AbstractUser):
    name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    avatar = models.ImageField(null=True, default='avatar.svg')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class Batch(models.Model):
    batch_year = models.IntegerField()

    def __str__(self):
        return str(self.batch_year)
    
class Students(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    branch = models.CharField(max_length=200)
    usn = models.CharField(max_length=20, null=True, validators=[validate_usn])
    aptitudeLevel = models.IntegerField(default=0)
    languageLevel = models.IntegerField(default=0)
    programmingLevel = models.IntegerField(default=0)
    coreLevel = models.IntegerField(default=0)
    softskillsLevel = models.IntegerField(default=0)
    placedCount = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.usn} : {self.student.name}'

class KYC(models.Model):
    CHOICES = (
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected')
    )
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    resume = models.FileField(blank=True, null=True)
    videoResume = models.FileField(blank=True, null=True)
    collegeIdCard = models.FileField(blank=True, null=True)
    passportSizePhoto = models.FileField(blank=True, null=True)
    panCard = models.FileField(blank=True, null=True)
    aadharCard = models.FileField(blank=True, null=True)
    passport = models.FileField(blank=True, null=True)
    tenthMarksCard = models.FileField(blank=True, null=True)
    twelfthMarksCard = models.FileField(blank=True, null=True)
    ugMarksSheet = models.FileField(blank=True, null=True)
    pgMarksSheet = models.FileField(blank=True, null=True)
    cgpaCalculator = models.FileField(blank=True, null=True)

    validation = models.CharField(max_length=10, choices=CHOICES, default='Pending')
    comments = models.TextField(default="No comments")

    def __str__(self):
        return f'KYC: {self.student.student.name}'
    
class SPF(models.Model):
    APPROVAL_CHOICES = (
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Rejected', 'Rejected')
    )
    DEGREE_CHOICES = (
        ('BE', 'BE'),
        ('MCA', 'MCA'),
        ('MBA', 'MBA')
    )
    DEPARTMENT_CHOICES = (
        ('Basic Science', 'Basic Science'),
        ('Placement', 'Placement'),
        ('CSE', 'CSE'),
        ('ISE', 'ISE'),
        ('ECE', 'ECE'),
        ('EEE', 'EEE'),
        ('MECH', 'MECH'),
        ('AIML', 'AIML'),
        ('CIV', 'CIV'),
        ('MCA', 'MCA'),
        ('MBA', 'MBA')
    )
    TYPE_OF_ENTRY_CHOICES = (
        ('Regular', 'Regular'),
        ('Lateral', 'Lateral')
    )
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female')
    )
    UG_PG_CHOICE = (
        ('UG', 'UG'),
        ('PG', 'PG')
    )
    BOOLEAN_CHOICES = (
        ('Yes', 'Yes'),
        ('No', 'No')
    )
    student = models.ForeignKey(Students, on_delete=models.CASCADE, null=False)
    mobileNumberForCalling = models.CharField(max_length=10, null=False)
    mobileNumberForWhatsapp = models.CharField(max_length=10, null=False)
    degree = models.CharField(max_length=3, null=False, choices=DEGREE_CHOICES, default='BE')
    typeOfEntry = models.CharField(max_length=10, choices=TYPE_OF_ENTRY_CHOICES, default='Regular', null=False)
    gender = models.CharField(max_length=6, null=False, choices=GENDER_CHOICES)
    dateOfBirth = models.DateField()
    personalEmailId = models.EmailField()
    mentorName = models.CharField(max_length=20, null=False)
    mentorDept = models.CharField(max_length=13, null=False, choices=DEPARTMENT_CHOICES)
    mentorMobileNumber = models.CharField(max_length=10, null=False)
    parentsMobileNumber = models.CharField(max_length=10, null=False)
    communicationAddress = models.TextField(null=False)
    permanentAddress = models.TextField(null=False)
    tenthMarks = models.FloatField(null=False)
    tenthYearOfPassing = models.CharField(max_length=4, null=False)
    twelfthMarks = models.FloatField(null=True, blank=True, default=0)
    twelfthYearOfPassing = models.CharField(max_length=4, null=True, blank=True, default=0)
    diplomaMarks = models.FloatField(null=True, blank=True, default=0)
    diplomaYearOfPassing = models.CharField(max_length=4, null=True, blank=True, default=0)
    ugOrPg = models.CharField(max_length=2, choices=UG_PG_CHOICE, default='UG', null=False)
    degreeCgpa = models.FloatField(null=False)
    currentBacklogs = models.IntegerField(default=0)
    backlogHistory = models.CharField(max_length=3, choices=BOOLEAN_CHOICES, default='No', null=False)
    yearBack = models.CharField(max_length=3, choices=BOOLEAN_CHOICES, default='No', null=False)
    numberOfYearGapsInAcademics = models.IntegerField(default=0)
    numberofYearGapsInDegree = models.IntegerField(default=0)
    
    validation = models.CharField(max_length=10, choices=APPROVAL_CHOICES, default='Pending')
    comments = models.TextField(default="No comments")

    def __str__(self):
        return f'SPF: {self.student.student.name}'

class Tests(models.Model):
    # Aptitude, Language
    TYL_CHOICES = (
        ('Aptitude', 'Aptitude'),
        ('Language', 'Language'),
        ('Core', 'Core'),
        ('Programming', 'Programming'),
        ('Soft Skills', 'Soft Skills'),
    )
    testName = models.CharField(max_length=200)
    testType = models.CharField(max_length=20, choices=TYL_CHOICES)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    maxMarks = models.FloatField(default=100)
    passingMarks = models.FloatField(default=50)

    def __str__(self):
        return self.testName

class StudentAptitudeTestScores(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.test} - {self.student}'

class StudentSoftSkillsTestScores(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.test} - {self.student}'

class StudentLanguageTestScores(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.test} - {self.student}'
    
class StudentProgrammingTestScores(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    subjectCode = models.CharField(max_length=10, null=True, blank=True)
    specialization = models.CharField(max_length=50)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.test} - {self.student}'

class StudentCoreTestScores(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.test} - {self.student}'
    
class SubTests(models.Model):
    # A1, A2, L2, P4
    test = models.ForeignKey(Tests, on_delete=models.CASCADE)
    subTestName = models.CharField(max_length=20)
    subTestDescription = models.CharField(max_length=200, default="Assignment Details published")
    subTestDeadline = models.DateField()
    maxMarks = models.FloatField(default=100)
    passingMarks = models.FloatField(default=50)

    def __str__(self):
        return f'{self.test.testName} \'{self.test.batch} : {self.subTestName}'
    
    class Meta:
        ordering = ['subTestDeadline', 'subTestName']

class StudentTest(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    subTest = models.ForeignKey(SubTests, on_delete=models.CASCADE)
    marksObtained = models.IntegerField(default=0)
    passed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.subTest.test.testName} : {self.subTest.subTestName} - {self.student.student.name}'
    
class Topic(models.Model):
    TOPICS = (
        ('General', 'General'),
        ('Drive', 'Drive'),
        ('Training - Aptitude', 'Training - Aptitude'),
        ('Training - Soft Skills', 'Training - Soft Skills'),
        ('Training - Java', 'Training - Java'),
        ('Training - Python', 'Training - Python'),
        ('Training - Core TYL', 'Training - Core TYL'),
    )

    name = models.CharField(max_length=200, choices=TOPICS)

    def __str__(self):
        return self.name

class ChatRoom(models.Model):
    host = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='participants', blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-updated', '-created']

class Drives(models.Model):
    placement_officer = models.ForeignKey(User, on_delete=models.CASCADE)
    driveChat = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    companyName = models.CharField(max_length=200)
    role = models.CharField(max_length=500)
    requirements = models.CharField(max_length=500)
    job_description = models.FileField()
    min_cgpa = models.FloatField(default=0)
    aptitude_level = models.IntegerField()
    programming_level = models.IntegerField()
    core_level = models.IntegerField()  
    softskills_level = models.IntegerField(default=0)
    language_level = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.companyName

class PlacedStudents(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    drive = models.ForeignKey(Drives, on_delete=models.CASCADE)
    offer_letter = models.FileField(default=None)

    def __str__(self):
        return f'{self.student.student} - {self.drive.companyName}'
    
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True) 
        
    def __str__(self):
        return self.message[:50]