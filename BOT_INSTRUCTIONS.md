# 🤖 Инструкция по использованию Telegram бота для поиска по базам данных

## 📱 Как найти и запустить бота

1. **Найдите бота в Telegram**: Откройте Telegram и найдите вашего бота по токену `6467050584:AAHhM8xo_VT-Ublz3A_2u3pU34k525b2lNg`
   
2. **Запустите бота**: Нажмите кнопку "Start" или отправьте команду `/start`

## 🔍 Основные команды

### `/start` - Начать работу
Показывает приветственное сообщение и список всех доступных команд.

### `/search <запрос>` - Поиск по всем базам
Выполняет поиск по всем 20+ миллиардам документов в базе usersbox.

**Примеры:**
```
/search +79123456789
/search example@mail.ru
/search Иван Петров
```

### `/sources` - Список баз данных
Показывает топ-10 крупнейших доступных баз данных с количеством записей.

### `/balance` - Проверка баланса
Показывает текущий баланс приложения и тарифы на поиск.

### `/help` - Справка
Подробная справка по всем командам и форматам поиска.

## 🚀 Быстрый поиск

**Самый простой способ:** Просто отправьте любой текст боту без команд!

Примеры:
```
+79123456789
example@mail.ru
Иван Петров
192.168.1.1
```

Бот автоматически определит, что это поисковый запрос, и выполнит поиск по всем базам.

## 📊 Что показывает бот

При поиске бот выдает:
- **Общее количество найденных записей**
- **Список баз данных** где найдена информация
- **Первые записи** из каждой базы с основными полями
- **Оценку релевантности** результатов

## 💰 Тарифы и оплата

- **Поиск по одной базе**: 0.005 ₽ за документ (минимум 0.125 ₽)
- **Поиск по всем базам**: 2.5 ₽ за запрос
- **Проверка количества**: Бесплатно

**Пополнение баланса:**
1. Перейдите к @usersbox_bot
2. Используйте команду `/me` для пополнения личного баланса
3. Используйте команду `/api` для перевода средств в приложение

## 🎯 Советы для эффективного поиска

### Форматирование запросов:
- **Телефоны**: `+79123456789` (формат E.164)
- **Email**: `user@domain.com`
- **Даты рождения**: `ДД.ММ.ГГГГ` (например, `15.03.1990`)
- **IP-адреса**: `192.168.1.1`

### Типы данных в базах:
- Номера телефонов
- Email адреса
- ФИО пользователей
- Адреса и геолокация
- Пароли и их хеши
- Данные социальных сетей
- Серии и номера документов

## ⚠️ Важные ограничения

1. **Законность**: Используйте бота только в законных целях
2. **Лимиты API**: 300 бесплатных запросов /explain в минуту
3. **Размер ответа**: Максимум 25 документов на источник
4. **Баланс**: Следите за балансом для платных запросов

## 🛠️ Панель управления

Веб-панель доступна по адресу: https://3312ad11-8248-4d7e-86f5-1571a6d10e5d.preview.emergentagent.com

В панели вы можете:
- Просматривать статистику использования
- Видеть последние сообщения и поиски
- Тестировать API подключения
- Настраивать webhook

## 🔧 Техническая информация

- **Версия API**: usersbox v1.2
- **Поддерживаемые методы**: /search, /sources, /explain, /getMe
- **База данных**: 20+ миллиардов документов
- **Источники**: 1000+ различных баз данных

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте баланс командой `/balance`
2. Убедитесь, что запрос корректно отформатирован
3. Попробуйте другой формат запроса
4. Обратитесь к администратору бота

---

**🚀 Готово! Ваш бот готов к использованию для поиска информации по базам данных!**