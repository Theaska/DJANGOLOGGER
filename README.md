# DJANGOLOGGER

Django приложение для обработки и агрегации Apache лога.

В составе приложения Management command, которая на вход принимает ссылку на лог файл определенного формата, скачивает ее, парсит и записывает в БД.

## Использовались
* Django
* aiofiles - для ассинхронного чтения и сохранения файлов
* aiohttp - для ассинхронного доступа к удаленным ресурсами 
* БД: postgresql

### Разворачивание проекта
Для разворачивания проекта перейти в папку с проектом и ввести следующую команду:
* `docker-compose up --build`

### Создание супер юзера
* ` docker exec -it djangologger_django_logger_1 python3 django_logger/manage.py createsuperuser `

### Получение лог файла из урл
* ` docker exec -it djangologger_django_logger_1 python3 django_logger/manage.py import_logger_file http://www.almhuette-raith.at/apache-log/access.log `
* ключ ` --save ` - для сохранения лог файла

### Парсинг существующего лог файла
* ` docker exec -it djangologger_django_logger_1 python3 django_logger/manage.py parse_logger_file django_logger/logs/log_file.txt `

Для легкого очищения логов в админку добавлена специальная кнопка clear, которая удаляет логи из БД.
