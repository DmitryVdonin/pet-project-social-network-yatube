# yatube_projectsocial network with blogs and diaries
### Описание
В этой социальной сети можно публиковать свои блоги: заметки, дневники и статьи. А так же читать блоги других людей и создавать сообщества с блогами по интересам
### Технологии
- Python 3.7
- Django 2.2.19
- Bootstrap v.5.2
### Запуск проекта в dev-режиме
- Установите и активируйте виртуальное окружение
- Установите зависимости из файла requirements.txt
```
pip install -r requirements.txt
``` 
- Выполните миграции. В папке с файлом manage.py выполните команду:
```
 python3.manage.py migtate (windows: py.manage.py migtate)
 ```
- Запустите сервер разработчика. В папке с файлом manage.py выполните команду:
```
python3 manage.py runserver (windows: py manage.py runserver)
```
### Администрирование и особенности
- Для администрирования проекта создайте суперпользователя. В папке с файлом manage.py выполните команду:
```
python3 manage.py createsuperuser (windows: py manage.py createsuperuser)
```
- Админ-зона расположена по относительному адреу /admin/
- Создание групп в проекте возможно только для администратора в админ-зоне
### Авторы
Дмитрий Вдонин
