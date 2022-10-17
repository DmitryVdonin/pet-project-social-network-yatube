# yatube_project: social network with blogs and diaries
## http://dmitryvdonin.pythonanywhere.com/
### Description
In this social network you can publish your blogs: notes, diaries and articles. Also you can read other people's blogs and create communities with blogs according to your interest
### Technologies
- Python 3.7
- Django 2.2.19
- Bootstrap v.5.2
### Running a project in dev mode
- Install and activate the virtual environment
- Install dependencies from requirements.txt file
```
pip install -r requirements.txt
``` 
- Run the migrations. In the folder with the manage.py file, run the command:

```
 python3.manage.py migtate (windows: py.manage.py migtate)
 ```
- Start the developer server. In the folder with the manage.py file, run the command:

```
python3 manage.py runserver (windows: py manage.py runserver)
```
### Administration and Features
- Create a superuser to administer the project. In the folder with the manage.py file, run the command:

```
python3 manage.py createsuperuser (windows: py manage.py createsuperuser)
```
- The admin area is located at the relative address /admin/
- Creation of groups in the project is possible only for the administrator in the admin area
### Authors
Dmitry Vdonin
