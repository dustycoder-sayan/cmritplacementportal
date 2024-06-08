from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.db.models import Count, Case, When, Sum
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse

import re
from datetime import datetime
import io
import csv

from .models import *
from .forms import *
from .decorators import *
from .filters import *

def get_group(request):
    group_list = []
    groups = request.user.groups.all()
    if groups:
        for group in groups:
            group_list.append(group.name)
    return group_list

def email_send(subject, message, email):
    send_mail (
        subject,
        message,
        'settings.EMAIL_HOST_USER',
        email,
        fail_silently=False
    )

def get_consolidated_marks_dict(students, test):
    marks_dict = {}
    for student in students:
        marks_dict[student.id] = StudentAptitudeTestScores.objects.get_or_create(student=student, test=test)[0].marksObtained
    return marks_dict

def get_filter_students_for_drive(drive_id):
    drive = Drives.objects.get(pk=drive_id)

    # Filter students based on criteria
    filtered_students = Students.objects.filter(
        batch__in=[drive.batch],
        spf__validation__in=['Approved'],
        spf__degreeCgpa__gte=drive.min_cgpa,
        aptitudeLevel__gte=drive.aptitude_level,
        languageLevel__gte=drive.language_level,
        programmingLevel__gte=drive.programming_level,
        coreLevel__gte=drive.core_level,
        softskillsLevel__gte=drive.softskills_level
    )

    return filtered_students

@unauthenticated_user
def loginPage(request):
    page = 'login'
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            User.objects.get(email=email)
        except:
            messages.error(request, 'No such user exists')
        
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home_page')
        else:
            messages.error(request, 'Username or password does not exist')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)

@unauthenticated_user
def registerPage(request):
    page = 'register'
    form = MyUserCreationForm()
    century = str(datetime.now().year)[:2]

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = user.email.lower()
            match = re.search(r'^([a-zA-Z]+)(\d+)([a-zA-Z]+)@cmrit\.ac\.in$', user.email)   
            user.username = match.group(1)+match.group(2)+match.group(3)
            user.save()
            
            group = Group.objects.get(name='Student')
            user.groups.add(group)

            usn_number = str(request.POST.get('usn')[-3:])

            if usn_number[0] == '4':
                batch_year = str(int(match.group(2))+3)
                batch, created = Batch.objects.get_or_create(batch_year=int(century+batch_year))
            else:
                batch_year = str(int(match.group(2))+4)
                batch, created = Batch.objects.get_or_create(batch_year=int(century+batch_year))

            Students.objects.create (
                student = user,
                batch=batch,
                branch = match.group(3).upper(),
                usn=request.POST.get('usn').upper()
            )
            login(request, user)
            return redirect('home_page')
        else:
            messages.error(request, form.errors)

    context = {'page':page, 'form': form}
    return render(request, 'base/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('login_page')

@login_required(login_url='login_page')
def homePage(request):
    page = 'Home'
    group_list = get_group(request)
    drives = Drives.objects.all()
    batches = Batch.objects.all()
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = None
    room_messages = None
    if 'Student' in group_list:
        student = Students.objects.get(student=request.user)
        room_messages = Message.objects.filter(room__batch__batch_year__in=[student.batch.batch_year])[5::-1]
        rooms = ChatRoom.objects.all()
    if 'Officer' in group_list:
        room_messages = Message.objects.filter(room__topic__name__in=['Drive'])[5::-1]
        rooms = ChatRoom.objects.filter(topic__name__in=['Drive'])
    if 'FPC' in group_list:
        room_messages = Message.objects.filter(room__topic__name__in=['General', 'Drive'])[5::-1]
        rooms = ChatRoom.objects.filter(topic__name__in=['General', 'Drive'])
    if 'Trainer' in group_list:
        all_topics = Topic.TOPICS
        topics_accessible = ['General', 'Drive']
        for topic1, topic2 in all_topics:
            if 'Training' in  topic1:
                topics_accessible.append(topic1)
        
        room_messages = Message.objects.filter(room__topic__name__in=topics_accessible)[5:0:-1]
        rooms = ChatRoom.objects.filter(topic__name__in=topics_accessible)

    if rooms: 
        rooms = rooms.filter(
            Q(topic__name__icontains=q) |
            Q(name__icontains=q) |
            Q(host__username__icontains=q)   
        )
    else:
        rooms = None

    context = {'page': page, 'groups': group_list, 'rooms': rooms, 'room_messages': room_messages, 'drives': drives, 'batches': batches}
    return render(request, 'base/home.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Student'])
def kycForm(request):
    page = 'KYC'
    student = Students.objects.get(student=request.user)
    form = KYCForm()
    exists = False
    try:
        kyc = KYC.objects.get(student=student)
        form = KYCForm(instance=kyc)
        exists = True
    except:
        kyc = None

    if request.method == 'POST':
        if exists:
            form = KYCForm(request.POST, request.FILES, instance=kyc)
        else:
            form = KYCForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                kyc_form = form.save(commit=False)
                if exists:
                    kyc_form.validation = 'Pending'
                    kyc_form.save()
                else:
                    kyc_form.validation = 'Pending'
                    kyc_form.comments = 'No Comments'
                    kyc_form.student = student
                    kyc_form.save()
                print(f"File saved at: {kyc_form.resume.path}")  # Debug: Print file path
                messages.success(request, 'KYC data successfully updated')
            except Exception as e:
                print(f"Exception: {e}")  # Debug: Print exception details
                messages.error(request, f'Could not update KYC: {e}')
        else:
            print(form.errors)  # Debug: Print form errors
            messages.error(request, 'KYC data could not be successfully updated')

        return redirect('home_page')
    
    context = {'page': page, 'form': form, 'kyc': kyc}
    return render(request, 'base/form.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['FPC', 'SPC', 'Trainer', 'Officer'])
def kycHomePage(request):
    group_list = get_group(request)
    page = 'kyc'
    br = request.GET.get('br') if request.GET.get('br') != None else ''
    ba = request.GET.get('ba') if request.GET.get('ba') != None else None

    if ba == None:
        students = Students.objects.filter(kyc__validation__in=['Pending', 'Rejected'])
    else:
        try:
            batch = Batch.objects.get(batch_year=int(ba))
            students = Students.objects.filter(branch=br,batch=batch,kyc__validation__in=['Pending', 'Rejected'])
        except:
            students = None

    branches = map(lambda x:x['branch'], list(Students.objects.values('branch').distinct()))

    year = datetime.now().year
    context = {'page': page, 'group': group_list, 'branches': branches, 'students': students, 'year': year}
    return render(request, 'base/validation_batches.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['FPC', 'SPC', 'Trainer', 'Officer'])
def kycStudentDetails(request, pk):
    page = 'kyc'
    student = Students.objects.get(id=pk)
    kyc = KYC.objects.get(student=student)

    if request.method == 'POST':
        kyc.validation = request.POST.get('approval')   
        kyc.comments = request.POST.get('comments')
        kyc.save()

        subject = f'CMRIT Placements - KYC Validation for {student.student.name} '
        message = f'Hi!\nYour spf data has been {kyc.validation}. The comments provided are : \n{kyc.comments}'
        email = student.student.email

        email_send(subject, message, [email,])

        return redirect('kyc_home_page')

    context = {'page': page, 'student': student, 'kyc': kyc}
    return render(request, 'base/validation_student.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Student'])
def spfForm(request):
    page = 'SPF'
    student = Students.objects.get(student=request.user)
    form = SPFForm()
    exists = False

    try:
        spf = SPF.objects.get(student=student)
        form = SPFForm(instance=spf)
        exists = True
    except:
        spf = None

    if request.method == 'POST':
        if exists:
            form = SPFForm(request.POST, instance=spf)
            if form.is_valid():
                spf_form = form.save(commit=False)
                spf_form.validation = 'Pending' 
                spf_form.save()
                messages.error(request, 'SPF data successfully updated')
        else:
            try:
                SPF.objects.create(
                    student=student,
                    mobileNumberForCalling=request.POST.get('mobileNumberForCalling'),
                    mobileNumberForWhatsapp=request.POST.get('mobileNumberForWhatsapp'),
                    degree=request.POST.get('degree'),
                    typeOfEntry=request.POST.get('typeOfEntry'),
                    gender=request.POST.get('gender'),
                    dateOfBirth=datetime.strptime(request.POST.get('dateOfBirth'), '%d/%m/%Y').date(),
                    personalEmailId=request.POST.get('personalEmailId'),
                    mentorName=request.POST.get('mentorName'),
                    mentorDept=request.POST.get('mentorDept'),
                    mentorMobileNumber=request.POST.get('mentorMobileNumber'),
                    parentsMobileNumber=request.POST.get('parentsMobileNumber'),
                    communicationAddress=request.POST.get('communicationAddress'),
                    permanentAddress=request.POST.get('permanentAddress'),
                    tenthMarks=float(request.POST.get('tenthMarks')),
                    tenthYearOfPassing=request.POST.get('tenthYearOfPassing'),
                    twelfthMarks=float(request.POST.get('twelfthMarks')),
                    twelfthYearOfPassing=request.POST.get('twelfthYearOfPassing'),
                    diplomaMarks=float(request.POST.get('diplomaMarks')),
                    diplomaYearOfPassing=request.POST.get('diplomaYearOfPassing'),
                    ugOrPg=request.POST.get('ugOrPg'),
                    degreeCgpa=float(request.POST.get('degreeCgpa')),
                    currentBacklogs=int(request.POST.get('currentBacklogs')),
                    backlogHistory=request.POST.get('backlogHistory'),
                    yearBack=request.POST.get('yearBack'),
                    numberOfYearGapsInAcademics=int(request.POST.get('numberOfYearGapsInAcademics')),
                    numberofYearGapsInDegree=int(request.POST.get('numberofYearGapsInDegree'))
                )
                messages.error(request, "SPF data successfully uploaded")
            except Exception as e:
                messages.error(request, f'SPF data could not be uploaded : {e.args}')
        return redirect('home_page')

    context = {'page': page, 'form': form, 'spf': spf}
    return render(request, 'base/form.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['FPC', 'SPC', 'Trainer', 'Officer'])
def spfHomePage(request):
    page = 'spf'
    br = request.GET.get('br') if request.GET.get('br') != None else ''
    ba = request.GET.get('ba') if request.GET.get('ba') != None else None

    if ba == None:
        students = Students.objects.filter(spf__validation__in=['Pending', 'Rejected'])
    else:
        try:
            batch = Batch.objects.get(batch_year=int(ba))
            students = Students.objects.filter(branch=br,batch=batch,spf__validation__in=['Pending', 'Rejected'])
        except:
            students = None

    branches = map(lambda x:x['branch'],list(Students.objects.values('branch').distinct()))

    year = datetime.now().year
    context = {'page': page, 'branches': branches, 'students': students, 'year': year}
    return render(request, 'base/validation_batches.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['FPC', 'SPC', 'Trainer', 'Officer'])
def spfStudentDetails(request, pk):
    page = 'spf'
    student = Students.objects.get(id=pk)
    spf = SPF.objects.get(student=student)

    if request.method == 'POST':
        spf.validation = request.POST.get('approval')   
        spf.comments = request.POST.get('comments')
        spf.save()

        subject = f'CMRIT Placements - SPF Validation for {student.student.name} '
        message = f'Hi!\nYour spf data has been {spf.validation}. The comments provided are : \n{spf.comments}'
        email = student.student.email

        email_send(subject, message, [email,])

        return redirect('spf_home_page')

    context = {'page': page, 'student': student, 'spf': spf}
    return render(request, 'base/validation_student.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Officer', 'Director'])
def createDrive(request):
    page = 'drive'
    form = DriveForm()
    if request.method == 'POST':
        topic, created = Topic.objects.get_or_create(name='Drive')
        description = f'''
            Role: {request.POST.get('role')},\n
            Requirements: {request.POST.get('requirements')}, A{request.POST.get('aptitude_level')}, P{request.POST.get('programming_level')}, C{request.POST.get('core_level')}
        '''
        chat_room = ChatRoom.objects.create (
            host=request.user,
            topic=topic,
            batch=Batch.objects.get(id=request.POST.get('batch')),
            name=request.POST.get('companyName'),
            description=description
        )
        drive_created = Drives.objects.create (
            placement_officer=request.user,
            driveChat=chat_room,
            batch=Batch.objects.get(id=request.POST.get('batch')),
            companyName=request.POST.get('companyName'),
            role=request.POST.get('role'),
            requirements=request.POST.get('requirements'),
            min_cgpa=request.POST.get('min_cgpa'),
            job_description=request.POST.get('job_description'),
            aptitude_level=request.POST.get('aptitude_level'),
            programming_level=request.POST.get('programming_level'),
            core_level=request.POST.get('core_level'),
            language_level=request.POST.get('language_level'),
            softskills_level=request.POST.get('softskills_level')
        )

        filtered_students = get_filter_students_for_drive(drive_created.id)
        subject = f'{drive_created.companyName} Drive posted for {drive_created.batch.batch_year-4}-{drive_created.batch.batch_year} Batch'
        message = f'''Dear Students,\nThis is Drive Announcement for {drive_created.companyName} for {drive_created.batch.batch_year} students.
        '''
        emails = []
        for student in filtered_students:
            emails.append(student.student.email)
        
        email_send(subject, message, emails)

        print(filtered_students)
        message = Message.objects.create (
            sender=request.user,
            room=chat_room,
            message=message
        )
        for student in filtered_students:
            chat_room.participants.add(student.student)

        return redirect('home_page')
        
    context = {'page': page, 'form': form}
    return render(request, 'base/create_chat_room.html', context)    

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Student', 'Trainer'])
def tylHomePage(request, name):
    group_list = get_group(request)
    page = name
    name = name.capitalize()
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    if 'Trainer' in group_list:
        batches = Batch.objects.all()[:6]

        ba = request.GET.get('ba') if request.GET.get('ba') != None else None
        
        if ba:
            tests = Tests.objects.filter(testType__in=[name]).filter(batch__batch_year__in=[ba]) or None
        else:
            tests = Tests.objects.filter(testType__in=[name]) 

        tests = tests.filter (
            Q(testName__icontains=q)
        )

        context = {'page': page, 'group': group_list, 'batches': batches, 'tests': tests, 'batchSelected': ba}
        return render(request, 'base/tyl.html', context)
    
    elif 'Student' in group_list:
        student = Students.objects.get(student=request.user)
        batch = student.batch.batch_year

        tests = Tests.objects.filter(testType__in=[name]).filter(batch__batch_year__in=[batch])

        tests = tests.filter (
            Q(testName__icontains=q)
        )

        context = {'page': page, 'group': group_list,'tests': tests}
        return render(request, 'base/tyl.html', context)    

    else:
        return HttpResponse('Sorry! You are not allowed to view this page!')

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Student', 'Trainer'])
def tylTestPage(request, pk):
    group_list = get_group(request)
    test = Tests.objects.get(id=pk)
    subTests = SubTests.objects.filter(test=test)
    subTestSelectedId = request.GET.get('st') if request.GET.get('st') != None else 'None'

    if 'Trainer' in group_list:
        branches = list(map(lambda x:x['branch'],list(Students.objects.values('branch').distinct())))
        branchSelected = request.GET.get('br') if request.GET.get('br') != None else str(branches[0])
        consolidated = request.GET.get('op') or None

        students = Students.objects.filter (
            branch=branchSelected,
            batch=test.batch    
        ).order_by('usn')

        try:
            subTestSelected = SubTests.objects.get(id=subTestSelectedId)
        except:
            subTestSelected = None

        marks_dict = {}
        if consolidated:
            if test.testType == 'Aptitude':
                marks_dict = get_consolidated_marks_dict(students, test)
                if request.method == 'POST':
                    student = Students.objects.get(id=request.GET.get('id'))
                    marksObtained = int(request.POST.get('marks'))
                    studentTest, created = StudentAptitudeTestScores.objects.get_or_create(student=student,test=test)
                    studentTest.marksObtained = marksObtained
                    studentTest.passed = True if marksObtained > test.passingMarks else False
                    studentTest.save()

                    level = int(test.testName[1])
                    if studentTest.passed:
                        if student.aptitudeLevel < level:
                            student.aptitudeLevel = level
                            student.save()

                    marks_dict = get_consolidated_marks_dict(students, test)

                    
            elif test.testType == 'Language':
                marks_dict = get_consolidated_marks_dict(students, test)
                if request.method == 'POST':
                    student = Students.objects.get(id=request.GET.get('id'))
                    marksObtained = int(request.POST.get('marks'))
                    studentTest, created = StudentLanguageTestScores.objects.get_or_create(student=student,test=test)
                    studentTest.marksObtained = marksObtained
                    studentTest.passed = True if marksObtained > test.passingMarks else False
                    studentTest.save()

                    level = int(test.testName[1])
                    if studentTest.passed:
                        if student.languageLevel < level:
                            student.languageLevel = level
                            student.save()

                    marks_dict = get_consolidated_marks_dict(students, test)
                    
            elif test.testType == 'Soft Skills':
                marks_dict = get_consolidated_marks_dict(students, test)
                if request.method == 'POST':
                    student = Students.objects.get(id=request.GET.get('id'))
                    marksObtained = int(request.POST.get('marks'))
                    studentTest, created = StudentSoftSkillsTestScores.objects.get_or_create(student=student,test=test)
                    studentTest.marksObtained = marksObtained
                    studentTest.passed = True if marksObtained > test.passingMarks else False
                    studentTest.save()
                    
                    level = int(test.testName[1])
                    if studentTest.passed:
                        if student.softskillsLevel < level:
                            student.softskillsLevel = level
                            student.save()
                        
                    marks_dict = get_consolidated_marks_dict(students, test)
                    
            elif test.testType == 'Core':
                marks_dict = get_consolidated_marks_dict(students, test)
                if request.method == 'POST':
                    student = Students.objects.get(id=request.GET.get('id'))
                    marksObtained = int(request.POST.get('marks'))
                    studentTest, created = StudentCoreTestScores.objects.get_or_create(student=student,test=test)
                    studentTest.marksObtained = marksObtained
                    studentTest.passed = True if marksObtained > test.passingMarks else False
                    studentTest.save()

                    level = int(test.testName[1])
                    if studentTest.passed:
                        if student.coreLevel < level:
                            print('Entered')
                            student.coreLevel = level
                            student.save()

                    marks_dict = get_consolidated_marks_dict(students, test)
                    
            elif test.testType == 'Programming':
                marks_dict = get_consolidated_marks_dict(students, test)
                if request.method == 'POST':
                    student = Students.objects.get(id=request.GET.get('id'))
                    marksObtained = int(request.POST.get('marks'))
                    studentTest, created = StudentProgrammingTestScores.objects.get_or_create(student=student,test=test)
                    studentTest.marksObtained = marksObtained
                    studentTest.passed = True if marksObtained > test.passingMarks else False
                    studentTest.save()

                    level = int(test.testName[1])
                    if studentTest.passed:
                        if student.programmingLevel < level:
                            student.programmingLevel = level
                            student.save()

                    marks_dict = get_consolidated_marks_dict(students, test)

            print(students)
            context = {'group': group_list, 'test': test, 'subTests': subTests, 'subTestSelected': subTestSelected, 'branches': branches, 'branchSelected': branchSelected, 'students': students, 'marks_dict': marks_dict, 'consolidated': consolidated} 
            return render(request, 'base/test_details.html', context)
        
        else:
            for student in students:
                try:
                    marks_dict[student.id] = StudentTest.objects.get(student=student,subTest=subTestSelected).marksObtained
                except:
                    pass

            if request.method == 'POST':
                student = Students.objects.get(id=request.GET.get('id'))
                marksObtained = int(request.POST.get('marks'))
                studentTest, created = StudentTest.objects.get_or_create(student=student,subTest=subTestSelected)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > subTestSelected.passingMarks else False
                studentTest.save()

                for student in students:
                    try:
                        marks_dict[student.id] = StudentTest.objects.get(student=student,subTest=subTestSelected).marksObtained
                    except:
                        pass

            context = {'group': group_list, 'test': test, 'subTests': subTests, 'subTestSelected': subTestSelected, 'branches': branches, 'branchSelected': branchSelected, 'students': students, 'marks_dict': marks_dict, 'consolidated': consolidated} 
            return render(request, 'base/test_details.html', context)

    elif 'Student' in group_list:
        student = Students.objects.get(student=request.user)
        branch = student.branch
        allSubTests = SubTests.objects.filter(test=test) 
        
        try:
            subTestSelected = SubTests.objects.get(id=subTestSelectedId)
        except:
            subTestSelected = None

        try:
            studentTest = StudentTest.objects.get(student=student, subTest=subTestSelected)
        except:
            studentTest = None
        
        submitted = False
        passed = False
    
        if studentTest:
            submitted = studentTest != None
            passed = studentTest.passed
        else:
            submitted = None
            passed = None

        pendingSubtests = allSubTests.exclude(studenttest__student=student).order_by('subTestDeadline')
        print(pendingSubtests)

        context = {'group': group_list, 'test': test, 'subTests': subTests, 'subTestSelected': subTestSelected, 'branch': branch, 'student': student, 'test_details': studentTest, 'submitted': submitted, 'passed': passed, 'pendingSubtests': pendingSubtests}
        return render(request, 'base/test_details.html', context)

def process_marks_file(file, test, subTest, consolidated):
    decoded_file = file.read().decode('utf-8')
    io_string = io.StringIO(decoded_file)
    reader = csv.DictReader(io_string)

    for row in reader:
        usn = row['USN']
        marks = row['Marks']
        student = Students.objects.get(usn=usn)
        if not consolidated:
            marksObtained = int(marks)
            studentTest, created = StudentTest.objects.get_or_create(student=student,subTest=subTest)
            studentTest.marksObtained = marksObtained
            studentTest.passed = True if marksObtained > subTest.passingMarks else False
            studentTest.save()
        else:
            if test.testType == 'Aptitude':
                marksObtained = int(marks)
                studentTest, created = StudentAptitudeTestScores.objects.get_or_create(student=student,test=test)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > test.passingMarks else False
                studentTest.save()

                level = int(test.testName[1])
                if studentTest.passed:
                    if student.aptitudeLevel < level:
                        student.aptitudeLevel = level
                        student.save()

            elif test.testType == 'Language':
                marksObtained = int(marks)
                studentTest, created = StudentLanguageTestScores.objects.get_or_create(student=student,test=test)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > test.passingMarks else False
                studentTest.save()

                level = int(test.testName[1])
                if studentTest.passed:
                    if student.aptitudeLevel < level:
                        student.aptitudeLevel = level
                        student.save()
            
            elif test.testType == 'Soft Skills':
                marksObtained = int(marks)
                studentTest, created = StudentSoftSkillsTestScores.objects.get_or_create(student=student,test=test)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > test.passingMarks else False
                studentTest.save()

                level = int(test.testName[1])
                if studentTest.passed:
                    if student.aptitudeLevel < level:
                        student.aptitudeLevel = level
                        student.save()
            
            elif test.testType == 'Core':
                marksObtained = int(marks)
                studentTest, created = StudentCoreTestScores.objects.get_or_create(student=student,test=test)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > test.passingMarks else False
                studentTest.save()

                level = int(test.testName[1])
                if studentTest.passed:
                    if student.aptitudeLevel < level:
                        student.aptitudeLevel = level
                        student.save()
            
            elif test.testType == 'Programming':
                marksObtained = int(marks)
                studentTest, created = StudentProgrammingTestScores.objects.get_or_create(student=student,test=test)
                studentTest.marksObtained = marksObtained
                studentTest.passed = True if marksObtained > test.passingMarks else False
                studentTest.save()

                level = int(test.testName[1])
                if studentTest.passed:
                    if student.aptitudeLevel < level:
                        student.aptitudeLevel = level
                        student.save()

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Trainer'])
def uploadTestMarks(request, pk):
    page = 'upload_marks'
    test = Tests.objects.get(id=pk)
    consolidated = True if request.GET.get('op') != 'None' else False
    subTestId = request.GET.get('st')
    branch = request.GET.get('br')
    form = UploadMarksForm()

    if subTestId:
        subTest = SubTests.objects.get(id=subTestId)
    else:
        subTest = None

    if request.method == 'POST':
        form = UploadMarksForm(request.POST, request.FILES)
        if form.is_valid():
            print('Valid')
            process_marks_file(request.FILES['csv_file'], test, subTest, consolidated)
        else:
            print(form.errors)
        
        url = reverse('tyl_trainer_test_details', kwargs={'pk':pk})
        if consolidated:
            query_params = f'?br={branch}&op=consolidated_scores'
        else:
            query_params = f'?st={subTestId}&br={branch}'
        full_url = f'{url}{query_params}'

        return redirect(full_url)
    context = {'page': page, 'test': test, 'consolidated': consolidated, 'subTest': subTest, 'form': form}
    return render(request, 'base/form.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Trainer'])
def createTest(request, name: str):
    page = 'test'
    name = name.capitalize()
    form = TestForm()
    batches = Batch.objects.all()

    if request.method == 'POST':
        try:
            nameEntered = request.POST.get('testName')
            batchEntered = request.POST.get('batch')
            test = Tests.objects.filter(
                testName=nameEntered,
                batch=Batch.objects.get(batch_year=int(batchEntered))
            )
            if test:
                messages.error(request, "Test already created")
                return redirect('tyl_home_page', name=name) 
            else:
                raise Exception()
        except:
            try:
                Tests.objects.create (
                    testName = request.POST.get('testName'),
                    testType = name,
                    batch = Batch.objects.get(batch_year=int(request.POST.get('batch')))
                )
                messages.error(request,'Test Created Successfully')
                return redirect('tyl_home_page', name=name)
            except:
                messages.error(request, 'Could not create test')

    context = {'page': page, 'name': name, 'form': form, 'batches': batches}
    return render(request, 'base/form.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Trainer'])
def createSubTest(request, pk):
    page = 'sub_test'
    form = SubTestForm()
    test = Tests.objects.get(id=pk)

    if request.method == 'POST':
        try:
            nameEntered = request.POST.get('subTestName')
            subTest = SubTests.objects.filter(
                test=test,
                subTestName=nameEntered
            )
            if subTest:
                messages.error(request, "Test already created")
                return redirect('tyl_home_page', name=test.testName)
            else:
                raise Exception()
        except:
            try:
                SubTests.objects.create (
                    test=test, 
                    subTestName=request.POST.get('subTestName'),
                    subTestDescription=request.POST.get('subTestDescription'),
                    subTestDeadline=datetime.strptime(request.POST.get('subTestDeadline'), '%d/%m/%Y').date(),
                    maxMarks=request.POST.get('maxMarks'),
                    passingMarks=request.POST.get('passingMarks')
                )
                messages.error(request,'Test Created Successfully')
            except Exception as e:
                messages.error(request, f'Could not create test {e}')
        return redirect('tyl_trainer_test_details', pk=test.id)

    context = {'page': page, 'form': form, 'test': test}
    return render(request, 'base/form.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Trainer', 'Officer', 'Director', 'FPC'])
def createChatRoom(request):
    page = 'chat'
    topics = map(lambda x:x[0], Topic.TOPICS)
    form = ChatRoomForm()
    
    if request.method == 'POST':
        topic_name = request.POST.get('topic') or 'General'
        topic, created = Topic.objects.get_or_create (
            name=topic_name
        )
        batch = Batch.objects.get(id=int(request.POST.get('batch')))
        room = ChatRoom.objects.create(
            host=request.user,
            topic=topic,
            batch=batch,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        room.participants.add(request.user)
        return redirect('home_page')
    context = {'page': page, 'form': form, 'topics': topics}
    return render(request, 'base/create_chat_room.html', context)

@login_required(login_url='login_page')
def room(request, pk):
    room = ChatRoom.objects.get(id=pk)
    room_messages = room.message_set.all()
    participants = room.participants.all()
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    if request.method == 'POST':
        message = Message.objects.create (
            sender = request.user,
            room = room,
            message = request.POST.get('message')
        )
        room.participants.add(request.user)
        return redirect('chat_room', pk=room.id)
    
    room_messages = room_messages.filter (
        Q(sender__username__icontains=q) |
        Q(message__icontains=q)
    )

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/chat_room.html', context)

def deleteMessage(request):
    pass

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Trainer', 'FPC', 'SPC', 'Officer', 'Director'])
def spfKycDashboard(request, pk):
    page = 'spf_kyc'
    batches = Batch.objects.all()
    
    batch = Batch.objects.get(id=pk)
    branches = Students.objects.filter(batch=batch).values('branch').annotate(
        total_students=Count('id'),
        students_with_spf=Count('spf__student'),
        students_with_kyc=Count('kyc__student')
    )

    context = {'page': page, 'batches': batches, 'branches': branches, 'batchSelected': batch}
    return render(request, 'base/dashboard.html', context)

def subTestDashboard(request, batch_id, test_id):
    page = 'subtests'
    batch = Batch.objects.get(pk=batch_id)
    test = Tests.objects.get(pk=test_id)

    # Get all subtests for the given test
    subtests = SubTests.objects.filter(test=test)

    # Create an empty dictionary to store statistics for each subtest
    subtest_stats = {}

    # Iterate over each subtest
    for subtest in subtests:
        # Calculate statistics for each subtest
        branches = Students.objects.filter(batch=batch).values('branch').annotate(
            total_students=Count('id'),
            students_with_test=Count('studenttest', filter=Q(studenttest__subtest=subtest), distinct=True),
            students_passed=Sum(
                Case(
                    When(studenttest__subtest=subtest, studenttest__passed=True, then=1),
                    default=0,
                    output_field=models.IntegerField()
                )
            ),
            students_failed=Sum(
                Case(
                    When(studenttest__subtest=subtest, studenttest__passed=False, then=1),
                    default=0,
                    output_field=models.IntegerField()
                )
            )
        )

        # Store the statistics for each subtest in the dictionary
        subtest_stats[subtest] = branches
    context = {'page': page, 'batch': batch, 'test': test, 'subtest_stats': subtest_stats}
    return render(request, 'base/dashboard.html', context)

@login_required(login_url='login_page')
@allowed_users(allowed_users=['Officer', 'Director'])
def spadDetails(request, batch):
    page = 'spad'
    batch = int(batch)
    students = Students.objects.filter(
        batch__batch_year = batch,
        spf__validation='Approved',
        kyc__validation='Approved'
    ).order_by('branch')

    mySPADFilter = SPADFilter(request.GET, queryset=students)
    students = mySPADFilter.qs

    context = {'page': page, 'students': students, 'batch': batch,'SPADFilter': mySPADFilter}
    return render(request, 'base/spad_details.html', context)

@login_required(login_url='login_page')
def user_profile(request, pk):
    page = 'user_profile'
    user = User.objects.get(id=pk)
    group_list = []
    groups = user.groups.all()
    if groups:
        for group in groups:
            group_list.append(group.name)

    try:
        student = Students.objects.get(student=user)
    except:
        student = None

    rooms = user.chatroom_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()
    context = {'page': page, 'user': user, 'groups': group_list, 'student': student, 'rooms': rooms, 'topics': topics, 'room_messages': room_messages}
    return render(request, 'base/profile.html', context)

@login_required(login_url='login_page')
def user_profile_update(request):
    user = request.user
    form = UserForm(instance=user)
    context = {'form':form}

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)     # request.FILES will process the files entered in form
        if form.is_valid():
            form.save()
            return redirect('user_profile', pk=user.id)
    return render(request, 'base/profile_update.html', context)

# @login_required(login_url='login_page')
# def edit_room(request, pk):
#     room = ChatRoom.objects.get(id=pk)
#     form = ChatRoomForm(instance=room)
#     topics = Topic.objects.all()

#     if request.method == 'POST':
#         topic_name = request.POST.get('topic')
#         topic, created = Topic.objects.get_or_create(name=topic_name)   # 'name' - named keyword to BE USED
#         room.name = request.POST.get('name')
#         room.topic = topic
#         room.description = request.POST.get('description')
#         room.save()     # important to SAVE after each edit
#         return redirect('chat_room', pk=pk)
        
#     context = {'form':form, 'topics':topics, 'room': room}
#     return render(request, 'base/create_chat_room.html', context)

@login_required(login_url='login_page')
def delete_room(request, pk):
    room = ChatRoom.objects.get(id=pk)

    if request.method == 'POST':
        room.delete()
        return redirect('home_page')
    
    context = {'obj':room}
    return render(request, 'base/delete.html', context)

@login_required(login_url='login_page')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.sender:
        return HttpResponse('You are not allowed here')
    
    if request.method == 'POST':
        message.delete()
        return redirect('chat_room', pk=message.room.id)    
    
    context = {'obj':message}
    return render(request, 'base/delete.html', context)